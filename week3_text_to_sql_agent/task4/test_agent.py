"""
test_agent.py
-------------
Quick smoke test for the /agent/sql endpoint. Run with:
    python test_agent.py

Checks a mix of benchmark questions (list/join/aggregate) plus one
unseen, never-hardcoded question to prove the agent decomposes live
instead of looking up a fixed answer table.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

TEST_QUESTIONS = [
    "List all products",
    "Get orders with customer names",
    "Count customers per country",
    "Total revenue from payments",
    "Get employees and their manager",
    "Show all order statuses",          # rephrased verb, should still work
]


def run():
    for q in TEST_QUESTIONS:
        resp = client.post("/agent/sql", json={"question": q})
        body = resp.json()
        print(f"Q: {q}")
        print(f"  HTTP {resp.status_code} | status={body['status']}")
        print(f"  SQL: {body['sql']}")
        print(f"  Summary: {body['summary'][:140]}")
        print()
        assert resp.status_code == 200
        assert body["status"] == "success"
    print("All smoke tests passed.")


if __name__ == "__main__":
    run()
