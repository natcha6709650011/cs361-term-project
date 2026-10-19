import json
import os
import time
import uuid

import boto3
from botocore.config import Config

BUCKET = os.environ["IMAGE_BUCKET"]
REGION = os.environ.get("AWS_REGION", "us-east-1")
EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_BYTES = 5 * 1024 * 1024

s3 = boto3.client("s3", region_name=REGION, config=Config(signature_version="s3v4"))


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def get_role(event):
    ctx = (event.get("requestContext") or {}).get("authorizer") or {}
    if isinstance(ctx.get("lambda"), dict):
        ctx = ctx["lambda"]
    return str(ctx.get("role") or "").lower()


def lambda_handler(event, context):
    method = (event.get("httpMethod") or (event.get("requestContext") or {}).get("http", {}).get("method") or "").upper()
    if method == "OPTIONS":
        return response(200, {"message": "OK"})
    if method != "POST":
        return response(405, {"message": "Method not allowed"})

    if get_role(event) != "facility_admin":
        return response(403, {"message": "You do not have permission to manage rooms"})

    room_id = (event.get("pathParameters") or {}).get("room_id", "")
    if not str(room_id).isdigit() or int(room_id) <= 0:
        return response(400, {"message": "Invalid room_id"})

    try:
        body = json.loads(event.get("body") or "{}")
    except ValueError:
        return response(400, {"message": "Invalid JSON body"})

    content_type = body.get("content_type")
    size = body.get("size")
    if content_type not in EXT:
        return response(400, {"message": "รองรับเฉพาะไฟล์ JPG, PNG, WebP"})
    if not isinstance(size, int) or size <= 0 or size > MAX_BYTES:
        return response(400, {"message": "ไฟล์ต้องมีขนาดไม่เกิน 5 MB"})

    key = f"room-{room_id}-{time.strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:6]}.{EXT[content_type]}"
    post = s3.generate_presigned_post(
        Bucket=BUCKET,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, MAX_BYTES],
        ],
        ExpiresIn=300,
    )
    return response(200, {
        "upload_url": post["url"],
        "fields": post["fields"],
        "image_url": f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}",
    })