import json
import os
import pymysql


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(
            body,
            ensure_ascii=False,
            default=str
        )
    }


def lambda_handler(event, context):

    connection = None

    try:

        # ==========================================
        # 1. รับ username จาก API Gateway Path
        # ==========================================

        path_parameters = event.get("pathParameters") or {}

        username = path_parameters.get("username")

        if not username:
            return response(400, {
                "error": "username is required"
            })

        print("Get user:", username)

        # ==========================================
        # 2. เชื่อมต่อ RDS MySQL
        # ==========================================

        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=int(os.environ["DB_PORT"]),
            cursorclass=pymysql.cursors.DictCursor
        )

        # ==========================================
        # 3. ค้นหา User
        # ==========================================

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,)
            )

            user = cursor.fetchone()

        # ==========================================
        # 4. ไม่พบ User
        # ==========================================

        if not user:
            return response(404, {
                "success": False,
                "error": "User not found"
            })

        print("Found user:", user)

        # ==========================================
        # 5. ส่งข้อมูล User กลับ
        # ==========================================

        return response(200, {
            "success": True,
            "user": user
        })

    except Exception as e:

        print("ERROR:", str(e))

        if connection:
            connection.rollback()

        return response(500, {
            "success": False,
            "error": str(e)
        })

    finally:

        if connection:
            connection.close()