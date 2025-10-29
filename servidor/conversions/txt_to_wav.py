# conversions/txt_to_wav.py
from TTS.api import TTS
import os

def text_to_wav_pt(text: str, output_path: str = "output.wav"):
    """
    Converte texto para áudio usando modelo em português
    """
    try:
        # Usar modelo específico para português (não precisa de speaker)
        tts = TTS(model_name="tts_models/pt/cv/vits", progress_bar=False, gpu=False)
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        tts.tts_to_file(text=text, file_path=output_path)
        print(f"Áudio gerado: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Erro com modelo PT: {e}")
        # Fallback para modelo multilíngue sem speaker específico
        try:
            tts_fallback = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)
            tts_fallback.tts_to_file(
                text=text, 
                file_path=output_path, 
                speaker=None,  # Sem speaker específico
                language="pt"
            )
            print(f"Áudio gerado com fallback: {output_path}")
            return output_path
        except Exception as e2:
            print(f"Erro também no fallback: {e2}")
            raise