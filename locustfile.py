
import itertools
import json
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import boto3
import jwt
from locust import HttpUser, between, task

PROFILE = "cs361-dev"
REGION = "us-east-1"
STACK = "cstu-room-booking-v5-dev"

# Five existing test users
USERS = [
    ("employee001", "employee", "employee"),
    ("master001", "student", "student"),
    ("doctoral001", "student", "student"),
    ("staff002", "employee", "facility_admin"),
    ("teacher002", "employee", "teacher"),
]

# Room type 3: allowed for all five users
ROOMS = [
    "214", "215", "301", "302", "303",
    "304", "305", "314", "315", "316",
]

RUN_ID = uuid4().hex[:10]
RUN_START_DATE = date.today() + timedelta(
    days=45 + int(RUN_ID[:4], 16) % 90
)

user_counter = itertools.count()
booking_counter = itertools.count()


def load_signing_credentials():
    source = Path(
        "lambda/cstu-user-auth/lambda_function.py"
    ).read_text(encoding="utf-8")

    match = re.search(
        r"""(?m)^\s*KID\s*=\s*["']([^"']+)["']""",
        source,
    )
    if not match:
        raise RuntimeError("Cannot find JWT KID")

    aws = boto3.Session(
        profile_name=PROFILE,
        region_name=REGION,
    )

    resource = aws.client(
        "cloudformation"
    ).describe_stack_resource(
        StackName=STACK,
        LogicalResourceId="JwtPrivateKeySecret",
    )

    secret_id = resource[
        "StackResourceDetail"
    ]["PhysicalResourceId"]

    secret = aws.client(
        "secretsmanager"
    ).get_secret_value(SecretId=secret_id)

    raw = secret.get("SecretString")
    if raw is None:
        raw = secret["SecretBinary"].decode("utf-8")

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        decoded = raw

    candidates = (
        decoded.values()
        if isinstance(decoded, dict)
        else [decoded]
    )

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

    if not key:
        raise RuntimeError("JWT private key not found")

    return key, match.group(1)


PRIVATE_KEY, KID = load_signing_credentials()

print("CS361 Load Test Run:", RUN_ID)
print("Test Booking Start Date:", RUN_START_DATE)
print("Private key and tokens will not be printed.")


def issue_token(identity):
    username, user_type, role = identity

    now = int(time.time())
    expires_at = now + 900

    token = jwt.encode(
        {
            "sub": username,
            "username": username,
            "user_type": user_type,
            "role": role,
            "iat": now,
            "exp": expires_at,
        },
        PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": KID},
    )

    return token, expires_at


def next_booking_payload():
    number = next(booking_counter)

    room_number = ROOMS[number % len(ROOMS)]
    slot_index = number // len(ROOMS)

    # 16 non-overlapping 30-minute slots per day
    slot = slot_index % 16
    day_offset = slot_index // 16

    booking_date = RUN_START_DATE + timedelta(
        days=day_offset
    )

    starts_at = datetime.combine(
        booking_date,
        datetime.min.time(),
    ) + timedelta(
        hours=9,
        minutes=slot * 30,
    )

    ends_at = starts_at + timedelta(minutes=30)

    return {
        "roomNumber": room_number,
        "purpose": (
            f"LOADTEST-CS361-RUN-{RUN_ID}-{number:06d}"
        ),
        "participants": 1,
        "date": booking_date.isoformat(),
        "startTime": starts_at.strftime("%H:%M"),
        "endTime": ends_at.strftime("%H:%M"),
        "note": "CS361 Locust load test",
    }


class RoomBookingUser(HttpUser):
    wait_time = between(2, 4)

    def on_start(self):
        index = next(user_counter) % len(USERS)
        self.identity = USERS[index]
        self.token, self.expires_at = issue_token(
            self.identity
        )

    def get_cookie_header(self):
        if int(time.time()) >= self.expires_at - 60:
            self.token, self.expires_at = issue_token(
                self.identity
            )

        return {"Cookie": f"session_token={self.token}"}

    @task(5)
    def list_rooms(self):
        self.client.get(
            "/rooms",
            name="GET /rooms",
        )

    @task(3)
    def room_detail(self):
        self.client.get(
            "/rooms/107",
            name="GET /rooms/{room_number}",
        )

    @task(2)
    def create_booking(self):
        payload = next_booking_payload()

        with self.client.post(
            "/bookings",
            json=payload,
            headers=self.get_cookie_header(),
            name="POST /bookings",
            catch_response=True,
        ) as result:

            if result.status_code == 201:
                result.success()
            else:
                result.failure(
                    f"HTTP {result.status_code}: "
                    f"{result.text[:150]}"
                )
