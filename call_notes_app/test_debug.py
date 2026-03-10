"""Quick debug: print the exact JSON body being sent to Bedrock."""
import json
import boto3
from botocore.config import Config
from config import AWS_REGION, CLAUDE_MODEL_ID

client = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    config=Config(read_timeout=300),
)

payload = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 65536,
    "system": "You are a helpful assistant.",
    "messages": [{"role": "user", "content": "Say hello."}],
}

body = json.dumps(payload)
print("Sending body:")
print(json.dumps(json.loads(body), indent=2))
print(f"\nboto3 version: {boto3.__version__}")

try:
    resp = client.invoke_model_with_response_stream(
        modelId=CLAUDE_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    for event in resp["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk.get("type") == "content_block_delta":
            print(chunk["delta"].get("text", ""), end="", flush=True)
    print("\n\nSuccess!")
except Exception as e:
    print(f"\nError: {e}")
    print("\nTrying with max_tokens=8192 instead...")
    payload["max_tokens"] = 8192
    body = json.dumps(payload)
    try:
        resp = client.invoke_model_with_response_stream(
            modelId=CLAUDE_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        for event in resp["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk.get("type") == "content_block_delta":
                print(chunk["delta"].get("text", ""), end="", flush=True)
        print("\n\nSuccess with 8192!")
    except Exception as e2:
        print(f"\nAlso failed with 8192: {e2}")
