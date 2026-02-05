"""
Load test: 10 concurrent users, 0% failure rate requirement.
Run: locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host=http://127.0.0.1:8000
Or with UI: locust -f locustfile.py --host=http://127.0.0.1:8000
"""
import os
from locust import HttpUser, task, between

API_KEY = os.getenv("VIBHISHAN_API_KEY", "gov_secure_access_2026")


class ScamAPIUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.headers = {"X-API-KEY": API_KEY}

    @task
    def analyze_scam(self):
        self.client.post(
            "/analyze",
            json={
                "session_id": f"test_{self.environment.runner.user_id or 0}",
                "message_text": "Pay fine to 9876543210@paytm or face arrest",
            },
            headers=self.headers,
            name="/analyze",
        )
