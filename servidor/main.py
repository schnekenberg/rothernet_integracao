'''# teste gpt
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import base64
import shutil
from servidor.database.session import SessionLocal
from servidor.database import crud
from servidor.conversions.txt_to_wav import text_to_wav_pt
from servidor.conversions.wav_to_txt import transcrever_audio
from agente_virtual.v5_integracao.servico_ia import ServicoIA
from servidor.getters.get_methods import is_interaction_over, get_order_id, get_user_id
from agente_virtual.v5_integracao.memoria import MemoriaConversa


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Gerenciador de conexões WS
# -----------------------------
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.memories = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        self.connections[client_id] = websocket
        self.memories[client_id] = MemoriaConversa()

    def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)
        self.memories.pop(client_id, None)

    async def send_audio(self, client_id: str, audio_bytes: bytes):
        if client_id in self.connections:
            await self.connections[client_id].send_bytes(audio_bytes)


manager = ConnectionManager()

os.makedirs("audios/received_audio", exist_ok=True)
os.makedirs("audios/audio_responses", exist_ok=True)


@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    db = SessionLocal()
    await websocket.accept()
    ia = ServicoIA.instance()
    client_id = None

    try:
        while True:
            # 1️⃣ Recebe áudio
            audio_bytes = await websocket.receive_bytes()
            tmp_file_path = "audios/received_audio/temp.wav"

            # Escreve o áudio recebido
            with open(tmp_file_path, "wb") as f:
                f.write(audio_bytes)

            # 2️⃣ Converte para texto
            try:
                user_text = transcrever_audio(tmp_file_path)
                if "erro" in user_text.lower() or "error" in user_text.lower():
                    print(f"[{client_id}] User said: {user_text}")
                    await websocket.send_json({
                        "audio": "",
                        "finished": True,
                        "error": "Falha na transcrição do áudio"
                    })
                    break
            except Exception as e:
                print(f"Exceção na transcrição: {e}")
                await websocket.send_json({
                    "audio": "",
                    "finished": True,
                    "error": "Erro interno no processamento"
                })
                break

            # 3️⃣ Identifica cliente
            if client_id is None:
                client_id = get_user_id(user_text) or "unknown_user"
                await manager.connect(websocket, client_id)

                final_file_path = f"audios/received_audio/{client_id}.wav"

                # Mover o arquivo para evitar erro de arquivo aberto
                if os.path.exists(tmp_file_path):
                    shutil.move(tmp_file_path, final_file_path)

                tmp_file_path = final_file_path
                print(f"Assigned client_id: {client_id}")

            # 4️⃣ Atualiza banco
            client = crud.get_client(db, client_id)
            if client == -1:
                crud.add_client(db, client_id)

            # 5️⃣ Gera resposta da IA
            memoria = manager.memories[client_id]
            print(user_text) # o erro deve estar na resposta da IA mesmo, pois chega tudo direito
            ai_text = ia.responder(user_text, memoria)
            print(f"[{client_id}] AI responded: {ai_text}")

            # 6️⃣ Detecta ID de pedido
            order_id = get_order_id(user_text)
            if order_id:
                print(f"Detected order ID: {order_id}")

            # 7️⃣ Converte resposta da IA em áudio
            response_wav_path = f"audios/audio_responses/{client_id}.wav"
            text_to_wav_pt(ai_text, output_path=response_wav_path)

            with open(response_wav_path, "rb") as f:
                audio_data = f.read()

            # 8️⃣ Envia áudio de volta
            finished = is_interaction_over(user_text)
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            await websocket.send_json({
                "audio": audio_base64,
                "finished": finished
            })

            if finished:
                print(f"Conversation ended for {client_id}")
                break

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
'''

