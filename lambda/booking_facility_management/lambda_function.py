"""CS361 V3 Approval + Facility Schedule API.

Deploy as one Lambda behind API Gateway HTTP API (Lambda proxy integration).
Required env: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME (usually cstu_room_db), DB_PORT optional.
Auth: API Gateway validates the team's own RS256 JWT with the Lambda authorizer
(lambda/cstu-jwt-authorizer). That authorizer passes `username` and `role` in its
context, which arrives at requestContext.authorizer.lambda (HTTP API) and is mapped
to users.username here. Permissions come from user_roles, not from the JWT `role`.

CONFIGURATION TO REVIEW:
- USERNAME_CLAIM: key in the authorizer context used to match users.username
  (default: username, as issued by cstu-jwt-authorizer).
- Routes are matched without the optional /v1 prefix, so both /approvals/pending
  and /v1/approvals/pending reach the same handler.
"""
import json
import os
import re
from datetime import datetime, date, time, timedelta
from decimal import Decimal

import pymysql

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")  # TODO: set to your deployed frontend origin in production.
USERNAME_CLAIM = os.getenv("USERNAME_CLAIM", "username")
DB_NAME = os.getenv("DB_NAME", "cstu_room_db")


def to_time(value):
    """Normalize a MySQL TIME value. pymysql returns TIME as timedelta, so
    str() gives '9:00:00' for morning times, which time.fromisoformat() rejects."""
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


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, timedelta):
        return to_time(value).isoformat()
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Cannot JSON encode {type(value).__name__}")


def response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": CORS_ORIGIN,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False, default=_json_default),
    }


def get_method_path(event):
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("path") or event.get("rawPath") or "/"
    # Accept both /approvals/pending and /v1/approvals/pending (API stage prefix).
    path = re.sub(r"^(/v1)+(?=/|$)", "", path)
    return method.upper(), path.rstrip("/") or "/"


def get_claims(event):
    # cstu-jwt-authorizer (HTTP API Lambda authorizer, simple response) puts its
    # context in requestContext.authorizer.lambda. A flat authorizer dict is also
    # accepted for payload format 1.0.
    rc = event.get("requestContext") or {}
    auth = rc.get("authorizer") or {}
    lambda_context = auth.get("lambda")
    if isinstance(lambda_context, dict) and lambda_context:
        return lambda_context
    if auth.get("username"):
        return auth
    return {}


def parse_user_id(claims):
    # Identity comes only from the verified authorizer context, never from the
    # request body or browser storage. users.username is the link to the login.
    username = claims.get(USERNAME_CLAIM)
    if not username:
        raise ApiError(401, "ไม่พบ username จาก Authorizer กรุณาตรวจ USERNAME_CLAIM")
    return {"username": str(username)}


class ApiError(Exception):
    def __init__(self, status_code, message, details=None):
        self.status_code = status_code
        self.message = message
        self.details = details


def connect_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], database=DB_NAME,
        port=int(os.getenv("DB_PORT", "3306")), charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=False,
        connect_timeout=5, read_timeout=10, write_timeout=10,
    )


def body_json(event):
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        raise ApiError(400, "ไม่รองรับ Base64 body ใน endpoint นี้")
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        raise ApiError(400, "Request body ต้องเป็น JSON ที่ถูกต้อง")
    if not isinstance(value, dict):
        raise ApiError(400, "Request body ต้องเป็น JSON object")
    return value


def require_fields(data, fields):
    missing = [f for f in fields if data.get(f) is None or data.get(f) == ""]
    if missing:
        raise ApiError(400, "ข้อมูลไม่ครบ", {"missing": missing})


def parse_datetime(value, field):
    if not isinstance(value, str):
        raise ApiError(400, f"{field} ต้องอยู่ในรูปแบบ YYYY-MM-DD HH:MM:SS")
    try:
        result = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ApiError(400, f"{field} ต้องอยู่ในรูปแบบ YYYY-MM-DD HH:MM:SS")
    return result


def resolve_user_id(cursor, claims):
    identity = parse_user_id(claims)
    cursor.execute("SELECT user_id FROM users WHERE username=%s", (identity["username"],))
    row = cursor.fetchone()
    if not row:
        raise ApiError(401, "ไม่พบผู้ใช้ในฐานข้อมูล กรุณาตรวจการเชื่อมบัญชี Login กับ users.username")
    return int(row["user_id"])


def require_role(cursor, user_id, role):
    cursor.execute("""
        SELECT 1
        FROM user_roles ur JOIN roles r ON r.role_id=ur.role_id
        WHERE ur.user_id=%s AND r.role_name=%s
        LIMIT 1
    """, (user_id, role))
    if not cursor.fetchone():
        raise ApiError(403, f"ต้องมี Role {role} จึงทำรายการนี้ได้")


