
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
            "Access-Control-Allow-Methods": "PATCH,OPTIONS"
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


def parse_body(event):
    body = event.get("body")

    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return None

    if isinstance(body, dict):
        return body

    return None


def get_request_info(event):
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {})
        .get("http", {})
        .get("method")
        or ""
    ).upper()

    path = (
        event.get("rawPath")
        or event.get("path")
        or event.get("requestContext", {})
        .get("http", {})
        .get("path")
        or ""
    ).rstrip("/")

    path_parameters = event.get("pathParameters") or {}
    room_id = path_parameters.get("room_id")

    # รองรับกรณี API Gateway ไม่ส่ง pathParameters มาให้
    parts = path.strip("/").split("/")
    is_status_endpoint = path.endswith("/status")

    if room_id is None:
        if (
            len(parts) == 2
            and parts[0] == "rooms"
        ):
            room_id = parts[1]
        elif (
            len(parts) == 3
            and parts[0] == "rooms"
            and parts[2] == "status"
        ):
            room_id = parts[1]

    return method, path, room_id, is_status_endpoint


def validate_room_id(room_id):
    if room_id is None:
        return None

    room_id = str(room_id)

    if not room_id.isdigit() or int(room_id) <= 0:
        return None

    return int(room_id)


def update_room(connection, room_id, body):
    allowed_fields = {
        "room_number",
        "room_type_id",
        "floor",
        "capacity",
        "caretaker_name",
        "image_url",
        "amenities_json",
        "is_partitionable"
    }

    if not body:
        return response(400, {"message": "Request body is required"})

    unknown_fields = set(body.keys()) - allowed_fields
    if unknown_fields:
        return response(400, {
            "message": "Unsupported fields",
            "fields": sorted(unknown_fields)
        })

    updates = {}
    integer_fields = {"room_number", "room_type_id", "floor", "capacity"}

    for field, value in body.items():
        if field in integer_fields:
            if value is None and field == "capacity":
                updates[field] = None
                continue

            if isinstance(value, bool) or not isinstance(value, int):
                return response(400, {
                    "message": f"{field} must be an integer"
                })

            if value <= 0:
                return response(400, {
                    "message": f"{field} must be greater than 0"
                })

            updates[field] = value

        elif field == "is_partitionable":
            if not isinstance(value, bool):
                return response(400, {
                    "message": "is_partitionable must be a boolean"
                })
            updates[field] = value

        elif field in {"caretaker_name", "image_url"}:
            if value is not None and not isinstance(value, str):
                return response(400, {
                    "message": f"{field} must be a string or null"
                })
            updates[field] = value

        elif field == "amenities_json":
            if value is not None and not isinstance(value, list):
                return response(400, {
                    "message": "amenities_json must be a JSON array or null"
                })

            if value is not None:
                for item in value:
                    if not isinstance(item, dict) or not isinstance(
                        item.get("item"), str
                    ):
                        return response(400, {
                            "message": (
                                "Each amenity must contain an item string"
                            )
                        })

            updates[field] = (
                json.dumps(value, ensure_ascii=False)
                if value is not None else None
            )

    if not updates:
        return response(400, {"message": "No fields to update"})

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT room_id FROM rooms WHERE room_id = %s",
            (room_id,)
        )
        if cursor.fetchone() is None:
            return response(404, {"message": "Room not found"})

        if "room_type_id" in updates:
            cursor.execute(
                "SELECT room_type_id FROM room_types WHERE room_type_id = %s",
                (updates["room_type_id"],)
            )
            if cursor.fetchone() is None:
                return response(400, {"message": "Room type not found"})

        if "room_number" in updates:
            cursor.execute(
                """
                SELECT room_id FROM rooms
                WHERE room_number = %s AND room_id <> %s
                """,
                (updates["room_number"], room_id)
            )
            if cursor.fetchone() is not None:
                return response(409, {
                    "message": "Room number already exists"
                })

        set_clause = ", ".join(
            f"`{field}` = %s" for field in updates
        )
        values = list(updates.values()) + [room_id]

        cursor.execute(
            f"UPDATE rooms SET {set_clause} WHERE room_id = %s",
            values
        )

        cursor.execute(
            "SELECT * FROM rooms WHERE room_id = %s",
            (room_id,)
        )
        updated_room = cursor.fetchone()

    connection.commit()
    return response(200, {
        "message": "Room updated successfully",
        "room": updated_room
    })


def update_room_status(connection, room_id, body):
    allowed_fields = {"is_active", "is_bookable"}

    if not body:
        return response(400, {"message": "Request body is required"})

    unknown_fields = set(body.keys()) - allowed_fields
    if unknown_fields:
        return response(400, {
            "message": "Only is_active and is_bookable can be updated",
            "fields": sorted(unknown_fields)
        })

    if not set(body.keys()).issubset(allowed_fields):
        return response(400, {"message": "Invalid status fields"})

    for field, value in body.items():
        if not isinstance(value, bool):
            return response(400, {
                "message": f"{field} must be a boolean"
            })

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT room_id FROM rooms WHERE room_id = %s",
            (room_id,)
        )
        if cursor.fetchone() is None:
            return response(404, {"message": "Room not found"})

        set_clause = ", ".join(
            f"`{field}` = %s" for field in body
        )
        values = list(body.values()) + [room_id]

        cursor.execute(
            f"UPDATE rooms SET {set_clause} WHERE room_id = %s",
            values
        )

        cursor.execute(
            """
            SELECT room_id, room_number, is_active, is_bookable
            FROM rooms
            WHERE room_id = %s
            """,
            (room_id,)
        )
        updated_status = cursor.fetchone()

    connection.commit()
    return response(200, {
        "message": "Room status updated successfully",
        "room": updated_status
    })


def lambda_handler(event, context):
    method, path, room_id, is_status_endpoint = get_request_info(event)

    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    if method != "PATCH":
        return response(405, {"message": "Method not allowed"})

    if not path.startswith("/rooms/") or room_id is None:
        return response(404, {"message": "API not found"})

    room_id = validate_room_id(room_id)
    if room_id is None:
        return response(400, {"message": "Invalid room_id"})
    role = get_user_role(event)

    if role != "facility_admin":
        return response(403, {"message": "You do not have permission to manage rooms"
    })

    expected_path = (
        f"/rooms/{room_id}/status"
        if is_status_endpoint
        else f"/rooms/{room_id}"
    )
    if path != expected_path:
        return response(404, {"message": "API not found"})

    body = parse_body(event)
    if body is None:
        return response(400, {"message": "Invalid JSON body"})

    connection = None

    try:
        connection = get_connection()

        if is_status_endpoint:
            return update_room_status(connection, room_id, body)

        return update_room(connection, room_id, body)

    except Exception:
        if connection:
            connection.rollback()

        print("Manage room request failed")
        return response(500, {"message": "Internal server error"})

    finally:
        if connection:
            connection.close()
def get_user_role(event):
    """
    Get user role from API Gateway Lambda Authorizer context.
    """
    authorizer = (
        event.get("requestContext", {})
        .get("authorizer", {})
    )

    lambda_context = authorizer.get("lambda", {})

    if isinstance(lambda_context, dict):
        return lambda_context.get("role")

    return None