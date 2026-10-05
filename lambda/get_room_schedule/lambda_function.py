import json
import os
from datetime import datetime, timedelta

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


def lambda_handler(event, context):
    event = event or {}

    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
    )

    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    if method and method != "GET":
        return response(405, {
            "error": "Method Not Allowed",
            "message": "รองรับเฉพาะ GET",
        })

    try:
        path_parameters = event.get("pathParameters") or {}
        room_number = path_parameters.get("room_number")

        query_parameters = event.get("queryStringParameters") or {}
        date_string = query_parameters.get("date")

        if room_number is None or str(room_number).strip() == "":
            return response(400, {
                "error": "Missing room_number",
                "message": "กรุณาระบุ room_number",
            })

        room_number = str(room_number).strip()

        if date_string is None or str(date_string).strip() == "":
            return response(400, {
                "error": "Missing date",
                "message": "กรุณาระบุ date",
            })

        date_string = str(date_string).strip()

        try:
            selected_date = datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError:
            return response(400, {
                "error": "Invalid date",
                "message": "รูปแบบ date ต้องเป็น YYYY-MM-DD",
            })

        day_start = datetime.combine(selected_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        connection = pymysql.connect(
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

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT room_id
                    FROM rooms
                    WHERE room_number = %s
                    LIMIT 1
                    """,
                    (room_number,),
                )

                room = cursor.fetchone()

                if room is None:
                    return response(404, {
                        "error": "Room not found",
                        "message": "ไม่พบห้องที่ระบุ",
                        "room_number": room_number,
                    })

                cursor.execute(
                    """
                    SELECT
                        booking_id,
                        start_time,
                        end_time,
                        status
                    FROM bookings
                    WHERE room_id = %s
                      AND start_time < %s
                      AND end_time > %s
                    ORDER BY start_time ASC
                    """,
                    (room["room_id"], day_end, day_start),
                )

                rows = cursor.fetchall()

        finally:
            connection.close()

        bookings = []
        for row in rows:
            start_time = row["start_time"]
            end_time = row["end_time"]

            bookings.append({
                "booking_id": row["booking_id"],
                "start_time": (
                    start_time.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(start_time, "strftime")
                    else str(start_time)
                ),
                "end_time": (
                    end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(end_time, "strftime")
                    else str(end_time)
                ),
                "status": row["status"],
            })

        return response(200, {
            "room_number": room_number,
            "date": date_string,
            "bookings": bookings,
        })

    except KeyError as error:
        print("Missing environment variable:", repr(error))
        return response(500, {
            "error": "Configuration error",
            "message": "Lambda environment variables ไม่ครบ",
        })

    except Exception as error:
        print("Lambda error:", repr(error))
        return response(500, {
            "error": "Internal server error",
            "message": "เกิดข้อผิดพลาดภายในระบบ",
        })