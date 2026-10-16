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

        # Get all rooms
        with connection.cursor() as cursor:

            sql = """
                SELECT
                    r.room_id,
                    r.room_number,
                    rt.room_type_id,
                    rt.type_name AS room_type,
                    r.floor,
                    r.capacity,
                    r.caretaker_name,
                    r.image_url,
                    r.amenities_json,
                    r.is_partitionable,
                    r.is_permanent_locked,
                    r.is_active,
                    r.is_bookable,
                    r.created_at
                FROM rooms r
                JOIN room_types rt
                    ON r.room_type_id = rt.room_type_id
                WHERE r.is_active = 1
                ORDER BY r.room_number
            """

            cursor.execute(sql)
            rooms = cursor.fetchall()

        # Return all rooms
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(
                rooms,
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