def connected_room_ids(cursor, room_id):
    """Return the transitive group of rooms connected by active room_connections pairs."""
    seen = {int(room_id)}
    frontier = [int(room_id)]
    while frontier:
        current = frontier.pop()
        cursor.execute("""SELECT room_id_1, room_id_2 FROM room_connections
                          WHERE is_active=TRUE AND (room_id_1=%s OR room_id_2=%s)""",
                       (current, current))
        for row in cursor.fetchall():
            other = int(row["room_id_2"] if int(row["room_id_1"]) == current else row["room_id_1"])
            if other not in seen:
                seen.add(other)
                frontier.append(other)
    return sorted(seen)


def lock_rooms(cursor, room_id):
    """Lock all connected room rows in ascending order; validate the requested room only."""
    ids = connected_room_ids(cursor, room_id)
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(f"SELECT room_id, is_active, is_bookable FROM rooms WHERE room_id IN ({placeholders}) ORDER BY room_id FOR UPDATE", ids)
    rooms = {int(row["room_id"]): row for row in cursor.fetchall()}
    if int(room_id) not in rooms:
        raise ApiError(404, "ไม่พบห้องที่ระบุ")
    room = rooms[int(room_id)]
    if not room["is_active"] or not room["is_bookable"]:
        raise ApiError(409, "ห้องนี้ปิดใช้งานหรือไม่เปิดให้จอง")
    return ids


