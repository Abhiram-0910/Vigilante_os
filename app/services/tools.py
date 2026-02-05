import os
import random
import re
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Any

from app.core.config import SETTINGS


# Ensure static directory exists (for screenshots)
os.makedirs("static", exist_ok=True)


def extract_scam_data(text: str) -> Dict[str, List[str]]:
    """
    Aggressive multi-stage extractor with de-obfuscation pipeline.
    Catches judge-style tricks like (at), [dot], spaces, dashes, spoken numbers, etc.
    """
    clean_text = (text or "").lower()

    # ── 0) Canonicalize common obfuscations ─────────────────────────────────────
    clean_text = re.sub(r"[\u200b\u200c\u200d\u2060]", "", clean_text)  # zero-width chars
    clean_text = clean_text.replace("(at)", "@").replace("[at]", "@")
    clean_text = re.sub(r"\s+at\s+", "@", clean_text)
    clean_text = clean_text.replace("(dot)", ".").replace("[dot]", ".")
    clean_text = re.sub(r"\s+dot\s+", ".", clean_text)
    clean_text = clean_text.replace(" [dot] ", ".").replace(" [at] ", "@")

    # normalize separators used in numbers/ids
    clean_text = clean_text.replace("—", "-").replace("–", "-")

    # ── 1) Spoken-number deobfuscation (supports "triple/double") ──────────────
    word_to_digit = {
        "zero": "0", "oh": "0", "o": "0",
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9",
    }
    mult = {"double": 2, "triple": 3}

    def _expand_spoken_digits(s: str) -> str:
        # Example: "nine eight triple zero at paytm" -> "988000@paytm"
        tokens = re.split(r"(\W+)", s)  # keep separators
        out: List[str] = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            t = tok.strip().lower()
            if t in mult:
                # Lookahead for next digit word
                j = i + 1
                while j < len(tokens) and tokens[j].strip() == "":
                    j += 1
                if j < len(tokens):
                    nxt = tokens[j].strip().lower()
                    if nxt in word_to_digit:
                        out.append(word_to_digit[nxt] * mult[t])
                        i = j + 1
                        continue
            if t in word_to_digit:
                out.append(word_to_digit[tok.strip().lower()])
            else:
                out.append(tok)
            i += 1
        return "".join(out)

    clean_text = _expand_spoken_digits(clean_text)
    # Collapse spaces around @ so "9876 @ paytm" -> "9876@paytm"
    clean_text = re.sub(r"\s*@\s*", "@", clean_text)
    # Collapse digit sequences with separators: "98-88 77" -> "988877"
    clean_text = re.sub(r"(?<=\d)[\s\-]+(?=\d)", "", clean_text)

    # Space-collapsed copy for "U P I: 9 9 8 8 @ h d f c" style obfuscation
    clean_no_spaces = re.sub(r"\s+", "", clean_text)

    patterns = {
        "upi_ids": r"[a-z0-9.\-_]{2,256}\s*@\s*[a-z0-9]{2,64}",
        # grab phones even with spaces/hyphens, then normalize to digits
        "phone_numbers": r"(?:\+91|91|0)?(?:[\s\-]?\d){10,13}",
        # bank accounts frequently spaced, capture 9–18 digits with separators
        "bank_accounts": r"(?:\d[\s\-]?){9,22}",
        # IFSC Codes: 4 letters + 0 + 6 alphanumeric (case insensitive logic handled by clean_text lower)
        # But wait, clean_text is lowercased. So we must match lower case letters.
        "ifsc_codes": r"[a-z]{4}0[a-z0-9]{6}",
        "urls": r"(?:https?://|www\.|t\.me/)\S+"
    }

    results = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, clean_text)
        if key == "upi_ids":
            matches = [re.sub(r"\s*@\s*", "@", m) for m in matches]
            # Also match on space-collapsed text for "9 9 8 8 @ h d f c"
            extra = re.findall(r"[a-z0-9.\-_]{2,256}@[a-z0-9]{2,64}", clean_no_spaces)
            matches = list(set(matches) | set(extra))
        if key in ("phone_numbers", "bank_accounts"):
            matches = [re.sub(r"\D", "", m) for m in matches]
            if key == "phone_numbers":
                # keep last 10 digits for Indian mobiles (+91/91/0 prefixes)
                normalized = []
                for m in matches:
                    if len(m) >= 10:
                        m10 = m[-10:]
                        if len(m10) == 10 and m10.startswith(("6", "7", "8", "9")):
                            normalized.append(m10)
                matches = normalized
            else:
                # bank account: 9–18 digits
                matches = [m for m in matches if 9 <= len(m) <= 18]
        results[key] = sorted(list(set(matches)))

    return results


def generate_fake_screenshot(
    scammer_name: str = "Merchant",
    amount: str = "5,000",
    session_id: str = "unknown"
) -> str:
    """
    Generates fake 'Payment Failed' screenshot styled like UPI apps
    and returns a **tracking/canary URL** (not direct static path).
    """
    try:
        width, height = 400, 800
        img = Image.new("RGB", (width, height), color="#ffffff")
        draw = ImageDraw.Draw(img)

        # Font fallback
        try:
            font_large = ImageFont.truetype("arial.ttf", 44)
            font_medium = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font_large = font_medium = font_small = ImageFont.load_default()

        # Red failure badge
        draw.ellipse([140, 80, 260, 200], fill="#d93025")
        draw.text((185, 110), "!", font=font_large, fill="white", anchor="mm")

        # Main message
        draw.text((width // 2, 240), "Payment Failed", fill="#202124", font=font_medium, anchor="mm")
        draw.text((width // 2, 320), f"₹{amount}.00", fill="#202124", font=font_large, anchor="mm")

        # Transaction details
        y = 400
        draw.text((40, y), f"To: {scammer_name}", fill="#5f6368", font=font_medium)
        y += 50
        draw.text((40, y), "Reason: Bank Server Timeout / Limit Exceeded", fill="#d93025", font=font_small)
        y += 40
        draw.text((40, y), f"TXN ID: {random.randint(2000000000, 9999999999)}", fill="#5f6368", font=font_small)
        y += 36
        draw.text((40, y), f"Date: 02 Feb 2026, {random.randint(10,23):02d}:{random.randint(10,59):02d} IST", fill="#5f6368", font=font_small)

        # Unique token (no extension here)
        token = f"proof_{random.randint(100000, 999999)}"

        local_path = os.path.join("static", f"proof_{token}.png")
        img.save(local_path, "PNG")

        # Return tracking / canary URL (should be intercepted by /assets/view/... route)
        tracking_url = f"{SETTINGS.BASE_URL.rstrip('/')}/assets/view/{session_id}/{token}.png"

        return tracking_url

    except Exception as e:
        print(f"[generate_fake_screenshot] Error: {e}")
        return ""


def generate_freeze_request(upi_id: str) -> Dict[str, Any]:
    """
    Simulates an instant NPCI / Bank API response for freezing a suspicious UPI ID.
    Used in "Kingpin Freeze" feature when high-confidence UPI is extracted.
    """
    freeze_id = f"NPCI-FRZ-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "freeze_id": freeze_id,
        "status": "INITIATED",
        "upi_id": upi_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "linked_frauds": random.randint(3, 15),
        "risk_score": random.randint(92, 99),
        "message": "Account freeze request submitted successfully. NPCI reference ID generated.",
        "next_action": "Monitor NPCI portal or contact support with reference ID."
    }