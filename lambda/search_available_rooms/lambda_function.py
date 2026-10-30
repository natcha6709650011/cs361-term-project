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
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
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
        "amenities": query.get("amenities"),
    }


def validate_input(params):
    errors = {}

    date_value = params["date"]
    start_time_value = params["start_time"]
    end_time_value = params["end_time"]
    min_capacity_value = params["min_capacity"]
    room_type_value = params["room_type"]
    amenities_value = params["amenities"]

    # -----------------------------
    # Date - optional
    # -----------------------------
    search_date = None

    if date_value:
        try:
            search_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            errors["date"] = "รูปแบบวันที่ไม่ถูกต้อง ต้องเป็น YYYY-MM-DD"

    # -----------------------------
    # Start time - optional
    # -----------------------------
    start_time = None

    if start_time_value:
        try:
            start_time = datetime.strptime(
                start_time_value,
                "%H:%M"
            ).time()
        except (ValueError, TypeError):
            errors["startTime"] = "รูปแบบเวลาไม่ถูกต้อง ต้องเป็น HH:MM"

    # -----------------------------
    # End time - optional
    # -----------------------------
    end_time = None

    if end_time_value:
        try:
            end_time = datetime.strptime(
                end_time_value,
                "%H:%M"
            ).time()
        except (ValueError, TypeError):
            errors["endTime"] = "รูปแบบเวลาไม่ถูกต้อง ต้องเป็น HH:MM"

    # ถ้ากรอกเวลา ต้องกรอกทั้งเริ่มและสิ้นสุด
    if start_time_value and not end_time_value:
        errors["endTime"] = "กรุณาระบุเวลาสิ้นสุด"

    if end_time_value and not start_time_value:
        errors["startTime"] = "กรุณาระบุเวลาเริ่มต้น"

    # เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด
    if start_time and end_time:
        if start_time >= end_time:
            errors["endTime"] = "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น"

    # -----------------------------
    # Minimum capacity - optional
    # -----------------------------
    min_capacity = None

    if min_capacity_value:
        try:
            min_capacity = int(min_capacity_value)

            if min_capacity <= 0:
                raise ValueError

        except (ValueError, TypeError):
            errors["minCapacity"] = "ความจุต้องเป็นจำนวนเต็มมากกว่า 0"

    # -----------------------------
    # Room type - optional
    # -----------------------------
    room_type = None

    if room_type_value not in (None, ""):
        try:
            room_type = int(room_type_value)

            if room_type <= 0:
                raise ValueError

        except (ValueError, TypeError):
            errors["roomType"] = "ประเภทห้องไม่ถูกต้อง"

    # -----------------------------
    # Amenities - optional comma-separated list
    # Each selected amenity must be present in a matching room.
    # -----------------------------
    amenities = []

    if amenities_value:
        allowed_amenities = {
            "โปรเจคเตอร์",
            "คอมพิวเตอร์",
            "ทีวี",
            "ปลั๊กไฟ",
        }
        amenities = [
            item.strip()
            for item in str(amenities_value).split(",")
            if item.strip()
        ]

        if not amenities or any(item not in allowed_amenities for item in amenities):
            errors["amenities"] = "รายการอุปกรณ์ไม่ถูกต้อง"

    if errors:
        return errors, None

    return {}, {
        "date": search_date,
        "start_time": start_time,
        "end_time": end_time,
        "min_capacity": min_capacity,
        "room_type": room_type,
        "amenities": amenities,
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
            return json.loads(value)
        except json.JSONDecodeError:
            return []

    return []


def search_available_rooms(connection, params):

    # ----------------------------------------
    # Basic room conditions
    # ----------------------------------------

    conditions = [
        "r.is_active = TRUE",
        "r.is_permanent_locked = FALSE",
        "r.is_bookable = TRUE",
    ]

    values = []

    # ----------------------------------------
    # Minimum capacity
    # ----------------------------------------

    if params["min_capacity"] is not None:
        conditions.append(
            "r.capacity IS NOT NULL AND r.capacity >= %s"
        )

        values.append(params["min_capacity"])

    # ----------------------------------------
    # Room type
    # ----------------------------------------

    if params["room_type"] is not None:
        conditions.append(
            "r.room_type_id = %s"
        )

        values.append(params["room_type"])

    # ----------------------------------------
    # Required amenities
    # JSON_SEARCH checks the `item` of every amenities_json element.
    # Adding one condition per selected item means the room must have all of them.
    # ----------------------------------------

    for amenity in params["amenities"]:
        conditions.append(
            "JSON_SEARCH(r.amenities_json, 'one', %s, NULL, '$[*].item') IS NOT NULL"
        )
        values.append(amenity)

    # ----------------------------------------
    # Booking availability
    #
    # Only check booking overlap when
    # date + start time + end time are provided.
    # ----------------------------------------

    if (
        params["date"] is not None
        and params["start_time"] is not None
        and params["end_time"] is not None
    ):

        requested_start = datetime.combine(
            params["date"],
            params["start_time"]
        )

        requested_end = datetime.combine(
            params["date"],
            params["end_time"]
        )

        conditions.append(
            """
            NOT EXISTS (
                SELECT 1
                FROM bookings b
                WHERE b.room_id = r.room_id
                  AND b.status IN ('approved', 'pending')
                  AND b.start_time < %s
                  AND b.end_time > %s
            )
            """
        )

        values.extend([
            requested_end,
            requested_start,
        ])

    # ----------------------------------------
    # SQL
    # ----------------------------------------

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
            r.is_active,
            r.is_bookable

        FROM rooms r

        INNER JOIN room_types rt
            ON r.room_type_id = rt.room_type_id

        WHERE {" AND ".join(conditions)}

        ORDER BY r.room_number ASC
    """

    print("SQL:", sql)
    print("VALUES:", values)

    with connection.cursor() as cursor:
        cursor.execute(sql, values)
        rooms = cursor.fetchall()

    # ----------------------------------------
    # Convert amenities JSON
    # ----------------------------------------

    for room in rooms:
        room["amenities"] = parse_amenities(
            room.get("amenities_json")
        )

        room.pop("amenities_json", None)

    return rooms


def lambda_handler(event, context):

    # ----------------------------------------
    # HTTP method
    # ----------------------------------------

    method = (
        event.get("httpMethod")
        or event.get("requestContext", {})
        .get("http", {})
        .get("method")
    )

    if method == "OPTIONS":
        return response(
            200,
            {
                "message": "OK"
            }
        )

    # ----------------------------------------
    # Get query parameters
    # ----------------------------------------

    params = get_query_parameters(event or {})

    print("Raw parameters:", params)

    # ----------------------------------------
    # Validate parameters
    # ----------------------------------------

    errors, clean_params = validate_input(params)

    if errors:
        print("Validation errors:", errors)

        return response(
            400,
            {
                "error": "Invalid input",
                "details": errors,
            }
        )

    # ----------------------------------------
    # Database
    # ----------------------------------------

    connection = None

    try:

        connection = connect_database()

        rooms = search_available_rooms(
            connection,
            clean_params
        )

        # ----------------------------------------
        # No rooms
        # ----------------------------------------

        if not rooms:

            return response(
                200,
                {
                    "count": 0,
                    "rooms": [],
                    "message": "ไม่พบห้องว่างตามเงื่อนไขที่เลือก",
                }
            )

        # ----------------------------------------
        # Success
        # ----------------------------------------

        return response(
            200,
            {
                "count": len(rooms),
                "rooms": rooms,
            }
        )

    except Exception as error:

        print(
            "Database error:",
            repr(error)
        )

        return response(
            500,
            {
                "error": "Internal server error",
                "message": "เกิดข้อผิดพลาดในการค้นหาห้องว่าง",
            }
        )

    finally:

        if connection:
            connection.close()