def _parse_date(value, field):
    if not isinstance(value, str):
        raise ApiError(400, f"{field} ต้องเป็น YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ApiError(400, f"{field} ต้องเป็น YYYY-MM-DD")


def _parse_time(value, field):
    if not isinstance(value, str):
        raise ApiError(400, f"{field} ต้องเป็น HH:MM หรือ HH:MM:SS")
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            pass
    raise ApiError(400, f"{field} ต้องเป็น HH:MM หรือ HH:MM:SS")


def _latest_exception_actions(cursor, schedule_ids, day):
    if not schedule_ids:
        return {}
    marks = ",".join(["%s"] * len(schedule_ids))
    cursor.execute(f"""SELECT e.schedule_id, e.action
        FROM facility_schedule_exceptions e
        JOIN (SELECT schedule_id, MAX(exception_id) AS latest_id
              FROM facility_schedule_exceptions
              WHERE schedule_id IN ({marks}) AND exception_date=%s
              GROUP BY schedule_id) x ON x.latest_id=e.exception_id""",
        list(schedule_ids) + [day])
    return {int(r["schedule_id"]): r["action"] for r in cursor.fetchall()}


def _rule_occurrence(cursor, rule, day):
    """Return occurrence datetime range for a date, or None if rule does not apply."""
    if day < rule["valid_from"] or day > rule["valid_until"] or day.weekday() != int(rule["weekday"]):
        return None
    actions = _latest_exception_actions(cursor, [int(rule["schedule_id"])], day)
    if actions.get(int(rule["schedule_id"])) == "RELEASE":
        return None
    start_t = to_time(rule["start_time"])
    end_t = to_time(rule["end_time"])
    return datetime.combine(day, start_t), datetime.combine(day, end_t)


def assert_no_recurring_rule_conflict(cursor, room_ids, start_time, end_time, exclude_rule_id=None):
    if not room_ids:
        return
    marks = ",".join(["%s"] * len(room_ids))
    cursor.execute(f"""SELECT schedule_id, room_id, title, weekday, start_time, end_time,
                              valid_from, valid_until, status
                       FROM facility_schedule_rules
                       WHERE room_id IN ({marks}) AND status='ACTIVE'
                         AND valid_from <= %s AND valid_until >= %s
                       FOR UPDATE""", list(room_ids) + [end_time.date(), start_time.date()])
    rules = cursor.fetchall()
    for rule in rules:
        if exclude_rule_id is not None and int(rule["schedule_id"]) == int(exclude_rule_id):
            continue
        day = max(start_time.date(), rule["valid_from"])
        last_day = min(end_time.date(), rule["valid_until"])
        while day <= last_day:
            occurrence = _rule_occurrence(cursor, rule, day)
            if occurrence:
                occ_start, occ_end = occurrence
                if occ_start < end_time and occ_end > start_time:
                    raise ApiError(409, "ช่วงเวลานี้ชนกับ Fixed Facility Schedule รายสัปดาห์ที่ยังมีผล",
                                   {"schedule_id": int(rule["schedule_id"]), "date": day.isoformat(), "title": rule["title"]})
            day += timedelta(days=1)


def assert_no_conflict(cursor, room_id, start_time, end_time, exclude_booking_id=None, exclude_schedule_id=None):
    """Check the requested room and every room linked through active room_connections.
    Must be called in a transaction after lock_rooms(). Uses half-open time intervals.
    """
    room_ids = connected_room_ids(cursor, room_id)
    placeholders = ",".join(["%s"] * len(room_ids))
    sql = f"""SELECT booking_id FROM bookings
             WHERE room_id IN ({placeholders}) AND status IN ('pending','approved')
               AND start_time < %s AND end_time > %s"""
    args = list(room_ids) + [end_time, start_time]
    if exclude_booking_id is not None:
        sql += " AND booking_id <> %s"
        args.append(exclude_booking_id)
    sql += " LIMIT 1 FOR UPDATE"
    cursor.execute(sql, args)
    if cursor.fetchone():
        raise ApiError(409, "ช่วงเวลานี้ชนกับคำขอจองหรือรายการจองที่ยังมีผลในห้องที่เชื่อมต่อกัน")

    sql = f"""SELECT schedule_id FROM facility_schedules
             WHERE room_id IN ({placeholders}) AND status='APPROVED' AND is_locked=TRUE
               AND start_time < %s AND end_time > %s"""
    args = list(room_ids) + [end_time, start_time]
    if exclude_schedule_id is not None:
        sql += " AND schedule_id <> %s"
        args.append(exclude_schedule_id)
    sql += " LIMIT 1 FOR UPDATE"
    cursor.execute(sql, args)
    if cursor.fetchone():
        raise ApiError(409, "ช่วงเวลานี้ชนกับ Fixed Facility Schedule ที่ล็อกอยู่ในห้องที่เชื่อมต่อกัน")

    assert_no_recurring_rule_conflict(cursor, room_ids, start_time, end_time)


def pending_approvals(cursor):
    cursor.execute("""
        SELECT b.booking_id, b.room_id, r.room_number, b.user_id,
               b.title, b.request_note, b.start_time, b.end_time, b.status, b.booking_source, b.created_at
        FROM bookings b JOIN rooms r ON r.room_id=b.room_id
        WHERE b.status='pending' AND b.booking_source='USER_REQUEST' AND b.user_id IS NOT NULL
        ORDER BY b.created_at ASC, b.booking_id ASC
    """)
    return cursor.fetchall()


def approve_decision(connection, cursor, booking_id, actor_id, data):
    require_fields(data, ["action"])
    action = str(data["action"]).upper()
    if action not in ("APPROVED", "REJECTED"):
        raise ApiError(400, "action ต้องเป็น APPROVED หรือ REJECTED")
    reason = data.get("reason")
    if action == "REJECTED" and (not isinstance(reason, str) or not reason.strip()):
        raise ApiError(400, "กรุณาระบุ reason เมื่อปฏิเสธคำขอ")
    if reason is not None and (not isinstance(reason, str) or len(reason) > 500):
        raise ApiError(400, "reason ต้องเป็นข้อความไม่เกิน 500 ตัวอักษร")

    cursor.execute("SELECT * FROM bookings WHERE booking_id=%s", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        raise ApiError(404, "ไม่พบคำขอจอง")
    if booking["booking_source"] != "USER_REQUEST":
        raise ApiError(409, "รายการนี้ไม่ใช่คำขอจองทั่วไป")
    if booking["user_id"] is None:
        raise ApiError(409, "รายการจองเก่านี้ไม่มีผู้ส่งคำขอที่ระบุได้ จึงไม่สามารถอนุมัติผ่าน V3 ได้")
    if booking["status"] != "pending":
        raise ApiError(409, f"ดำเนินการไม่ได้ เพราะสถานะปัจจุบันคือ {booking['status']}")

    if action == "APPROVED":
        lock_rooms(cursor, int(booking["room_id"]))
        # Re-read under lock after locking rooms to guard against a concurrent decision.
        cursor.execute("SELECT * FROM bookings WHERE booking_id=%s FOR UPDATE", (booking_id,))
        booking = cursor.fetchone()
        if not booking or booking["status"] != "pending":
            raise ApiError(409, "สถานะคำขอเปลี่ยนไปแล้ว กรุณาโหลดข้อมูลใหม่")
        assert_no_conflict(cursor, int(booking["room_id"]), booking["start_time"], booking["end_time"], exclude_booking_id=booking_id)
    else:
        cursor.execute("SELECT * FROM bookings WHERE booking_id=%s FOR UPDATE", (booking_id,))
        booking = cursor.fetchone()
        if not booking or booking["status"] != "pending":
            raise ApiError(409, "สถานะคำขอเปลี่ยนไปแล้ว กรุณาโหลดข้อมูลใหม่")

    new_status = "approved" if action == "APPROVED" else "rejected"
    cursor.execute("UPDATE bookings SET status=%s WHERE booking_id=%s AND status='pending'", (new_status, booking_id))
    if cursor.rowcount != 1:
        raise ApiError(409, "สถานะคำขอเปลี่ยนไปแล้ว กรุณาโหลดข้อมูลใหม่")
    cursor.execute("""INSERT INTO booking_approvals (booking_id, approver_id, action, reason)
                      VALUES (%s,%s,%s,%s)""", (booking_id, actor_id, action, reason.strip() if isinstance(reason, str) else None))
    return {"booking_id": booking_id, "status": new_status, "action": action, "message": "บันทึกผลการพิจารณาเรียบร้อยแล้ว"}


def list_schedules(cursor, query):
    clauses = ["fs.status='APPROVED'"]
    args = []
    if query.get("date"):
        try:
            datetime.strptime(query["date"], "%Y-%m-%d")
        except ValueError:
            raise ApiError(400, "date ต้องเป็น YYYY-MM-DD")
        next_day = (datetime.strptime(query["date"], "%Y-%m-%d").date()).toordinal() + 1
        from datetime import date as _date
        clauses.append("fs.start_time < %s AND fs.end_time > %s")
        args.extend([_date.fromordinal(next_day).strftime("%Y-%m-%d") + " 00:00:00", query["date"] + " 00:00:00"])
    if query.get("room_id"):
        if not str(query["room_id"]).isdigit():
            raise ApiError(400, "room_id ต้องเป็นจำนวนเต็ม")
        clauses.append("fs.room_id=%s")
        args.append(int(query["room_id"]))
    cursor.execute("""SELECT fs.schedule_id, fs.room_id, r.room_number, fs.title,
                              fs.start_time, fs.end_time, fs.status, fs.is_locked,
                              fs.created_by, fs.updated_by, fs.created_at, fs.updated_at
                       FROM facility_schedules fs JOIN rooms r ON r.room_id=fs.room_id
                       WHERE """ + " AND ".join(clauses) + " ORDER BY fs.start_time", args)
    return cursor.fetchall()


def create_schedule(cursor, actor_id, data):
    require_fields(data, ["room_id", "title", "start_time", "end_time"])
    if not str(data["room_id"]).isdigit():
        raise ApiError(400, "room_id ต้องเป็นจำนวนเต็ม")
    room_id = int(data["room_id"])
    title = str(data["title"]).strip()
    if not title or len(title) > 150:
        raise ApiError(400, "title ต้องมีความยาว 1-150 ตัวอักษร")
    start = parse_datetime(data["start_time"], "start_time")
    end = parse_datetime(data["end_time"], "end_time")
    if start >= end:
        raise ApiError(400, "end_time ต้องมากกว่า start_time")
    locked = data.get("is_locked", True)
    if not isinstance(locked, bool):
        raise ApiError(400, "is_locked ต้องเป็น true หรือ false")
    lock_rooms(cursor, room_id)
    assert_no_conflict(cursor, room_id, start, end)
    cursor.execute("""INSERT INTO facility_schedules
        (room_id,title,start_time,end_time,status,is_locked,created_by)
        VALUES (%s,%s,%s,%s,'APPROVED',%s,%s)""",
        (room_id, title, start, end, locked, actor_id))
    return {"schedule_id": cursor.lastrowid, "room_id": room_id, "title": title,
            "start_time": start, "end_time": end, "status": "APPROVED", "is_locked": locked}


def update_schedule(cursor, actor_id, schedule_id, data):
    cursor.execute("SELECT * FROM facility_schedules WHERE schedule_id=%s FOR UPDATE", (schedule_id,))
    old = cursor.fetchone()
    if not old:
        raise ApiError(404, "ไม่พบตารางประจำ")
    if old["status"] != "APPROVED":
        raise ApiError(409, "แก้ไขได้เฉพาะตารางที่ยังมีสถานะ APPROVED")

    room_id = int(data.get("room_id", old["room_id"]))
    title = str(data.get("title", old["title"])).strip()
    start = parse_datetime(data.get("start_time", old["start_time"].strftime("%Y-%m-%d %H:%M:%S")), "start_time")
    end = parse_datetime(data.get("end_time", old["end_time"].strftime("%Y-%m-%d %H:%M:%S")), "end_time")
    locked = data.get("is_locked", bool(old["is_locked"]))
    if not title or len(title) > 150:
        raise ApiError(400, "title ต้องมีความยาว 1-150 ตัวอักษร")
    if start >= end:
        raise ApiError(400, "end_time ต้องมากกว่า start_time")
    if not isinstance(locked, bool):
        raise ApiError(400, "is_locked ต้องเป็น true หรือ false")

    # To avoid two transactions locking the same pair in different orders, lock the smaller room_id first.
    room_ids = sorted({int(old["room_id"]), room_id})
    # Lock every connected room group in a deterministic order to reduce conflicting concurrent writes.
    all_lock_ids = set()
    for rid in room_ids:
        all_lock_ids.update(connected_room_ids(cursor, rid))
    placeholders = ",".join(["%s"] * len(all_lock_ids))
    cursor.execute(f"SELECT room_id FROM rooms WHERE room_id IN ({placeholders}) ORDER BY room_id FOR UPDATE", sorted(all_lock_ids))
    # Validate target room availability after lock; the old room may have been disabled since creation.
    cursor.execute("SELECT room_id,is_active,is_bookable FROM rooms WHERE room_id=%s", (room_id,))
    target_room = cursor.fetchone()
    if not target_room:
        raise ApiError(404, "ไม่พบห้องที่ระบุ")
    if not target_room["is_active"] or not target_room["is_bookable"]:
        raise ApiError(409, "ห้องนี้ปิดใช้งานหรือไม่เปิดให้จอง")
    # A schedule being unlocked still cannot be saved on top of an active booking.
    assert_no_conflict(cursor, room_id, start, end, exclude_schedule_id=schedule_id)
    cursor.execute("""UPDATE facility_schedules
        SET room_id=%s,title=%s,start_time=%s,end_time=%s,is_locked=%s,updated_by=%s
        WHERE schedule_id=%s AND status='APPROVED'""",
        (room_id, title, start, end, locked, actor_id, schedule_id))
    return {"schedule_id": schedule_id, "room_id": room_id, "title": title,
            "start_time": start, "end_time": end, "status": "APPROVED", "is_locked": locked}


def cancel_schedule(cursor, actor_id, schedule_id):
    cursor.execute("SELECT schedule_id,status FROM facility_schedules WHERE schedule_id=%s FOR UPDATE", (schedule_id,))
    row = cursor.fetchone()
    if not row:
        raise ApiError(404, "ไม่พบตารางประจำ")
    if row["status"] == "CANCELLED":
        raise ApiError(409, "ตารางนี้ถูกยกเลิกไปแล้ว")
    cursor.execute("UPDATE facility_schedules SET status='CANCELLED', is_locked=FALSE, updated_by=%s WHERE schedule_id=%s", (actor_id, schedule_id))
    return {"schedule_id": schedule_id, "status": "CANCELLED", "message": "ยกเลิกตารางประจำแล้ว"}


def list_recurring_rules(cursor, query):
    clauses = ["fs.status='ACTIVE'"]
    args = []
    if query.get("room_id"):
        if not str(query["room_id"]).isdigit():
            raise ApiError(400, "room_id ต้องเป็นจำนวนเต็ม")
        clauses.append("fs.room_id=%s")
        args.append(int(query["room_id"]))
    if query.get("date"):
        day = _parse_date(query["date"], "date")
        clauses.extend(["fs.valid_from <= %s", "fs.valid_until >= %s", "fs.weekday=%s"])
        args.extend([day, day, day.weekday()])
    cursor.execute("""SELECT fs.schedule_id, fs.room_id, r.room_number, fs.title, fs.weekday,
                             fs.start_time, fs.end_time, fs.valid_from, fs.valid_until,
                             fs.status, fs.created_by, fs.created_at
                      FROM facility_schedule_rules fs JOIN rooms r ON r.room_id=fs.room_id
                      WHERE """ + " AND ".join(clauses) + " ORDER BY fs.room_id, fs.weekday, fs.start_time", args)
    rows = cursor.fetchall()
    if query.get("date"):
        day = _parse_date(query["date"], "date")
        ids = [int(r["schedule_id"]) for r in rows]
        actions = _latest_exception_actions(cursor, ids, day)
        for row in rows:
            row["exception_action"] = actions.get(int(row["schedule_id"]))
            row["is_blocked_on_date"] = row["exception_action"] != "RELEASE"
    return rows


def create_recurring_rule(cursor, actor_id, data):
    require_fields(data, ["room_id", "title", "weekday", "start_time", "end_time", "valid_from", "valid_until"])
    if not str(data["room_id"]).isdigit():
        raise ApiError(400, "room_id ต้องเป็นจำนวนเต็ม")
    room_id = int(data["room_id"])
    try:
        weekday = int(data["weekday"])
    except (TypeError, ValueError):
        raise ApiError(400, "weekday ต้องเป็น 0-6 โดย 0=จันทร์ และ 6=อาทิตย์")
    if weekday < 0 or weekday > 6:
        raise ApiError(400, "weekday ต้องเป็น 0-6 โดย 0=จันทร์ และ 6=อาทิตย์")
    title = str(data["title"]).strip()
    if not title or len(title) > 150:
        raise ApiError(400, "title ต้องมีความยาว 1-150 ตัวอักษร")
    start_t = _parse_time(data["start_time"], "start_time")
    end_t = _parse_time(data["end_time"], "end_time")
    if start_t >= end_t:
        raise ApiError(400, "end_time ต้องมากกว่า start_time และต้องอยู่ภายในวันเดียวกัน")
    valid_from = _parse_date(data["valid_from"], "valid_from")
    valid_until = _parse_date(data["valid_until"], "valid_until")
    if valid_from > valid_until:
        raise ApiError(400, "valid_until ต้องไม่ก่อน valid_from")
    lock_rooms(cursor, room_id)
    # Validate every occurrence in the selected term against existing bookings/rules.
    day = valid_from
    while day <= valid_until:
        if day.weekday() == weekday:
            start = datetime.combine(day, start_t)
            end = datetime.combine(day, end_t)
            assert_no_conflict(cursor, room_id, start, end)
        day += timedelta(days=1)
    cursor.execute("""INSERT INTO facility_schedule_rules
        (room_id,title,weekday,start_time,end_time,valid_from,valid_until,status,created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s)""",
        (room_id, title, weekday, start_t, end_t, valid_from, valid_until, actor_id))
    return {"schedule_id": cursor.lastrowid, "room_id": room_id, "title": title,
            "weekday": weekday, "start_time": start_t, "end_time": end_t,
            "valid_from": valid_from, "valid_until": valid_until, "status": "ACTIVE"}


def change_rule_exception(cursor, actor_id, schedule_id, data):
    require_fields(data, ["date", "action", "reason"])
    day = _parse_date(data["date"], "date")
    action = str(data["action"]).upper()
    reason = data.get("reason")
    if action not in ("RELEASE", "RESTORE"):
        raise ApiError(400, "action ต้องเป็น RELEASE หรือ RESTORE")
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
        raise ApiError(400, "กรุณาระบุ reason ความยาวไม่เกิน 500 ตัวอักษร")
    cursor.execute("SELECT * FROM facility_schedule_rules WHERE schedule_id=%s FOR UPDATE", (schedule_id,))
    rule = cursor.fetchone()
    if not rule:
        raise ApiError(404, "ไม่พบตารางประจำรายสัปดาห์")
    if rule["status"] != "ACTIVE":
        raise ApiError(409, "ตารางประจำนี้ไม่ได้เปิดใช้งาน")
    if day < rule["valid_from"] or day > rule["valid_until"] or day.weekday() != int(rule["weekday"]):
        raise ApiError(400, "วันที่เลือกไม่ตรงกับวันประจำหรืออยู่นอกช่วงภาคเรียนของตารางนี้")
    start_t = to_time(rule["start_time"])
    end_t = to_time(rule["end_time"])
    start, end = datetime.combine(day, start_t), datetime.combine(day, end_t)
    if action == "RESTORE":
        # A+C: only restore this date. Never overwrite approved or pending bookings.
        room_ids = connected_room_ids(cursor, int(rule["room_id"]))
        marks = ",".join(["%s"] * len(room_ids))
        cursor.execute(f"""SELECT booking_id, room_id, title, status, start_time, end_time
            FROM bookings WHERE room_id IN ({marks}) AND status IN ('pending','approved')
              AND start_time < %s AND end_time > %s FOR UPDATE""",
            room_ids + [end, start])
        conflicts = cursor.fetchall()
        if conflicts:
            raise ApiError(409, "คืนตารางประจำไม่ได้: วันที่นี้มีคำขอจองหรือการจองที่ยังมีผลอยู่ กรุณาจัดการ conflict ก่อน",
                           {"date": day.isoformat(), "conflicting_bookings": conflicts})
    cursor.execute("""INSERT INTO facility_schedule_exceptions
        (schedule_id,exception_date,action,reason,created_by)
        VALUES (%s,%s,%s,%s,%s)""", (schedule_id, day, action, reason.strip(), actor_id))
    return {"schedule_id": schedule_id, "date": day, "action": action,
            "message": "บันทึกข้อยกเว้นเฉพาะวันเรียบร้อยแล้ว" if action == "RELEASE" else "คืนตารางประจำเฉพาะวันนี้แล้ว"}



def change_room_closure(cursor, actor_id, room_id, data):
    """Close/open a room for maintenance with an audit trail and a required reason."""
    require_fields(data, ["action", "reason"])
    action = str(data["action"]).upper()
    reason = data.get("reason")
    if action not in ("CLOSE", "OPEN"):
        raise ApiError(400, "action ต้องเป็น CLOSE หรือ OPEN")
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
        raise ApiError(400, "กรุณาระบุ reason ความยาว 1-500 ตัวอักษร")

    cursor.execute("SELECT room_id, room_number, is_active, is_bookable, is_permanent_locked FROM rooms WHERE room_id=%s FOR UPDATE", (room_id,))
    room = cursor.fetchone()
    if not room:
        raise ApiError(404, "ไม่พบห้องที่ระบุ")

    cursor.execute("SELECT closure_id, previous_is_bookable FROM room_closures WHERE room_id=%s AND status='CLOSED' ORDER BY closure_id DESC LIMIT 1 FOR UPDATE", (room_id,))
    active_closure = cursor.fetchone()

    if action == "CLOSE":
        if active_closure:
            raise ApiError(409, "ห้องนี้ถูกปิดอยู่แล้ว กรุณาเปิดห้องหรือแก้ไขรายการปิดเดิมก่อน")
        cursor.execute("UPDATE rooms SET is_bookable=FALSE WHERE room_id=%s", (room_id,))
        cursor.execute("""INSERT INTO room_closures
            (room_id, reason, previous_is_bookable, status, created_by)
            VALUES (%s,%s,%s,'CLOSED',%s)""",
            (room_id, reason.strip(), bool(room["is_bookable"]), actor_id))
        return {"room_id": room_id, "room_number": room["room_number"], "status": "CLOSED", "reason": reason.strip(), "message": "ปิดห้องเรียบร้อยแล้ว และบล็อกการจองใหม่"}

    if not room["is_active"] or room["is_permanent_locked"]:
        raise ApiError(409, "ไม่สามารถเปิดให้จองได้ เพราะห้องไม่ active หรือถูกล็อกถาวร")
    if not active_closure:
        if room["is_bookable"]:
            raise ApiError(409, "ห้องนี้เปิดให้จองอยู่แล้ว")
        # ห้องที่ปิดมาจากทางอื่น (เช่น ข้อมูลเดิม) ยังไม่มีประวัติการปิด:
        # บันทึกประวัติทันทีเพื่อให้ตรวจสอบย้อนหลังได้ แล้วเปิดห้อง
        cursor.execute("""INSERT INTO room_closures
            (room_id, reason, previous_is_bookable, status, created_by,
             opened_by, opening_reason, opened_at)
            VALUES (%s,%s,FALSE,'OPENED',%s,%s,%s,CURRENT_TIMESTAMP)""",
            (room_id, "(ไม่มีบันทึกการปิดก่อนหน้า)", actor_id, actor_id, reason.strip()))
        cursor.execute("UPDATE rooms SET is_bookable=TRUE WHERE room_id=%s", (room_id,))
        return {"room_id": room_id, "room_number": room["room_number"], "status": "OPENED", "reason": reason.strip(), "message": "เปิดห้องให้จองแล้ว"}
    cursor.execute("UPDATE room_closures SET status='OPENED', opened_by=%s, opening_reason=%s, opened_at=CURRENT_TIMESTAMP WHERE closure_id=%s AND status='CLOSED'",
                   (actor_id, reason.strip(), active_closure["closure_id"]))
    cursor.execute("UPDATE rooms SET is_bookable=%s WHERE room_id=%s", (bool(active_closure["previous_is_bookable"]), room_id))
    return {"room_id": room_id, "room_number": room["room_number"], "status": "OPENED", "reason": reason.strip(), "message": "บันทึกการเปิดห้องแล้ว โดยคืนสถานะการจองเดิมก่อนปิดห้อง"}


def list_admin_rooms(cursor):
    cursor.execute("""SELECT room_id, room_number, is_active, is_bookable, is_permanent_locked
        FROM rooms ORDER BY room_number""")
    return cursor.fetchall()


def list_room_closures(cursor, query):
    clauses = []
    args = []
    if query.get("room_id"):
        if not str(query["room_id"]).isdigit():
            raise ApiError(400, "room_id ต้องเป็นจำนวนเต็ม")
        clauses.append("rc.room_id=%s")
        args.append(int(query["room_id"]))
    if query.get("status"):
        status = str(query["status"]).upper()
        if status not in ("CLOSED", "OPENED"):
            raise ApiError(400, "status ต้องเป็น CLOSED หรือ OPENED")
        clauses.append("rc.status=%s")
        args.append(status)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cursor.execute("""SELECT rc.closure_id, rc.room_id, r.room_number, rc.reason,
        rc.previous_is_bookable, rc.status, rc.created_by, rc.closed_at,
        rc.opened_by, rc.opening_reason, rc.opened_at
        FROM room_closures rc JOIN rooms r ON r.room_id=rc.room_id""" + where +
        " ORDER BY rc.closed_at DESC, rc.closure_id DESC LIMIT 200", args)
    return cursor.fetchall()


def lambda_handler(event, context):
    method, path = get_method_path(event or {})
    if method == "OPTIONS":
        return response(200, {"message": "OK"})
    # This endpoint must be protected by API Gateway authorizer. Do not deploy as an unauthenticated public API.
    claims = get_claims(event or {})
    if not claims:
        return response(401, {"error": "Unauthorized", "message": "ไม่พบข้อมูล Token จาก API Gateway Authorizer"})

    connection = None
    try:
        connection = connect_db()
        with connection.cursor() as cursor:
            actor_id = resolve_user_id(cursor, claims)
            result = None
            # Paths are normalized in get_method_path (optional /v1 prefix is removed).
            if method == "GET" and path == "/approvals/pending":
                require_role(cursor, actor_id, "APPROVER")
                result = {"items": pending_approvals(cursor)}
                connection.commit()
                return response(200, result)

            match = re.fullmatch(r"/approvals/(\d+)/decision", path)
            if method == "POST" and match:
                require_role(cursor, actor_id, "APPROVER")
                result = approve_decision(connection, cursor, int(match.group(1)), actor_id, body_json(event))
                connection.commit()
                return response(200, result)

            if method == "GET" and path == "/admin/rooms":
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = {"items": list_admin_rooms(cursor)}
                connection.commit()
                return response(200, result)

            if method == "GET" and path == "/room-closures":
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = {"items": list_room_closures(cursor, event.get("queryStringParameters") or {})}
                connection.commit()
                return response(200, result)

            match = re.fullmatch(r"/rooms/(\d+)/availability", path)
            if method == "POST" and match:
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = change_room_closure(cursor, actor_id, int(match.group(1)), body_json(event))
                connection.commit()
                return response(200, result)

            if method == "GET" and path == "/facility-schedule-rules":
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = {"items": list_recurring_rules(cursor, event.get("queryStringParameters") or {})}
                connection.commit()
                return response(200, result)

            if method == "POST" and path == "/facility-schedule-rules":
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = create_recurring_rule(cursor, actor_id, body_json(event))
                connection.commit()
                return response(201, result)

            match = re.fullmatch(r"/facility-schedule-rules/(\d+)/exceptions", path)
            if method == "POST" and match:
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = change_rule_exception(cursor, actor_id, int(match.group(1)), body_json(event))
                connection.commit()
                return response(200, result)

            if method == "GET" and path == "/facility-schedules":
                # Read access is login-required; restrict further here if your faculty policy requires it.
                result = {"items": list_schedules(cursor, event.get("queryStringParameters") or {})}
                connection.commit()
                return response(200, result)

            if method == "POST" and path == "/facility-schedules":
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = create_schedule(cursor, actor_id, body_json(event))
                connection.commit()
                return response(201, result)

            match = re.fullmatch(r"/facility-schedules/(\d+)", path)
            if method == "PATCH" and match:
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = update_schedule(cursor, actor_id, int(match.group(1)), body_json(event))
                connection.commit()
                return response(200, result)

            match = re.fullmatch(r"/facility-schedules/(\d+)/cancel", path)
            if method == "POST" and match:
                require_role(cursor, actor_id, "FACILITY_ADMIN")
                result = cancel_schedule(cursor, actor_id, int(match.group(1)))
                connection.commit()
                return response(200, result)

            connection.rollback()
            return response(404, {"error": "Not Found", "message": f"ไม่มี endpoint สำหรับ {method} {path}"})

    except ApiError as error:
        if connection:
            connection.rollback()
        body = {"error": error.message}
        if error.details is not None:
            body["details"] = error.details
        return response(error.status_code, body)
    except Exception as error:
        if connection:
            connection.rollback()
        print("V3 workflow error:", repr(error))
        return response(500, {"error": "Internal server error", "message": "เกิดข้อผิดพลาดภายในระบบ กรุณาตรวจ CloudWatch Logs"})
    finally:
        if connection:
            connection.close()
