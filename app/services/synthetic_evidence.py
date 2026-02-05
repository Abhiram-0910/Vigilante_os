import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random

def generate_failed_payment_screenshot(session_id: str, scammer_name: str = "Unknown") -> str:
    """
    Generates a realistic (simulated) 'Payment Failed' screenshot.
    Scammers believe images more than text.
    """
    # 1. Create a canvas (Mobile screen size)
    width, height = 1080, 1920
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # 2. Draw Header (GPay style)
    draw.rectangle([0, 0, width, 200], fill='#4285F4')
    
    # 3. Draw Red 'X' (Failure Icon)
    draw.ellipse([width//2 - 150, 400, width//2 + 150, 700], fill='#EA4335')
    draw.line([width//2 - 70, 470, width//2 + 70, 630], fill='white', width=20)
    draw.line([width//2 + 70, 470, width//2 - 70, 630], fill='white', width=20)
    
    # 4. Draw Text (Generic fonts if specific ones aren't available)
    try:
        # Try to load a standard system font
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_med = ImageFont.truetype("arial.ttf", 50)
    except:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        
    draw.text((width//2 - 300, 800), "Payment Failed", fill='#3c4043', font=font_large)
    
    reason = random.choice([
        "Security risk detected by bank",
        "Receiver's account reported for fraud",
        "Insufficient funds in source account",
        "UPI Server Timeout (NPCI-ERR-99)"
    ])
    
    draw.text((width//2 - 350, 950), f"To: {scammer_name}", fill='#5f6368', font=font_med)
    draw.text((width//2 - 400, 1050), f"Reason: {reason}", fill='#d93025', font=font_med)
    
    # 5. Add Transaction ID & Timestamp
    tx_id = f"TXN{random.randint(100000, 999999)}VIBH"
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    draw.text((width//2 - 350, 1200), f"TXN ID: {tx_id}", fill='#5f6368', font=font_med)
    draw.text((width//2 - 350, 1300), f"Time: {now}", fill='#5f6368', font=font_med)
    
    # 6. Save to static folder
    os.makedirs("static/evidence", exist_ok=True)
    file_path = f"static/evidence/fail_{session_id}.png"
    img.save(file_path)
    
    return file_path
