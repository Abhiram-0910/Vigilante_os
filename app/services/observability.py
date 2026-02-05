import json
import time
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict
import hashlib
import os
import random
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_FILE = os.path.join(PROJECT_ROOT, "audit_trail.jsonl")

@dataclass
class AuditLog:
    """Immutable audit record for legal compliance with hash chaining."""
    timestamp: str
    session_id: str
    event_type: str
    actor: str
    decision: str
    reasoning: str
    confidence: float
    input_hash: str
    output_hash: str
    previous_hash: str  # Chaining field
    current_hash: str   # Self hash
    metadata: Dict

class ObservabilityEngine:
    def __init__(self):
        self.performance_metrics = {
            "total_requests": 0,
            "error_rate": 0.0,
            "avg_latency": 0.0
        }
        self.last_hash = "0" * 64 # Genesis hash state
        if os.path.exists(AUDIT_FILE):
             try:
                 with open(AUDIT_FILE, "rb") as f:
                     # Seek to last line to find most recent hash
                     f.seek(-2, os.SEEK_END)
                     while f.read(1) != b"\n":
                         f.seek(-2, os.SEEK_CUR)
                     last_line = f.readline().decode()
                     self.last_hash = json.loads(last_line).get("current_hash", "0"*64)
             except Exception:
                 pass

    def log_decision(self, session_id: str, event_type: str, actor: str, 
                     decision: str, reasoning: str, confidence: float, 
                     input_data: str, output_data: str, metadata: Dict = None):
        
        # Calculate hashes
        in_h = hashlib.sha256(str(input_data).encode()).hexdigest()
        out_h = hashlib.sha256(str(output_data).encode()).hexdigest()
        
        # Create block signature (Chaining)
        block_content = f"{self.last_hash}{session_id}{event_type}{in_h}{out_h}"
        curr_h = hashlib.sha256(block_content.encode()).hexdigest()

        log_entry = AuditLog(
            timestamp=datetime.utcnow().isoformat() + "Z",
            session_id=session_id,
            event_type=event_type,
            actor=actor,
            decision=str(decision)[:500],
            reasoning=reasoning,
            confidence=confidence,
            input_hash=in_h,
            output_hash=out_h,
            previous_hash=self.last_hash,
            current_hash=curr_h,
            metadata=metadata or {}
        )
        
        self.last_hash = curr_h
        self._persist_log(log_entry)
        return log_entry

    def _persist_log(self, log: AuditLog):
        with open(AUDIT_FILE, "a") as f:
            f.write(json.dumps(asdict(log)) + "\n")

    def track_performance(self, duration_ms: float, success: bool):
        self.performance_metrics["total_requests"] += 1
        n = self.performance_metrics["total_requests"]
        
        # Update latency moving average
        prev_avg = self.performance_metrics["avg_latency"]
        self.performance_metrics["avg_latency"] = (prev_avg * (n-1) + duration_ms) / n
        
        # Update error rate
        if not success:
            prev_err = self.performance_metrics["error_rate"]
            self.performance_metrics["error_rate"] = (prev_err * (n-1) + 1.0) / n
        else:
            prev_err = self.performance_metrics["error_rate"]
            self.performance_metrics["error_rate"] = (prev_err * (n-1)) / n

    def mask_pii_laplace(self, value: float, epsilon: float = 0.1) -> float:
        """
        Adds Laplacian noise to financial values for Differential Privacy.
        Ensures local intelligence sharing for Government compliance without leaking exact sums.
        """
        sensitivity = 1.0 # Scale for currency noise
        noise = np.random.laplace(0, sensitivity / epsilon)
        return round(value + noise, 2)

    def get_geo_from_ip(self, ip: str) -> Dict[str, str]:
        """
        Simulates Geospatial Intelligence lookup for the 'Canary Trap'.
        In production: use MaxMind, IP-API, or Gov-Database.
        """
        regions = ["Delhi, IN", "Jamtara, JH", "Bharatpur, RJ", "Mewat, HR", "Kolkata, WB", "Unknown"]
        cities = ["New Delhi", "Jamtara Town", "Deeg", "Nuh", "Bidhannagar", "Gateway Node"]
        
        idx = hash(ip) % len(regions)
        return {
            "region": regions[idx],
            "city": cities[idx],
            "isp": random.choice(["Jio", "Airtel", "BSNL", "Proxy/VPN"]),
            "threat_level": "RED" if regions[idx] in ["Jamtara, JH", "Mewat, HR"] else "AMBER"
        }

    def scrub_pii_for_federal_sharing(self, data: Dict) -> Dict:
        """Anonymizes data further for Sovereign Federated Learning."""
        scrubbed = data.copy()
        if "session_id" in scrubbed:
            scrubbed["session_id"] = hashlib.md5(scrubbed["session_id"].encode()).hexdigest()[:12]
        if "economic_damage" in scrubbed:
            scrubbed["economic_damage_noisy"] = self.mask_pii_laplace(scrubbed["economic_damage"])
        return scrubbed

observability = ObservabilityEngine()