'''import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import base64
from servidor.database.session import SessionLocal
from servidor.database import crud
from servidor.conversions.txt_to_wav import text_to_wav_pt
from servidor.conversions.wav_to_txt import transcrever_audio
from agente_virtual.v5_integracao.servico_ia import ServicoIA
from servidor.getters.get_methods import is_interaction_over
from servidor.getters.get_methods import get_order_id, get_user_id
from agente_virtual.v5_integracao.memoria import MemoriaConversa


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerencia conexões WebSocket ativas
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.memories = {}  # memória por cliente

    async def connect(self, websocket: WebSocket, client_id: str):
        #await websocket.accept()
        self.connections[client_id] = websocket
        self.memories[client_id] = MemoriaConversa()

    def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)
        self.memories.pop(client_id, None)

    async def send_audio(self, client_id: str, audio_bytes: bytes):
        if client_id in self.connections:
            await self.connections[client_id].send_bytes(audio_bytes)

manager = ConnectionManager()

os.makedirs("audios/received_audio", exist_ok=True)
os.makedirs("audios/audio_responses", exist_ok=True)

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    db = SessionLocal()
    await websocket.accept() 
    ia = ServicoIA.instance()
    client_id = None

    try:
        while True:
            # 1. Recebe áudio do Unity
            audio_bytes = await websocket.receive_bytes()
            tmp_file_path = f"audios/received_audio/temp.wav"
            with open(tmp_file_path, "wb") as f:
                f.write(audio_bytes)

            # 2. Converte áudio em texto
                try:
                    user_text = transcrever_audio(tmp_file_path)
                    if "erro" in user_text.lower() or "error" in user_text.lower():
                        print(f"[{client_id}] User said: {user_text}") #teste
                        error_message ={
                            "audio": "",  # ou um áudio de fallback
                            "finished": True,
                            "error": "Falha na transcrição do áudio"
                        }
                        await websocket.send_json(error_message)
                        break
                except Exception as e:
                    print(f"Exceção na transcrição: {e}")
                    error_message = {
                        "audio": "",
                        "finished": True,
                        "error": "Erro interno no processamento"
                    }
                    await websocket.send_json(error_message)
                    break

                # Extrai o user id do texto
                if client_id is None:
                    client_id = get_user_id(user_text) or "unknown_user"
                    await manager.connect(websocket, client_id)
                    # Renomeia o arquivo temporário para client_id
                    final_file_path = f"audios/received_audio/{client_id}.wav"
                    os.rename(tmp_file_path, final_file_path)
                    tmp_file_path = final_file_path
                    print(f"Assigned client_id: {client_id}")

            # 3. Cria ou atualiza cliente no banco
            client = crud.get_client(db, client_id)
            if client == -1:
                client = crud.add_client(db, client_id)

            # 4. IA gera resposta
            memoria = manager.memories[client_id]
            ai_text = ia.responder(user_text, memoria)
            print(f"[{client_id}] AI responded: {ai_text}")

            # 5. Detecta ID de pedido se houver
            order_id = get_order_id(user_text)
            if order_id:
                print(f"Detected order ID: {order_id}")

            # 6. Converte resposta da IA em áudio
            response_wav_path = f"audios/audio_responses/{client_id}.wav"
            text_to_wav_pt(ai_text, output_path=response_wav_path)
            with open(response_wav_path, "rb") as f:
                audio_data = f.read()

            # 7. Envia áudio de volta ao cliente
            finished = is_interaction_over(user_text)
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            message = {
                "audio": audio_base64,   # áudio convertido para base64
                "finished": finished,
            }

            await websocket.send_json(message)
            # 8. Verifica se a conversa terminou
            if finished:
                print(f"Conversation ended for {client_id}")
                break
        

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
    finally:
        manager.disconnect(client_id)
        db.close() '''
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# teste gpt
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import base64
import shutil
from servidor.database.session import SessionLocal
from servidor.database import crud
from servidor.conversions.txt_to_wav import text_to_wav_pt
from servidor.conversions.wav_to_txt import transcrever_audio
from agente_virtual.v5_integracao.servico_ia import ServicoIA
from servidor.getters.get_methods import is_interaction_over, get_order_id, get_user_id
from agente_virtual.v5_integracao.memoria import MemoriaConversa


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Gerenciador de conexões WS
# -----------------------------
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.memories = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        self.connections[client_id] = websocket
        self.memories[client_id] = MemoriaConversa()

    def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)
        self.memories.pop(client_id, None)

    async def send_audio(self, client_id: str, audio_bytes: bytes):
        if client_id in self.connections:
            await self.connections[client_id].send_bytes(audio_bytes)


manager = ConnectionManager()

os.makedirs("audios/received_audio", exist_ok=True)
os.makedirs("audios/audio_responses", exist_ok=True)


@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    db = SessionLocal()
    await websocket.accept()
    ia = ServicoIA.instance()
    client_id = None

    try:
        while True:
            # 1. Recebe áudio
            audio_bytes = await websocket.receive_bytes()
            tmp_file_path = "audios/received_audio/temp.wav"

            # Escreve o áudio recebido
            with open(tmp_file_path, "wb") as f:
                f.write(audio_bytes)

            # 2. Converte para texto
            try:
                user_text = transcrever_audio(tmp_file_path)
                if "erro" in user_text.lower() or "error" in user_text.lower():
                    print(f"[{client_id}] User said: {user_text}")
                    await websocket.send_json({
                        "audio": "",
                        "finished": True,
                        "error": "Falha na transcrição do áudio"
                    })
                    break
            except Exception as e:
                print(f"Exceção na transcrição: {e}")
                await websocket.send_json({
                    "audio": "",
                    "finished": True,
                    "error": "Erro interno no processamento"
                })
                break

            # 3. Identifica cliente
            if client_id is None:
                client_id = get_user_id(user_text) or "unknown_user"
                await manager.connect(websocket, client_id)

                final_file_path = f"audios/received_audio/{client_id}.wav"

                # Mover o arquivo para evitar erro de arquivo aberto
                if os.path.exists(tmp_file_path):
                    shutil.move(tmp_file_path, final_file_path)

                tmp_file_path = final_file_path
                print(f"Assigned client_id: {client_id}")

            # 4. Atualiza banco
            client = crud.get_client(db, client_id)
            if client == -1:
                crud.add_client(db, client_id)

            # 5. Gera resposta da IA
            memoria = manager.memories[client_id]
            print(user_text) # o erro deve estar na resposta da IA mesmo, pois chega tudo direito
            ai_text = ia.responder(user_text, memoria)
            print(f"[{client_id}] AI responded: {ai_text}")

            # 6. Detecta ID de pedido
            order_id = get_order_id(user_text)
            if order_id:
                print(f"Detected order ID: {order_id}")

            # 7. Converte resposta da IA em áudio
            response_wav_path = f"audios/audio_responses/{client_id}.wav"
            text_to_wav_pt(ai_text, output_path=response_wav_path)

            with open(response_wav_path, "rb") as f:
                audio_data = f.read()

            # 8. Envia áudio de volta
            finished = is_interaction_over(user_text)

            # audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            # await websocket.send_json({
            #     "audio": audio_base64,
            #     "finished": finished
            # })
            print(f"Enviando áudio de {len(audio_data)} bytes")
            await websocket.send_bytes(audio_data) # envia somente o audio

            if finished:
                 print(f"Conversation ended for {client_id}")
                 break

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")

    finally:
        manager.disconnect(client_id)
        db.close()
