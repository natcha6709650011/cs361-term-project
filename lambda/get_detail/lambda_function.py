import json
import os
import pymysql


def lambda_handler(event, context):

    connection = None

    try:
        # Connect to RDS MySQL
        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=int(os.environ["DB_PORT"]),
            cursorclass=pymysql.cursors.DictCursor
        )

        # Get room number from path parameter
        room_number = event.get("pathParameters", {}).get("room_number")

        if not room_number:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "room_number is required"
                }, ensure_ascii=False)
            }

        # Get room detail
        with connection.cursor() as cursor:

            sql = """
                SELECT
                    r.room_id,
                    r.room_number,
                    rt.room_type_id,
                    rt.type_name AS room_type,
                    rt.is_bookable,
                    rt.allowed_roles_json,
                    r.floor,
                    r.capacity,
                    r.caretaker_name,
                    r.image_url,
                    r.amenities_json,
                    r.is_partitionable,
                    r.is_permanent_locked,
                    r.is_active,
                    r.created_at
                FROM rooms r
                JOIN room_types rt
                    ON r.room_type_id = rt.room_type_id
                WHERE r.room_number = %s
                LIMIT 1
            """

            cursor.execute(sql, (room_number,))
            room = cursor.fetchone()

        # Room not found
        if not room:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Room not found"
                }, ensure_ascii=False)
            }

        # Return room detail
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(
                room,
                ensure_ascii=False,
                default=str
            )
        }

    except Exception as e:

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        }

    finally:

        if connection:
            connection.close()