# /app/routers/tracking.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
import os
import time
from app.services.observability import observability

router = APIRouter()

@router.get("/assets/view/{session_id}/{token}.png")
async def serve_canary_image(session_id: str, token: str, request: Request):
    """
    THE CANARY TRAP.
    Serves the 'fake payment' screenshot but logs the requester's IP first.
    """
    # 1. Capture Intelligence + Geo-Location
    scammer_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    geo = observability.get_geo_from_ip(scammer_ip)
    
    # 2. Log to Intelligence Dashboard
    observability.log_decision(
        session_id=session_id,
        event_type="CANARY_TRIGGERED",
        actor="Scammer",
        decision="Viewed Payment Proof",
        reasoning=f"Tracking Pixel Fired. IP: {scammer_ip} | City: {geo['city']} | ISP: {geo['isp']}",
        confidence=1.0,
        input_data=token,
        output_data="Image Served",
        metadata={"geo": geo, "user_agent": user_agent}
    )
    
    # 3. Serve the actual image (so they don't get suspicious)
    # In a real app, 'token' maps to the specific file. 
    # For hackathon, we assume the token IS the filename hash or we serve a generic proof.
    
    image_path = f"static/proof_{token}.png"
    if not os.path.exists(image_path):
        # Fallback if specific file missing
        image_path = "static/default_proof.png" 
        
    return FileResponse(image_path)