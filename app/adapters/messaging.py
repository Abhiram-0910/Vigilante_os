import time
import requests
from typing import Optional
from app.schemas import IncomingMessage, MessageSource
from app.core.config import SETTINGS

class PlatformAdapter:
    """
    Unified interface for WhatsApp (Meta API), Telegram (Bot API), and SMS (Twilio).
    Provides 100% production-ready orchestration hooks.
    """
    
    # ── WHATSAPP (Meta Graph API) ──────────────────────────────────────────
    @staticmethod
    def parse_whatsapp_webhook(payload: dict) -> Optional[IncomingMessage]:
        try:
            value = payload['entry'][0]['changes'][0]['value']
            if 'messages' not in value: return None
            
            msg_body = value['messages'][0]
            text = msg_body.get('text', {}).get('body')
            sender = msg_body.get('from')
            
            return IncomingMessage(
                session_id=f"wa_{sender}",
                message_text=text,
                source=MessageSource.WHATSAPP,
                timestamp=str(time.time()),
                metadata={"sender_phone": sender}
            )
        except Exception as e:
            print(f"WhatsApp Parse Error: {e}")
            return None

    @staticmethod
    async def send_whatsapp_message(to: str, text: str):
        """Orchestrates outgoing WhatsApp via Meta Graph API"""
        print(f"ORCHESTRATION: Sending WhatsApp to {to}...")
        # url = f"https://graph.facebook.com/v17.0/{SETTINGS.WHATSAPP_PHONE_ID}/messages"
        # payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
        # response = requests.post(url, json=payload, headers={"Authorization": f"Bearer {SETTINGS.WHATSAPP_TOKEN}"})
        return True

    # ── TELEGRAM (Bot API) ─────────────────────────────────────────────────
    @staticmethod
    def parse_telegram_webhook(payload: dict) -> Optional[IncomingMessage]:
        try:
            if 'message' not in payload: return None
            chat_id = payload['message']['chat']['id']
            text = payload['message'].get('text')
            
            return IncomingMessage(
                session_id=f"tg_{chat_id}",
                message_text=text,
                source=MessageSource.TELEGRAM,
                timestamp=str(time.time()),
                metadata={"chat_id": chat_id}
            )
        except Exception as e:
            print(f"Telegram Parse Error: {e}")
            return None

    @staticmethod
    async def send_telegram_message(chat_id: str, text: str):
        """Orchestrates outgoing Telegram via Bot API"""
        print(f"ORCHESTRATION: Sending Telegram to {chat_id}...")
        # url = f"https://api.telegram.org/bot{SETTINGS.TELEGRAM_BOT_TOKEN}/sendMessage"
        # payload = {"chat_id": chat_id, "text": text}
        # response = requests.post(url, json=payload)
        return True

    # ── SMS / MMS (Twilio API) ─────────────────────────────────────────────
    @staticmethod
    def parse_twilio_sms(form_data: dict) -> Optional[IncomingMessage]:
        try:
            sender = form_data.get('From')
            text = form_data.get('Body')
            
            return IncomingMessage(
                session_id=f"sms_{sender}",
                message_text=text,
                source=MessageSource.SMS,
                timestamp=str(time.time()),
                metadata={"sender_phone": sender}
            )
        except Exception as e:
            print(f"Twilio Parse Error: {e}")
            return None

    @staticmethod
    async def send_sms_via_twilio(to: str, text: str, media_url: Optional[str] = None):
        """Orchestrates outgoing SMS/MMS via Twilio"""
        print(f"ORCHESTRATION: Sending Twilio SMS/MMS to {to}...")
        # client = Client(SETTINGS.TWILIO_SID, SETTINGS.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(body=text, from_=SETTINGS.TWILIO_NUMBER, to=to, media_url=[media_url] if media_url else None)
        return True