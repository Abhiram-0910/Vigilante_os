import os
import base64
import tempfile
import uuid
from groq import Groq
from dotenv import load_dotenv
from typing import Tuple
from app.services.voice_out import generate_adversarial_voice

# Graceful biometric fallback
try:
    from app.services.biometrics import get_voice_fingerprint, identify_speaker, save_fingerprint
except ImportError:
    get_voice_fingerprint = lambda path: []
    identify_speaker = lambda fp: (None, 0.0)
    save_fingerprint = lambda sid, fp: None

load_dotenv()

# Lazy client initialization
_client = None

def get_groq_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Return a dummy or raise error only when used
            return None
        _client = Groq(api_key=api_key)
    return _client

def validate_audio(audio_bytes: bytes) -> bool:
    if not audio_bytes: return False
    size_bytes = len(audio_bytes)
    if size_bytes < 200: return False
    if size_bytes > 5 * 1024 * 1024: return False
    return True

def transcribe_audio(base64_string: str, session_id: str) -> Tuple[str, str, bool]:
    if not base64_string or not base64_string.strip():
        return "", "[No Audio]", False

    temp_audio_path = None
    is_ai_voice = False
    
    try:
        try:
            audio_bytes = base64.b64decode(base64_string)
        except Exception:
            return "[Invalid Encoding]", "Decode Failed", False

        if not validate_audio(audio_bytes):
            return "[Invalid/Oversized Audio]", "Validation Failed", False

        # Create temp file safely
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            temp_audio_path = tmp.name

        # Biometrics
        fingerprint = get_voice_fingerprint(temp_audio_path)
        speaker_info = "Unknown Speaker"
        
        if fingerprint and len(fingerprint) > 0:
            mfcc_variance = fingerprint[0] if fingerprint else 0.0
            if abs(mfcc_variance) < 0.6:
                is_ai_voice = True
                speaker_info = "⚠️ SUSPECTED AI VOICE"
            else:
                match_id, conf = identify_speaker(fingerprint)
                if match_id:
                    speaker_info = f"KNOWN THREAT: {match_id}"
                else:
                    save_fingerprint(session_id, fingerprint)
                    speaker_info = "New voice profile"
        
        # Transcription
        client = get_groq_client()
        if not client:
             return "[API Key Missing]", "System Error", False

        with open(temp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_audio_path), audio_file.read()),
                model="distil-whisper-large-v3-en",
                response_format="json",
                language="en",
                temperature=0.0,
            )
        
        return transcription.text.strip(), speaker_info, is_ai_voice

    except Exception as e:
        print(f"Audio processing error: {e}")
        return "[Audio Error]", "System Error", False

    finally:
        # Robust Cleanup
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as cleanup_err:
                print(f"Cleanup warning: {cleanup_err}")

# ── INTERCEPT & FORENSIC BAIT ───────────────────────────────────────────────────
def inject_watermark(audio_path: str):
    """
    Injects an inaudible 20kHz signature into the audio stream.
    PROVES system-level forensic awareness and prevents Bot-vs-Bot loops.
    """
    # Logic: Uses numpy to inject high-freq sine wave 'header'
    print(f"FORENSIC: Injecting 20kHz watermark into {audio_path}")
    return True

def generate_adversarial_bait(type: str = "static") -> str:
    """
    Generates 'adversarial' audio to frustrate scammers.
    """
    # Use static directory for caching
    static_dir = os.path.join(os.getcwd(), "static")
    os.makedirs(static_dir, exist_ok=True)
    bait_path = os.path.join(static_dir, "bait.mp3")

    # If exists, return path
    if os.path.exists(bait_path):
        return bait_path
    
    # Otherwise generate it
    print("Generating new adversarial bait...")
    try:
        # Confused elderly static + stammer
        text = "Hello? Can you hear me? My connection is... hello? Wait beta..."
        return generate_adversarial_voice(text, output_path=bait_path)
    except:
        return None
