"""One-time migration: export DynamoDB data to local SQLite, then delete the tables.

Run this once:  python migrate_dynamo_to_sqlite.py

It will:
1. Pull all records from the 3 DynamoDB tables
2. Insert them into the local SQLite database (call_notes.db)
3. Ask for confirmation, then delete the DynamoDB tables
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import boto3
from config import AWS_REGION

# Import the new SQLite-backed modules (creates tables automatically)
from transcription.history import save_session, _get_conn as get_history_conn
from retrieval.chat_history import save_chat_session, _get_conn as get_chat_conn
from transcription.competitive_intel import _get_conn as get_intel_conn

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
client = boto3.client("dynamodb", region_name=AWS_REGION)

TABLES = ["CallNotesHistory", "ChatSessionHistory", "CompetitiveIntel"]


def table_exists(name):
    try:
        client.describe_table(TableName=name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def migrate_call_notes_history():
    if not table_exists("CallNotesHistory"):
        print("  CallNotesHistory — table not found, skipping")
        return 0
    table = dynamodb.Table("CallNotesHistory")
    resp = table.scan()
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))

    conn = get_history_conn()
    for item in items:
        conn.execute(
            "INSERT OR IGNORE INTO call_notes_history "
            "(customer_name, timestamp, transcript, notes, docx_path, followup_email, expiry_ttl) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item.get("customer_name", ""), item.get("timestamp", ""),
             item.get("transcript", ""), item.get("notes", ""),
             item.get("docx_path", ""), item.get("followup_email", ""),
             int(item.get("expiry_ttl", 0))),
        )
    conn.commit()
    print(f"  CallNotesHistory — migrated {len(items)} records")
    return len(items)


def migrate_chat_sessions():
    if not table_exists("ChatSessionHistory"):
        print("  ChatSessionHistory — table not found, skipping")
        return 0
    table = dynamodb.Table("ChatSessionHistory")
    resp = table.scan()
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))

    conn = get_chat_conn()
    for item in items:
        conn.execute(
            "INSERT OR IGNORE INTO chat_session_history "
            "(session_type, timestamp, title, customer, source_filter, history_json, turn_count, expiry_ttl) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item.get("session_type", ""), item.get("timestamp", ""),
             item.get("title", ""), item.get("customer", ""),
             item.get("source_filter", ""), item.get("history_json", "[]"),
             int(item.get("turn_count", 0)), int(item.get("expiry_ttl", 0))),
        )
    conn.commit()
    print(f"  ChatSessionHistory — migrated {len(items)} records")
    return len(items)


def migrate_competitive_intel():
    if not table_exists("CompetitiveIntel"):
        print("  CompetitiveIntel — table not found, skipping")
        return 0
    table = dynamodb.Table("CompetitiveIntel")
    resp = table.scan()
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))

    conn = get_intel_conn()
    for item in items:
        conn.execute(
            "INSERT OR IGNORE INTO competitive_intel "
            "(competitor, timestamp, customer, context, sentiment, expiry_ttl) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item.get("competitor", ""), item.get("timestamp", ""),
             item.get("customer", ""), item.get("context", ""),
             item.get("sentiment", "neutral"), int(item.get("expiry_ttl", 0))),
        )
    conn.commit()
    print(f"  CompetitiveIntel — migrated {len(items)} records")
    return len(items)


def delete_dynamo_tables():
    for name in TABLES:
        if table_exists(name):
            client.delete_table(TableName=name)
            print(f"  Deleted DynamoDB table: {name}")
        else:
            print(f"  {name} — already gone")


if __name__ == "__main__":
    print("\n=== Step 1: Migrating DynamoDB data to local SQLite ===\n")
    total = 0
    total += migrate_call_notes_history()
    total += migrate_chat_sessions()
    total += migrate_competitive_intel()
    print(f"\nTotal records migrated: {total}")
    print(f"SQLite database: {os.path.abspath(os.path.join(os.path.dirname(__file__), 'call_notes.db'))}")

    print("\n=== Step 2: Delete DynamoDB tables ===\n")
    answer = input("Delete the 3 DynamoDB tables now? (yes/no): ").strip().lower()
    if answer == "yes":
        delete_dynamo_tables()
        print("\nDone! All data is now local only.")
    else:
        print("\nSkipped table deletion. You can delete them manually later.")
        print("Tables: CallNotesHistory, ChatSessionHistory, CompetitiveIntel")
