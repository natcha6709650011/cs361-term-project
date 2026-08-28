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

        # Execute SQL query
        with connection.cursor() as cursor:
            sql = """
                SELECT
                    r.room_id,
                    r.room_number,
                    rt.type_name AS room_type,
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
                WHERE r.is_active = 1
            """

            cursor.execute(sql)
            rooms = cursor.fetchall()

        # Return room data
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

        # Return error
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

        # Close database connection
        if connection:
            connection.close()