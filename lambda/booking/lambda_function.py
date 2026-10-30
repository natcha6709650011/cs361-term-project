"""Authenticated Booking API for V3.

API Gateway routes expected for this Lambda:
  GET    /bookings/me
  POST   /bookings
  PATCH  /bookings/{booking_id}
  DELETE /bookings/{booking_id}

Attach `cstu-jwt-authorizer` to every route.  The authorizer must put the
authenticated username in requestContext.authorizer.lambda.username.  Never
accept a user id or username from the browser request body.

V3 Fixed Facility Schedule: a booking request is rejected (409) when it overlaps
a locked facility schedule of the same room (weekly rules from
`facility_schedule_rules` minus per-date RELEASE exceptions, or a one-off row in
`facility_schedules`).  The check runs in the same transaction as the INSERT/UPDATE
and after the room row is locked FOR UPDATE, the same lock the Approval/Facility
Lambda takes, so a request and a new fixed schedule cannot slip past each other.
"""

import base64
import json
import os
from datetime import datetime, time, timedelta

import pymysql


ACTIVE_STATUSES = ("pending", "approved")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def connect_database():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        port=int(os.environ.get("DB_PORT", 3306)),
        charset="utf8mb4",
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def get_method(event):
    return (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or ""
    ).upper()


def get_path(event):
    return event.get("rawPath") or event.get("path") or ""


def get_authenticated_username(event):
    """Read identity written by either HTTP API or REST API Lambda authorizer."""
    authorizer = event.get("requestContext", {}).get("authorizer") or {}
    context = authorizer.get("lambda") or authorizer
    username = context.get("username")
    return str(username).strip() if username else None


def parse_json_body(event):
    body = event.get("body")
    if body in (None, ""):
        return {}

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    if isinstance(body, dict):
        return body

    try:
        value = json.loads(body)
    except (TypeError, ValueError) as error:
        raise ValueError("Request body must be valid JSON") from error

    if not isinstance(value, dict):
        raise ValueError("Request body must be a JSON object")

    return value


def get_current_user(connection, username):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, username, user_type, education_level
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        )
        return cursor.fetchone()


def policy_user_type(user):
    if user["user_type"] == "employee":
        return "employee"
    return user.get("education_level") or "student"


def require_room_permission(cursor, room_type_id, user):
    cursor.execute(
        """
        SELECT is_allowed
        FROM room_policies
        WHERE room_type_id = %s AND user_type = %s
        LIMIT 1
        """,
        (room_type_id, policy_user_type(user)),
    )
    policy = cursor.fetchone()
    return bool(policy and policy["is_allowed"])


def parse_booking_values(payload, *, partial=False):
    errors = {}

    purpose = payload.get("purpose")
    note = payload.get("note")
    participants = payload.get("participants")
    date_value = payload.get("date")
    start_time = payload.get("startTime")
    end_time = payload.get("endTime")

    required = {
        "purpose": purpose,
        "participants": participants,
        "date": date_value,
        "startTime": start_time,
        "endTime": end_time,
    }
    if not partial:
        for key, value in required.items():
            if value in (None, ""):
                errors[key] = "กรุณาระบุข้อมูล"

    if purpose is not None:
        purpose = str(purpose).strip()
        if not purpose:
            errors["purpose"] = "กรุณาระบุวัตถุประสงค์"
        elif len(purpose) > 150:
            errors["purpose"] = "วัตถุประสงค์ยาวได้ไม่เกิน 150 ตัวอักษร"

    if note is not None:
        note = str(note).strip()
        if len(note) > 500:
            errors["note"] = "หมายเหตุยาวได้ไม่เกิน 500 ตัวอักษร"

    participant_count = None
    if participants is not None:
        try:
            participant_count = int(participants)
            if participant_count < 1:
                raise ValueError
        except (TypeError, ValueError):
            errors["participants"] = "จำนวนผู้เข้าร่วมต้องเป็นจำนวนเต็มอย่างน้อย 1 คน"

    starts_at = ends_at = None
    if date_value is not None or start_time is not None or end_time is not None:
        try:
            starts_at = datetime.strptime(
                f"{date_value} {start_time}", DATETIME_FORMAT
            )
            ends_at = datetime.strptime(
                f"{date_value} {end_time}", DATETIME_FORMAT
            )
            if starts_at >= ends_at:
                errors["endTime"] = "เวลาสิ้นสุดต้องอยู่หลังเวลาเริ่มต้น"
        except (TypeError, ValueError):
            errors["date"] = "วันที่และเวลาต้องอยู่ในรูปแบบ YYYY-MM-DD และ HH:MM"

    if errors:
        return None, errors

    return {
        "purpose": purpose,
        "note": note,
        "participants": participant_count,
        "start_time": starts_at,
        "end_time": ends_at,
    }, None


