import os
import io
from gtts import gTTS

def generate_adversarial_voice(text: str, output_path: str = "reply.mp3"):
    """
    Generates a voice reply using Google Text-to-Speech (Free, no API key required).
    Adds a slight 'confusion' delay to simulate an elderly person.
    """
    try:
        # Generate speech (Indian English accent 'co.in' if available, else default)
        tts = gTTS(text=text, lang='en', tld='co.in', slow=True)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Voice generation failed: {e}")
        return None

def generate_voice_reply(text: str, session_id: str):
    """
    Generates a voice reply and returns the binary content (for streaming).
    """
    try:
        tts = gTTS(text=text, lang='en', tld='co.in')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.getvalue()
    except Exception as e:
        print(f"Voice generation failed: {e}")
        return None
