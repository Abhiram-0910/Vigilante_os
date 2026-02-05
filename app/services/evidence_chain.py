# app/services/evidence_chain.py
import hashlib
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, Optional

DB_NAME = "evidence_ledger.db"


class JudicialEvidenceChain:
    """
    Tamper-evident evidence ledger implementing a cryptographic hash chain.
    
    Each entry contains:
    - prev_hash (links to previous block)
    - timestamp
    - session_id
    - event_type
    - content (JSON-serializable dict)
    - data_hash = SHA256(prev_hash + timestamp + session_id + event_type + content_json)
    
    Any modification to any row breaks the chain from that point onward.
    """

    def __init__(self):
        self.db_path = DB_NAME
        self._init_database()

    def _init_database(self) -> None:
        """Create the evidence chain table if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_chain (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id      TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,          -- ISO 8601
                    event_type      TEXT NOT NULL,
                    content_json    TEXT NOT NULL,          -- JSON string
                    prev_hash       TEXT NOT NULL,
                    data_hash       TEXT NOT NULL UNIQUE,   -- SHA256 integrity check
                    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON evidence_chain(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON evidence_chain(data_hash)")
            conn.commit()

    def _compute_block_hash(
        self,
        prev_hash: str,
        timestamp: str,
        session_id: str,
        event_type: str,
        content_json: str
    ) -> str:
        """Deterministic hash: SHA256(prev_hash || timestamp || session || type || content)"""
        data = f"{prev_hash}{timestamp}{session_id}{event_type}{content_json}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _get_latest_hash(self) -> str:
        """Fetch hash of the most recent block or return genesis hash."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data_hash FROM evidence_chain ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else "GENESIS_BLOCK_0000000000000000000000000000000000000000000000000000000000000000"

    def log_evidence(
        self,
        session_id: str,
        event_type: str,
        content: Dict[str, Any]
    ) -> str:
        """
        Append a new tamper-evident evidence block to the chain.
        
        Returns: the hash of the newly created block
        """
        if not session_id or not event_type:
            raise ValueError("session_id and event_type are required")

        # Prepare block content
        timestamp = datetime.utcnow().isoformat() + "Z"  # UTC ISO 8601
        content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))

        # Get previous hash (links the chain)
        prev_hash = self._get_latest_hash()

        # Compute this block's hash (includes prev_hash → tamper-evident)
        current_hash = self._compute_block_hash(
            prev_hash=prev_hash,
            timestamp=timestamp,
            session_id=session_id,
            event_type=event_type,
            content_json=content_json
        )

        # Insert into database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO evidence_chain 
                (session_id, timestamp, event_type, content_json, prev_hash, data_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, timestamp, event_type, content_json, prev_hash, current_hash)
            )
            conn.commit()

        return current_hash

    def verify_chain_integrity(self, session_id: Optional[str] = None) -> tuple[bool, str]:
        """
        Verify the entire chain (or chain for one session) has not been tampered with.
        
        Returns: (is_valid: bool, message: str)
        """
        where_clause = "WHERE session_id = ?" if session_id else ""
        params = (session_id,) if session_id else ()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT id, timestamp, session_id, event_type, content_json, prev_hash, data_hash
                FROM evidence_chain
                {where_clause}
                ORDER BY id ASC
                """,
                params
            )

            rows = cursor.fetchall()
            if not rows:
                return True, "No entries found → chain is trivially valid"

            previous_hash = "GENESIS_BLOCK_0000000000000000000000000000000000000000000000000000000000000000"

            for row in rows:
                (
                    entry_id, ts, sid, etype, content_json, prev_hash, stored_hash
                ) = row

                # Re-compute what the hash should be
                computed_hash = self._compute_block_hash(
                    prev_hash=prev_hash,
                    timestamp=ts,
                    session_id=sid,
                    event_type=etype,
                    content_json=content_json
                )

                if computed_hash != stored_hash:
                    return False, f"Tampering detected at entry ID {entry_id} (hash mismatch)"

                if prev_hash != previous_hash:
                    return False, f"Broken chain link at entry ID {entry_id} (prev_hash mismatch)"

                previous_hash = stored_hash

        return True, f"Chain intact ({len(rows)} entries verified)"

    def get_chain_for_session(self, session_id: str) -> list[Dict]:
        """Retrieve full verifiable chain for a given session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, event_type, content_json, prev_hash, data_hash
                FROM evidence_chain
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,)
            )
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "event_type": r[2],
                    "content": json.loads(r[3]),
                    "prev_hash": r[4],
                    "data_hash": r[5]
                }
                for r in cursor.fetchall()
            ]