def booking_to_json(row):
    return {
        "id": row["booking_id"],
        "room": f"บร.2-{row['room_number']}",
        "roomNumber": str(row["room_number"]),
        "roomType": row.get("room_type_name") or "ไม่ระบุ",
        "date": row["start_time"].strftime("%Y-%m-%d"),
        "startTime": row["start_time"].strftime("%H:%M"),
        "endTime": row["end_time"].strftime("%H:%M"),
        "purpose": row["title"],
        "note": row.get("request_note") or "",
        "participants": row.get("participant_count"),
        "status": row["status"].upper(),
    }


def get_owned_booking(cursor, booking_id, user_id, *, for_update=False):
    lock = " FOR UPDATE" if for_update else ""
    cursor.execute(
        f"""
        SELECT b.booking_id, b.room_id, b.user_id, b.title, b.request_note, b.participant_count,
               b.start_time, b.end_time, b.status, r.room_number, r.capacity,
               r.room_type_id, rt.type_name AS room_type_name
        FROM bookings b
        INNER JOIN rooms r ON r.room_id = b.room_id
        INNER JOIN room_types rt ON rt.room_type_id = r.room_type_id
        WHERE b.booking_id = %s AND b.user_id = %s{lock}
        """,
        (booking_id, user_id),
    )
    return cursor.fetchone()


def has_conflict(cursor, room_id, starts_at, ends_at, *, exclude_booking_id=None):
    """True if another pending/approved booking overlaps (half-open intervals)."""
    sql = """
        SELECT booking_id
        FROM bookings
        WHERE room_id = %s
          AND status IN ('pending', 'approved')
          AND start_time < %s
          AND end_time > %s
    """
    values = [room_id, ends_at, starts_at]
    if exclude_booking_id is not None:
        sql += " AND booking_id <> %s"
        values.append(exclude_booking_id)
    sql += " LIMIT 1 FOR UPDATE"
    cursor.execute(sql, values)
    return cursor.fetchone() is not None


