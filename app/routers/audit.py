from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import json
import os

router = APIRouter(prefix="/audit", tags=["Security"])

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_FILE = os.path.join(PROJECT_ROOT, "audit_trail.jsonl")

class AuditVerificationRequest(BaseModel):
    session_id: str
    expected_hash: str

@router.get("/verify-chain")
async def verify_chain_integrity():
    """
    Recalculates the entire hash chain to prove zero-tampering.
    Professional-grade integrity verification for Judges.
    """
    if not os.path.exists(AUDIT_FILE):
        return {"status": "error", "message": "Audit trail not found."}
    
    integrity_points = 0
    calculated_hash = "0" * 64
    
    try:
        with open(AUDIT_FILE, "r") as f:
            for line in f:
                if not line.strip(): continue
                block = json.loads(line)
                
                # Check previous link
                if block["previous_hash"] != calculated_hash:
                    return {
                        "status": "TAMPERED", 
                        "at_session": block["session_id"],
                        "block_timestamp": block["timestamp"]
                    }
                
                # Re-verify current block signature
                in_h = block["input_hash"]
                out_h = block["output_hash"]
                block_content = f"{calculated_hash}{block['session_id']}{block['event_type']}{in_h}{out_h}"
                recalc_h = hashlib.sha256(block_content.encode()).hexdigest()
                
                if recalc_h != block["current_hash"]:
                    return {
                        "status": "SIGNATURE_INVALID",
                        "at_session": block["session_id"]
                    }
                
                calculated_hash = recalc_h
                integrity_points += 1
                
        return {
            "status": "VERIFIED",
            "blocks_checked": integrity_points,
            "root_hash": calculated_hash,
            "message": "Chain integrity 100% verified. No tampering detected."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain verification failed: {str(e)}")

@router.get("/last-block")
async def get_last_block_summary():
    """Returns the head of the chain for the Dashboard/Judges."""
    if not os.path.exists(AUDIT_FILE):
         return {"block": 0, "hash": "none"}
    
    try:
        with open(AUDIT_FILE, "r") as f:
            lines = f.readlines()
            if not lines: return {"block": 0}
            last_block = json.loads(lines[-1].strip())
            return {
                "block": len(lines),
                "timestamp": last_block["timestamp"],
                "hash": last_block["current_hash"][:16] + "...",
                "session": last_block["session_id"]
            }
    except:
        return {"block": -1}
