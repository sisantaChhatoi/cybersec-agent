"""Quick diagnostic: checks an account's incident_count in Neo4j, and
optionally prints a session's raw conversation from Mongo for debugging.

Usage:
    python -m src.graph._check account 414253647586
    python -m src.graph._check session cli-e9b8a1bd
"""
import sys

from dotenv import load_dotenv

load_dotenv()


def check_account(value: str) -> None:
    from src.graph.neo4j_client import get_database, get_driver

    driver = get_driver()
    db = get_database()
    with driver.session(database=db) as session:
        result = session.run(
            "MATCH (a:MuleAccount {value: $v}) RETURN a.incident_count AS c, a.incident_ids AS ids", v=value
        ).single()
        print(result)
    driver.close()


def check_session(session_id: str) -> None:
    import os

    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGODB_URI"])
    doc = client["digital_arrest_shield"]["incidents"].find_one({"session_id": session_id})
    if not doc:
        print("No incident found for that session_id.")
        return
    print("--- fields ---")
    for field in (
        "caller_number", "mule_account", "mule_account_bank_name", "mule_upi",
        "victim_region", "scam_type", "claimed_authority", "amount_demanded",
        "amount_lost", "payment_method", "remote_app_requested",
    ):
        print(f"{field}: {doc.get(field)}")
    print("--- raw_conversation ---")
    print(doc.get("raw_conversation", "(none)"))


if __name__ == "__main__":
    mode, value = sys.argv[1], sys.argv[2]
    if mode == "account":
        check_account(value)
    elif mode == "session":
        check_session(value)
    else:
        print("Usage: python -m src.graph._check account|session <value>")
