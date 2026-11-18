"""CS361 V5 room-booking Locust test, adapted from the course's starter template.

Workload: GET /rooms (40%), GET /rooms/{room_number} (40%),
          POST /bookings (20%). Every successful POST writes a real RDS row.

Shape: 0-2min 10 users, 2-4min 20 users, 4-6min 40 users,
       6-12min 80 users; ramp at 5 users/second; stops at 12min.

Before starting (PowerShell):
    aws sso login --profile cs361-dev
    aws sts get-caller-identity --profile cs361-dev
    py -3 -m locust -f locustfile.py \
       --host https://i1125qz211.execute-api.us-east-1.amazonaws.com \
       --web-host 127.0.0.1

The public V5 API has MOCK_LOGIN_ENABLED=false. This script signs short-lived
JWTs locally using AWS Secrets Manager in the authorized developer account;
it does not call /auth/login or the TU identity provider. Do not commit or
share any signing keys or generated tokens. Run only on a trusted computer.
"""

import itertools
import json
import os
import random
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import boto3
import jwt
from locust import HttpUser, LoadTestShape, between, task

# ----- Real V5 paths (not the generic /api/items template paths) -----
LIST_PATH = "/rooms"
DETAIL_PATH = "/rooms/{id}"
SAVE_PATH = "/bookings"
LOGIN_PATH = None  # No mock login against the public /auth/login endpoint.
DETAIL_IDS = ["107", "214", "215", "301", "302", "303", "304", "305", "314", "315", "316"]
BOOKABLE_ROOMS = ["214", "215", "301", "302", "303", "304", "305", "314", "315", "316"]

# Pre-existing mock users. All five have permission for room type 3.
TEST_USERS = [
    ("employee001", "employee", "employee"),
    ("master001", "student", "student"),
    ("doctoral001", "student", "student"),
    ("staff002", "employee", "facility_admin"),
    ("teacher002", "employee", "teacher"),
]

AWS_PROFILE = os.environ.get("AWS_PROFILE", "cs361-dev")
AWS_REGION = "us-east-1"
STACK_NAME = "cstu-room-booking-v5-dev"

# Unique marker for cleanup. Do not delete unrelated or seed bookings.
RUN_ID = uuid4().hex[:10]
RUN_START_DATE = date.today() + timedelta(days=420 + int(RUN_ID[:4], 16) % 365)
_user_sequence = itertools.count()
_booking_sequence = itertools.count()


def read_jwt_signing_config():
    """Fetch the project's existing key once, never log or write it to disk."""
    source = Path("lambda/cstu-user-auth/lambda_function.py").read_text(encoding="utf-8")
    match = re.search(r'''(?m)^\s*KID\s*=\s*["']([^"']+)["']''', source)
    if not match:
        raise RuntimeError("JWT KID not found in lambda/cstu-user-auth/lambda_function.py")

    aws = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    resource = aws.client("cloudformation").describe_stack_resource(
        StackName=STACK_NAME,
        LogicalResourceId="JwtPrivateKeySecret",
    )
    secret_id = resource["StackResourceDetail"]["PhysicalResourceId"]
    secret = aws.client("secretsmanager").get_secret_value(SecretId=secret_id)
    raw = secret.get("SecretString")
    if raw is None:
        raw = secret["SecretBinary"].decode("utf-8")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        decoded = raw
    candidates = decoded.values() if isinstance(decoded, dict) else [decoded]
    key = next(
        (
            value.replace("\\n", "\n")
            for value in candidates
            if isinstance(value, str)
            and "-----BEGIN " in value.replace("\\n", "\n")
            and "PRIVATE KEY-----" in value.replace("\\n", "\n")
        ),
        None,
    )
    if key is None:
        raise RuntimeError("No PEM private key found in JwtPrivateKeySecret")
    return key, match.group(1)


# Works in the same environment as the previously tested CS361 Locust script.
# If AWS SSO has expired, run: aws sso login --profile cs361-dev
_SIGNING_KEY, _KID = read_jwt_signing_config()
print(f"[CS361] Locust run ID: {RUN_ID}")
print(f"[CS361] First booking date: {RUN_START_DATE.isoformat()}")
print("[CS361] JWT signing key and tokens will not be printed.")


def issue_test_session(identity):
    username, user_type, role = identity
    now = int(time.time())
    expiry = now + 900  # 15 minutes; refreshed before expiry.
    token = jwt.encode(
        {
            "sub": username,
            "username": username,
            "user_type": user_type,
            "role": role,
            "iat": now,
            "exp": expiry,
        },
        _SIGNING_KEY,
        algorithm="RS256",
        headers={"kid": _KID},
    )
    return token, expiry


def new_booking_payload():
    """Give each POST a distinct (room, date, timeslot) within this run."""
    sequence = next(_booking_sequence)
    room = BOOKABLE_ROOMS[sequence % len(BOOKABLE_ROOMS)]
    slot_index = sequence // len(BOOKABLE_ROOMS)
    slot_in_day = slot_index % 16  # 09:00-17:00, 30-minute slots
    day_offset = slot_index // 16
    booking_day = RUN_START_DATE + timedelta(days=day_offset)
    starts_at = datetime.combine(booking_day, datetime.min.time()) + timedelta(
        hours=9, minutes=30 * slot_in_day
    )
    ends_at = starts_at + timedelta(minutes=30)
    return {
        "roomNumber": room,
        "purpose": f"LOADTEST-CS361-RUN-{RUN_ID}-{sequence:06d}",
        "participants": 1,
        "date": booking_day.isoformat(),
        "startTime": starts_at.strftime("%H:%M"),
        "endTime": ends_at.strftime("%H:%M"),
        "note": "CS361 template-based Locust load test",
    }


class TeamUser(HttpUser):
    # Match the classwork template's think time.
    wait_time = between(1, 3)

    def on_start(self):
        self.identity = TEST_USERS[next(_user_sequence) % len(TEST_USERS)]
        self.token, self.expiry = issue_test_session(self.identity)

    def session_headers(self):
        if int(time.time()) >= self.expiry - 60:
            self.token, self.expiry = issue_test_session(self.identity)
        return {"Cookie": f"session_token={self.token}"}

    @task(4)  # 40%: listing
    def list_page(self):
        self.client.get(LIST_PATH, name="GET /rooms")

    @task(4)  # 40%: detail
    def detail_page(self):
        room_number = random.choice(DETAIL_IDS)
        self.client.get(
            DETAIL_PATH.format(id=room_number),
            name="GET /rooms/{room_number}",
        )

    @task(2)  # 20%: write
    def save(self):
        payload = new_booking_payload()
        with self.client.post(
            SAVE_PATH,
            json=payload,
            headers=self.session_headers(),
            name="POST /bookings",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:180]}")


class StepLoad(LoadTestShape):
    """The exact 10 -> 20 -> 40 -> 80 users / 12-minute teacher template."""

    # (end at second, target concurrent users)
    steps = [(120, 10), (240, 20), (360, 40), (720, 80)]
    spawn_rate = 5  # users per second, matching the template

    def tick(self):
        elapsed = self.get_run_time()
        for end, users in self.steps:
            if elapsed < end:
                return users, self.spawn_rate
        return None  # Automatically stops at 12 minutes (NOT on SLO breach).

