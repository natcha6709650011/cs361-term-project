import json
import os
from datetime import datetime

import pymysql


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def get_query_parameters(event):
    query = event.get("queryStringParameters") or {}

    return {
        "date": query.get("date"),
        "start_time": query.get("startTime"),
        "end_time": query.get("endTime"),
        "min_capacity": query.get("minCapacity"),
        "room_type": query.get("roomType"),
    }


def validate_input(params):
    errors = {}

    date_value = params["date"]
    start_time_value = params["start_time"]
    end_time_value = params["end_time"]
    min_capacity_value = params["min_capacity"]
    room_type_value = params["room_type"]

    if not date_value:
        errors["date"] = "กรุณาระบุวันที่"

    if not start_time_value:
        errors["startTime"] = "กรุณาระบุเวลาเริ่มต้น"

    if not end_time_value:
        errors["endTime"] = "กรุณาระบุเวลาสิ้นสุด"

    if not min_capacity_value:
        errors["minCapacity"] = "กรุณาระบุความจุขั้นต่ำ"

    if errors:
        return errors, None

    try:
        search_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        errors["date"] = "รูปแบบวันที่ไม่ถูกต้อง ต้องเป็น YYYY-MM-DD"
        search_date = None

    try:
        start_time = datetime.strptime(start_time_value, "%H:%M").time()
    except (ValueError, TypeError):
        errors["startTime"] = "รูปแบบเวลาไม่ถูกต้อง ต้องเป็น HH:MM"
        start_time = None

    try:
        end_time = datetime.strptime(end_time_value, "%H:%M").time()
    except (ValueError, TypeError):
        errors["endTime"] = "รูปแบบเวลาไม่ถูกต้อง ต้องเป็น HH:MM"
        end_time = None

    if start_time and end_time and start_time >= end_time:
        errors["endTime"] = "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น"

    try:
        min_capacity = int(min_capacity_value)
        if min_capacity <= 0:
            raise ValueError
    except (ValueError, TypeError):
        errors["minCapacity"] = "ความจุต้องเป็นจำนวนเต็มมากกว่า 0"
        min_capacity = None

    room_type = None

    # Empty roomType means "ทุกประเภท"
    if room_type_value not in (None, ""):
        try:
            room_type = int(room_type_value)
            if room_type <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors["roomType"] = "ประเภทห้องไม่ถูกต้อง"

    if errors:
        return errors, None

    return {}, {
        "date": search_date,
        "start_time": start_time,
        "end_time": end_time,
        "min_capacity": min_capacity,
        "room_type": room_type,
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
    )


def parse_amenities(value):
    if value is None:
        return []

    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed
        except json.JSONDecodeError:
            return []

    return []


def search_available_rooms(connection, params):
    conditions = [
        "r.is_active = 1",
        "r.is_permanent_locked = 0",
        "rt.is_bookable = 1",
        "r.capacity IS NOT NULL",
        "r.capacity >= %s",
    ]

    values = [params["min_capacity"]]

    if params["room_type"] is not None:
        conditions.append("r.room_type_id = %s")
        values.append(params["room_type"])

    # Overlap rule:
    # existing.start < requested.end
    # AND existing.end > requested.start
    #
    # Therefore, adjacent intervals such as
    # 08:00-10:00 and 10:00-12:00 do NOT overlap.
    conditions.append(
        """
        NOT EXISTS (
            SELECT 1
            FROM room_schedules rs
            WHERE rs.room_id = r.room_id
              AND rs.schedule_date = %s
              AND rs.is_active = 1
              AND rs.start_time < %s
              AND rs.end_time > %s
        )
        """
    )

    values.extend(
        [
            params["date"],
            params["end_time"],
            params["start_time"],
        ]
    )

    sql = f"""
        SELECT
            r.room_id,
            r.room_number,
            r.room_type_id,
            rt.type_name AS room_type,
            r.floor,
            r.capacity,
            r.caretaker_name,
            r.image_url,
            r.amenities_json,
            r.is_partitionable,
            r.is_permanent_locked,
            r.is_active
        FROM rooms r
        INNER JOIN room_types rt
            ON r.room_type_id = rt.room_type_id
        WHERE {" AND ".join(conditions)}
        ORDER BY r.room_number ASC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, values)
        rooms = cursor.fetchall()

    for room in rooms:
        room["amenities"] = parse_amenities(room.get("amenities_json"))
        room.pop("amenities_json", None)

    return rooms


def lambda_handler(event, context):
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
    )

    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    params = get_query_parameters(event or {})
    errors, clean_params = validate_input(params)

    if errors:
        return response(
            400,
            {
                "error": "Invalid input",
                "details": errors,
            },
        )

    connection = None

    try:
        connection = connect_database()
        rooms = search_available_rooms(connection, clean_params)

        if not rooms:
            return response(
                200,
                {
                    "count": 0,
                    "rooms": [],
                    "message": "ไม่พบห้องว่างตามเงื่อนไขที่เลือก",
                },
            )

        return response(
            200,
            {
                "count": len(rooms),
                "rooms": rooms,
            },
        )

    except Exception as error:
        print("Database error:", repr(error))

        return response(
            500,
            {
                "error": "Internal server error",
                "message": "เกิดข้อผิดพลาดในการค้นหาห้องว่าง",
            },
        )

    finally:
        if connection:
            connection.close()
