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
            "Access-Control-Allow-Methods": "OPTIONS,POST"
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
        # 1. รับข้อมูลจาก API Gateway
        # ==========================================

        body = event.get("body")

        if not body:
            return response(400, {
                "error": "Request body is required"
            })

        if isinstance(body, str):
            body = json.loads(body)

        print("Received login data:", body)

        # ==========================================
        # 2. รับ username
        # ==========================================

        username = body.get("username")

        if not username:
            return response(400, {
                "error": "username is required"
            })

        # ==========================================
        # 3. เชื่อมต่อ RDS
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
        # 4. ค้นหา User
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
        # 5. ไม่พบ User
        # ==========================================

        if not user:
            return response(404, {
                "success": False,
                "error": "User not found"
            })

        print("Login user:", user)

        # ==========================================
        # 6. Login สำเร็จ
        # ==========================================

        return response(200, {
            "success": True,
            "message": "Login successful",
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