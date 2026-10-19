import json
import os
import pymysql

def response(status_code, data):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(data, ensure_ascii=False, default=str)
    }

def get_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        port=int(os.environ.get("DB_PORT", "3306")),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )

def get_room_types(connection):
    sql = """
        SELECT
            rt.room_type_id,
            rt.type_name,
            rp.user_type,
            rp.is_allowed
        FROM room_types rt
        LEFT JOIN room_policies rp
            ON rt.room_type_id = rp.room_type_id
        ORDER BY rt.room_type_id, rp.user_type
    """

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    room_types = {}

    for row in rows:
        type_id = row["room_type_id"]

        if type_id not in room_types:
            room_types[type_id] = {
                "room_type_id": type_id,
                "type_name": row["type_name"],
                "policies": []
            }

        if row["user_type"] is not None:
            room_types[type_id]["policies"].append({
                "user_type": row["user_type"],
                "is_allowed": bool(row["is_allowed"])
            })

    return list(room_types.values())

def get_room_connections(connection, room_number):
    sql = """
        SELECT
            rc.connection_id,
            r1.room_number AS room_1,
            r2.room_number AS room_2,
            CASE
                WHEN r1.room_number = %s
                    THEN r2.room_number
                ELSE r1.room_number
            END AS connected_room_number
        FROM room_connections rc
        JOIN rooms r1
            ON rc.room_id_1 = r1.room_id
        JOIN rooms r2
            ON rc.room_id_2 = r2.room_id
        WHERE rc.is_active = TRUE
          AND (r1.room_number = %s OR r2.room_number = %s)
        ORDER BY connected_room_number
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            (room_number, room_number, room_number)
        )
        rows = cursor.fetchall()

    return {
        "room_number": room_number,
        "connections": rows
    }

def lambda_handler(event, context):
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {})
             .get("http", {})
             .get("method")
        or ""
    )

    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    if method != "GET":
        return response(405, {"message": "Method not allowed"})

    path = (
        event.get("rawPath")
        or event.get("path")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or ""
    ).rstrip("/")

    # Remove API Gateway stage prefix, e.g. /v1
    stage = event.get("requestContext", {}).get("stage")

    if stage and path.startswith(f"/{stage}/"):
        path = path[len(f"/{stage}"):]

    path_parameters = event.get("pathParameters") or {}
    room_number = path_parameters.get("room_number")

    parts = path.strip("/").split("/")

    if (
        room_number is None
        and len(parts) == 3
        and parts[0] == "rooms"
        and parts[2] == "connections"
    ):
        room_number = parts[1]

    if path == "/room-types":
        action = "room_types"
    elif (
        room_number is not None
        and path.endswith("/connections")
    ):
        action = "room_connections"
    else:
        return response(404, {"message": "API not found"})

    connection = None

    try:
        connection = get_connection()

        if action == "room_types":
            data = get_room_types(connection)
            return response(200, {"room_types": data})

        data = get_room_connections(connection, room_number)

        if not data["connections"]:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT room_id FROM rooms WHERE room_number = %s",
                    (room_number,)
                )
                room = cursor.fetchone()

            if room is None:
                return response(404, {"message": "Room not found"})

        return response(200, data)

    except Exception:
        print("Room configuration request failed")
        return response(500, {"message": "Internal server error"})

    finally:
        if connection:
            connection.close()