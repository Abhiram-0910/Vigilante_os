# /app/services/mock_govt_apis.py
import random
import uuid
from datetime import datetime

class GovernmentSimulationLayer:
    """Simulates NPCI, TRAI, and Police APIs for automated evaluation stability."""
    @staticmethod
    def npci_upi_lookup(upi_id: str):
        return {"status": "ACTIVE", "bank": "SBI", "risk": "LOW", "kyc": True}

    @staticmethod
    def trai_dnd_check(phone: str):
        return {"status": "DND_ACTIVE", "reports": random.randint(0, 10)}

    @staticmethod
    def file_fir_automatically(evidence: dict):
        return {"fir_no": f"FIR/2026/CYB/{random.randint(1000,9999)}", "status": "FILED"}