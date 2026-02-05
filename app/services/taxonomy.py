# /app/services/taxonomy.py
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any

TAXONOMY_DB = "scammer_taxonomy.json"


class ScammerTaxonomy:
    """
    Persistent lightweight database of known scammer profiles.
    Tracks repeat offenders across sessions using phone, UPI, voice fingerprint, etc.
    Supports coordination detection (same fingerprint in multiple sessions close in time).
    """

    def __init__(self):
        self.db: Dict[str, Dict[str, Any]] = {}
        self._load_db()

    def _load_db(self) -> None:
        """Load existing taxonomy from disk or initialize empty."""
        if os.path.exists(TAXONOMY_DB):
            try:
                with open(TAXONOMY_DB, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
            except Exception as e:
                print(f"Failed to load taxonomy DB: {e}")
                self.db = {}
        else:
            self.db = {}

    def _save_db(self) -> None:
        """Persist current taxonomy to disk (atomic write)."""
        try:
            # Write to temp file first → atomic replace
            tmp_path = TAXONOMY_DB + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=2, sort_keys=True)
            os.replace(tmp_path, TAXONOMY_DB)
        except Exception as e:
            print(f"Failed to save taxonomy DB: {e}")

    def get_profile(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve profile for a given identifier (phone, UPI, voice fingerprint hash, etc.)
        
        Args:
            identifier: Unique scammer key (str)
            
        Returns:
            Profile dict or None if not found
        """
        return self.db.get(identifier)

    def update_profile(self, identifier: str, data: Dict[str, Any]) -> None:
        """
        Update or create profile for a scammer identifier.
        
        Args:
            identifier: Unique key (phone, UPI, fingerprint hash, etc.)
            data: Dict with at least 'scam_score' and optionally 'scam_type'
        """
        if not identifier or not isinstance(identifier, str):
            return

        profile = self.db.get(identifier, {
            "first_seen": datetime.now().isoformat(),
            "risk_score": 0,
            "scam_types": [],
            "encounters": 0,
            "fingerprint": None,           # optional – can store voice hash
            "last_seen": None,
            "last_session_id": None
        })

        now_iso = datetime.now().isoformat()

        profile["last_seen"] = now_iso
        profile["encounters"] += 1
        profile["risk_score"] = max(profile["risk_score"], data.get("scam_score", 0))

        # Add new scam type if not already present
        scam_type = data.get("scam_type")
        if scam_type and scam_type not in profile["scam_types"]:
            profile["scam_types"].append(scam_type)

        # Optional: update fingerprint if provided
        if "fingerprint" in data:
            profile["fingerprint"] = data["fingerprint"]

        # Optional: store last session for coordination tracking
        if "session_id" in data:
            profile["last_session_id"] = data["session_id"]

        self.db[identifier] = profile
        self._save_db()

    def check_coordination(
        self,
        fingerprint: str,
        window_minutes: int = 10,
        exclude_session: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if the same fingerprint (voice / behavioral) is active 
        across **multiple sessions** within a short time window.
        
        Useful for identifying coordinated multi-scammer attacks.
        
        Args:
            fingerprint: Voice hash / behavioral fingerprint to check
            window_minutes: Time window to look back (default 10 min)
            exclude_session: Optional session ID to ignore (current session)
            
        Returns:
            Dict with coordination status and details
        """
        if not fingerprint:
            return {"coordinated": False, "count": 0, "sessions": []}

        now = datetime.now()
        window_seconds = window_minutes * 60
        active_sessions = []

        for pid, profile in self.db.items():
            if profile.get("fingerprint") != fingerprint:
                continue

            last_seen_str = profile.get("last_seen")
            if not last_seen_str:
                continue

            try:
                last_seen = datetime.fromisoformat(last_seen_str)
            except ValueError:
                continue

            time_diff = (now - last_seen).total_seconds()

            if time_diff < window_seconds:
                session_id = profile.get("last_session_id")
                if session_id and session_id != exclude_session:
                    active_sessions.append({
                        "session_id": session_id,
                        "last_seen": last_seen_str,
                        "seconds_ago": int(time_diff),
                        "risk_score": profile.get("risk_score", 0)
                    })

        coordinated = len(active_sessions) > 0  # >0 other sessions = coordination

        return {
            "coordinated": coordinated,
            "count_other_sessions": len(active_sessions),
            "active_sessions": active_sessions,
            "window_minutes": window_minutes
        }


# Global singleton instance (recommended usage pattern)
taxonomy = ScammerTaxonomy()