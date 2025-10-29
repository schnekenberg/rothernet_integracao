from TTS.api import TTS
import os

def text_to_wav_pt(text: str, output_path: str):
    """
    Converte texto em português para arquivo WAV
    """
    try:
        # Usar modelo específico para português que não requer licença
        tts = TTS("tts_models/pt/cv/vits")
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Gerar áudio
        tts.tts_to_file(text=text, file_path=output_path)
        
        print(f"Áudio gerado com sucesso: {output_path}")
        
    except Exception as e:
        print(f"Erro no TTS: {e}")
        
        # Fallback para outro modelo
        try:
            print("Tentando modelo fallback...")
            tts_fallback = TTS("tts_models/multilingual/multi-dataset/your_tts")
            tts_fallback.tts_to_file(
                text=text,
                file_path=output_path,
                language="pt"
            )
            print(f"Áudio gerado com fallback: {output_path}")
        except Exception as e2:
            print(f"Erro também no fallback: {e2}")
            raise Exception(f"Falha no sistema TTS: {e2}")