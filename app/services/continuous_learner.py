import json
import os
from collections import defaultdict

LEARNING_FILE = "tactical_knowledge.json"

class ContinuousLearner:
    def __init__(self):
        self.stats = defaultdict(lambda: {"success": 0, "fail": 0})
        self.patterns = defaultdict(list)
        self._load()

    def record_outcome(self, tactic: str, extracted_intel: dict, scam_type: str, message: str):
        # Determine success (Did we get intel?)
        success = bool(extracted_intel.get("upi_ids") or extracted_intel.get("bank_accounts"))
        
        key = tactic
        if success:
            self.stats[key]["success"] += 1
            self.patterns[scam_type].append(message) # Store successful triggers
        else:
            self.stats[key]["fail"] += 1
        
        self._save()

    def get_emerging_patterns(self):
        # Find recurring phrases in successful scam messages
        # (Simplified logic for demo)
        alerts = []
        for stype, msgs in self.patterns.items():
            if len(msgs) > 2:
                alerts.append({"type": "NEW_SCRIPT", "scam": stype, "count": len(msgs)})
        return alerts

    def _save(self):
        with open(LEARNING_FILE, "w") as f:
            json.dump({"stats": self.stats, "patterns": self.patterns}, f)

    def _load(self):
        if os.path.exists(LEARNING_FILE):
            try:
                with open(LEARNING_FILE, "r") as f:
                    data = json.load(f)
                    self.stats.update(data.get("stats", {}))
                    self.patterns.update(data.get("patterns", {}))
            except: pass

    def sync_global_intelligence(self):
        """
        Simulates Transfer Learning from global scam databases.
        Downloads emerging script patterns from central VIBHISHAN node.
        """
        global_patterns = {
            "Customs Scam": ["package held", "drugs found", "illegal items"],
            "E-Challan Fraud": ["traffic violation", "pay fine online", "vahan portal"]
        }
        for stype, phrases in global_patterns.items():
            if phrases[0] not in self.patterns[stype]:
                self.patterns[stype].extend(phrases)
        self._save()
        print("GLOBAL SYNC: Transfer Learning complete. New script patterns loaded.")

learner = ContinuousLearner()