def to_time(value):
    """pymysql returns TIME columns as timedelta; normalize to datetime.time."""
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds()) % 86400
        return time(seconds // 3600, seconds % 3600 // 60, seconds % 60)
    text = str(value)
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    raise ValueError(f"Invalid TIME value: {value!r}")


def find_fixed_schedule_conflict(cursor, room_id, starts_at, ends_at):
    """Return the first locked Fixed Facility Schedule overlapping the request.

    Returns a dict {"title", "date"} or None.  Two sources are checked:
      1) facility_schedules       - one-off locked datetime ranges
      2) facility_schedule_rules  - weekly rules for a term, except dates where
                                    the newest exception is RELEASE
    """
    cursor.execute(
        """
        SELECT title, start_time
        FROM facility_schedules
        WHERE room_id = %s
          AND status = 'APPROVED'
          AND is_locked = TRUE
          AND start_time < %s
          AND end_time > %s
        LIMIT 1
        FOR UPDATE
        """,
        (room_id, ends_at, starts_at),
    )
    one_off = cursor.fetchone()
    if one_off:
        return {"title": one_off["title"], "date": one_off["start_time"].strftime("%Y-%m-%d")}

    cursor.execute(
        """
        SELECT schedule_id, title, weekday, start_time, end_time,
               valid_from, valid_until
        FROM facility_schedule_rules
        WHERE room_id = %s
          AND status = 'ACTIVE'
          AND valid_from <= %s
          AND valid_until >= %s
        FOR UPDATE
        """,
        (room_id, ends_at.date(), starts_at.date()),
    )
    for rule in cursor.fetchall():
        day = max(starts_at.date(), rule["valid_from"])
        last_day = min(ends_at.date(), rule["valid_until"])
        while day <= last_day:
            if day.weekday() == int(rule["weekday"]):
                occurrence_start = datetime.combine(day, to_time(rule["start_time"]))
                occurrence_end = datetime.combine(day, to_time(rule["end_time"]))
                if occurrence_start < ends_at and occurrence_end > starts_at:
                    if not is_released_on(cursor, rule["schedule_id"], day):
                        return {"title": rule["title"], "date": day.strftime("%Y-%m-%d")}
            day += timedelta(days=1)
    return None


def is_released_on(cursor, schedule_id, day):
    """The newest exception for that schedule/date decides (RELEASE opens it)."""
    cursor.execute(
        """
        SELECT action
        FROM facility_schedule_exceptions
        WHERE schedule_id = %s AND exception_date = %s
        ORDER BY exception_id DESC
        LIMIT 1
        """,
        (schedule_id, day),
    )
    latest = cursor.fetchone()
    return bool(latest and latest["action"] == "RELEASE")


def fixed_schedule_conflict_response(conflict):
    return response(
        409,
        {
            "error": "Fixed schedule conflict",
            "message": f"ห้องนี้ถูกจัดไว้สำหรับ \"{conflict['title']}\" ในวันที่ {conflict['date']} ไม่สามารถจองทับได้",
        },
    )


def get_booking(cursor, booking_id, user_id):
    cursor.execute(
        """
        SELECT b.booking_id, b.title, b.request_note, b.participant_count, b.start_time, b.end_time,
               b.status, r.room_number, rt.type_name AS room_type_name
        FROM bookings b
        INNER JOIN rooms r ON r.room_id = b.room_id
        INNER JOIN room_types rt ON rt.room_type_id = r.room_type_id
        WHERE b.booking_id = %s AND b.user_id = %s
        """,
        (booking_id, user_id),
    )
    return cursor.fetchone()


def list_my_bookings(connection, user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT b.booking_id, b.title, b.request_note, b.participant_count, b.start_time,
                   b.end_time, b.status, r.room_number, rt.type_name AS room_type_name
            FROM bookings b
            INNER JOIN rooms r ON r.room_id = b.room_id
            INNER JOIN room_types rt ON rt.room_type_id = r.room_type_id
            WHERE b.user_id = %s
            ORDER BY b.booking_id DESC
            """,
            (user_id,),
        )
        return [booking_to_json(row) for row in cursor.fetchall()]


def create_booking(connection, user, payload):
    values, errors = parse_booking_values(payload)
    if errors:
        return response(400, {"error": "Invalid input", "details": errors})

    room_number = str(payload.get("roomNumber") or "").strip()
    if not room_number:
        return response(400, {"error": "Invalid input", "details": {"roomNumber": "กรุณาระบุห้อง"}})

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT room_id, room_number, room_type_id, capacity
                FROM rooms
                WHERE room_number = %s
                  AND is_active = TRUE
                  AND is_bookable = TRUE
                  AND is_permanent_locked = FALSE
                LIMIT 1
                FOR UPDATE
                """,
                (room_number,),
            )
            room = cursor.fetchone()
            if not room:
                connection.rollback()
                return response(404, {"error": "Room not found", "message": "ไม่พบห้องที่พร้อมจอง"})

            if not require_room_permission(cursor, room["room_type_id"], user):
                connection.rollback()
                return response(403, {"error": "Forbidden", "message": "คุณไม่มีสิทธิ์จองห้องประเภทนี้"})

            if room["capacity"] is not None and values["participants"] > room["capacity"]:
                connection.rollback()
                return response(400, {"error": "Capacity exceeded", "message": "จำนวนผู้เข้าร่วมเกินความจุห้อง"})

            if has_conflict(cursor, room["room_id"], values["start_time"], values["end_time"]):
                connection.rollback()
                return response(409, {"error": "Booking conflict", "message": "ช่วงเวลานี้ไม่ว่าง"})

            fixed = find_fixed_schedule_conflict(
                cursor, room["room_id"], values["start_time"], values["end_time"]
            )
            if fixed:
                connection.rollback()
                return fixed_schedule_conflict_response(fixed)

            cursor.execute(
                """
                INSERT INTO bookings
                    (room_id, user_id, title, request_note, participant_count, start_time, end_time, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                """,
                (
                    room["room_id"], user["user_id"], values["purpose"], values["note"],
                    values["participants"], values["start_time"], values["end_time"],
                ),
            )
            booking_id = cursor.lastrowid
            booking = get_booking(cursor, booking_id, user["user_id"])
        connection.commit()
        return response(201, {"booking": booking_to_json(booking)})
    except Exception:
        connection.rollback()
        raise


def update_booking(connection, user, booking_id, payload):
    try:
        with connection.cursor() as cursor:
            booking = get_owned_booking(cursor, booking_id, user["user_id"], for_update=True)
            if not booking:
                connection.rollback()
                return response(404, {"error": "Booking not found", "message": "ไม่พบรายการจองของคุณ"})
            if booking["status"] == "cancelled":
                connection.rollback()
                return response(409, {"error": "Booking cancelled", "message": "ไม่สามารถแก้ไขรายการที่ยกเลิกแล้ว"})
            if booking["status"] == "rejected":
                connection.rollback()
                return response(409, {"error": "Booking rejected", "message": "ไม่สามารถแก้ไขรายการที่ถูกปฏิเสธ กรุณาส่งคำขอใหม่"})

            # Lock the room row first (same order as create_booking and the
            # Approval/Facility Lambda) before checking conflicts.
            cursor.execute("SELECT room_id FROM rooms WHERE room_id = %s FOR UPDATE", (booking["room_id"],))

            merged = {
                "purpose": payload.get("purpose", booking["title"]),
                "note": payload.get("note", booking.get("request_note") or ""),
                "participants": payload.get("participants", booking["participant_count"]),
                "date": payload.get("date", booking["start_time"].strftime("%Y-%m-%d")),
                "startTime": payload.get("startTime", booking["start_time"].strftime("%H:%M")),
                "endTime": payload.get("endTime", booking["end_time"].strftime("%H:%M")),
            }
            values, errors = parse_booking_values(merged)
            if errors:
                connection.rollback()
                return response(400, {"error": "Invalid input", "details": errors})

            if booking["capacity"] is not None and values["participants"] > booking["capacity"]:
                connection.rollback()
                return response(400, {"error": "Capacity exceeded", "message": "จำนวนผู้เข้าร่วมเกินความจุห้อง"})
            if has_conflict(cursor, booking["room_id"], values["start_time"], values["end_time"], exclude_booking_id=booking_id):
                connection.rollback()
                return response(409, {"error": "Booking conflict", "message": "ช่วงเวลานี้ไม่ว่าง"})

            fixed = find_fixed_schedule_conflict(
                cursor, booking["room_id"], values["start_time"], values["end_time"]
            )
            if fixed:
                connection.rollback()
                return fixed_schedule_conflict_response(fixed)

            # An approved booking whose time changes must be approved again;
            # otherwise a user could move an approved booking without review.
            time_changed = (
                values["start_time"] != booking["start_time"]
                or values["end_time"] != booking["end_time"]
            )
            new_status = "pending" if booking["status"] == "approved" and time_changed else booking["status"]

            cursor.execute(
                """
                UPDATE bookings
                SET title = %s, request_note = %s, participant_count = %s, start_time = %s, end_time = %s,
                    status = %s
                WHERE booking_id = %s AND user_id = %s
                """,
                (values["purpose"], values["note"], values["participants"], values["start_time"], values["end_time"], new_status, booking_id, user["user_id"]),
            )
            updated = get_booking(cursor, booking_id, user["user_id"])
        connection.commit()
        return response(200, {"booking": booking_to_json(updated)})
    except Exception:
        connection.rollback()
        raise


def cancel_booking(connection, user, booking_id):
    try:
        with connection.cursor() as cursor:
            booking = get_owned_booking(cursor, booking_id, user["user_id"], for_update=True)
            if not booking:
                connection.rollback()
                return response(404, {"error": "Booking not found", "message": "ไม่พบรายการจองของคุณ"})
            if booking["status"] == "cancelled":
                connection.rollback()
                return response(409, {"error": "Booking cancelled", "message": "รายการนี้ถูกยกเลิกแล้ว"})

            cursor.execute(
                """
                UPDATE bookings
                SET status = 'cancelled'
                WHERE booking_id = %s AND user_id = %s
                """,
                (booking_id, user["user_id"]),
            )
            cancelled = get_booking(cursor, booking_id, user["user_id"])
        connection.commit()
        return response(200, {"booking": booking_to_json(cancelled)})
    except Exception:
        connection.rollback()
        raise


def get_booking_id(event):
    value = (event.get("pathParameters") or {}).get("booking_id")
    try:
        booking_id = int(value)
        if booking_id < 1:
            raise ValueError
        return booking_id
    except (TypeError, ValueError):
        return None


def lambda_handler(event, context):
    event = event or {}
    method = get_method(event)
    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    username = get_authenticated_username(event)
    if not username:
        return response(401, {"error": "Unauthorized", "message": "กรุณาเข้าสู่ระบบใหม่"})

    connection = None
    try:
        connection = connect_database()
        user = get_current_user(connection, username)
        if not user:
            return response(401, {"error": "Unauthorized", "message": "ไม่พบผู้ใช้ในระบบ"})

        path = get_path(event).rstrip("/")
        if method == "GET" and path.endswith("/bookings/me"):
            return response(200, {"bookings": list_my_bookings(connection, user["user_id"])})
        if method == "POST" and path.endswith("/bookings"):
            return create_booking(connection, user, parse_json_body(event))

        booking_id = get_booking_id(event)
        if booking_id is None:
            return response(404, {"error": "Not found", "message": "ไม่พบเส้นทาง API"})
        if method == "PATCH":
            return update_booking(connection, user, booking_id, parse_json_body(event))
        if method == "DELETE":
            return cancel_booking(connection, user, booking_id)
        return response(405, {"error": "Method not allowed"})

    except ValueError as error:
        return response(400, {"error": "Invalid input", "message": str(error)})
    except KeyError as error:
        print("Missing environment variable:", repr(error))
        return response(500, {"error": "Configuration error", "message": "Lambda environment variables ไม่ครบ"})
    except Exception as error:
        print("Booking Lambda error:", repr(error))
        return response(500, {"error": "Internal server error", "message": "เกิดข้อผิดพลาดภายในระบบ"})
    finally:
        if connection:
            connection.close()
