"""DynamoDB-backed competitive intelligence tracker.

Stores competitor mentions extracted from call notes.
"""
import boto3
import time
from datetime import datetime
from botocore.exceptions import ClientError
from config import AWS_REGION

TABLE_NAME = "CompetitiveIntel"
TTL_DAYS = 365  # keep for a year

_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
_table = None


def _ensure_table():
    """Create the DynamoDB table if it doesn't exist."""
    global _table
    client = boto3.client("dynamodb", region_name=AWS_REGION)
    try:
        client.describe_table(TableName=TABLE_NAME)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "competitor", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "competitor", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=TABLE_NAME)
        try:
            client.update_time_to_live(
                TableName=TABLE_NAME,
                TimeToLiveSpecification={"Enabled": True, "AttributeName": "expiry_ttl"},
            )
        except Exception:
            pass
    _table = _dynamodb.Table(TABLE_NAME)


def save_competitor_mentions(customer_name: str, mentions: list):
    """Save extracted competitor mentions to DynamoDB."""
    global _table
    if _table is None:
        _ensure_table()
    ts = datetime.now().isoformat()
    for m in mentions:
        competitor = m.get("competitor", "").strip()
        if not competitor:
            continue
        _table.put_item(Item={
            "competitor": competitor,
            "timestamp": ts,
            "customer": customer_name,
            "context": m.get("context", ""),
            "sentiment": m.get("sentiment", "neutral"),
            "expiry_ttl": int(time.time()) + (TTL_DAYS * 86400),
        })


def get_all_mentions(limit=100) -> list:
    """Return all competitor mentions, sorted by most recent."""
    global _table
    if _table is None:
        _ensure_table()
    resp = _table.scan(Limit=limit)
    items = resp.get("Items", [])
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items


def get_mentions_by_competitor(competitor: str) -> list:
    """Return all mentions of a specific competitor."""
    global _table
    if _table is None:
        _ensure_table()
    resp = _table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("competitor").eq(competitor),
        ScanIndexForward=False,
    )
    return resp.get("Items", [])


def get_competitor_summary() -> dict:
    """Return a summary: {competitor: count} sorted by frequency."""
    items = get_all_mentions(limit=500)
    counts = {}
    for item in items:
        comp = item.get("competitor", "")
        counts[comp] = counts.get(comp, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
