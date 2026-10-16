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
        "body": json.dumps(body, ensure_ascii=False, default=str)
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

        print("Received user data:", body)

        # ==========================================
        # 2. ดึงข้อมูล User
        # ==========================================

        username = body.get("username")

        # TU API ใช้ field ชื่อ "type"
        user_type = body.get("type")

        if not username:
            return response(400, {
                "error": "username is required"
            })

        if not user_type:
            return response(400, {
                "error": "type is required"
            })

        # ==========================================
        # 3. เชื่อมต่อ RDS MySQL
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
        # 4. เตรียมข้อมูล
        # ==========================================

        displayname_th = body.get("displayname_th")
        displayname_en = body.get("displayname_en")
        email = body.get("email")

        faculty = body.get("faculty")
        program = body.get("program")
        education_level = body.get("education_level")
        program_type = body.get("program_type")
        year_level = body.get("year_level")

        department = body.get("department")
        organization = body.get("organization")

        # ==========================================
        # 5. INSERT / UPDATE User
        # ==========================================

        sql = """
            INSERT INTO users (
                username,
                user_type,
                displayname_th,
                displayname_en,
                email,
                faculty,
                program,
                education_level,
                program_type,
                year_level,
                department,
                organization
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s
            )
            ON DUPLICATE KEY UPDATE

                user_type = VALUES(user_type),
                displayname_th = VALUES(displayname_th),
                displayname_en = VALUES(displayname_en),
                email = VALUES(email),
                faculty = VALUES(faculty),
                program = VALUES(program),
                education_level = VALUES(education_level),
                program_type = VALUES(program_type),
                year_level = VALUES(year_level),
                department = VALUES(department),
                organization = VALUES(organization)
        """

        values = (
            username,
            user_type,
            displayname_th,
            displayname_en,
            email,
            faculty,
            program,
            education_level,
            program_type,
            year_level,
            department,
            organization
        )

        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            connection.commit()

        # ==========================================
        # 6. ดึงข้อมูล User ที่เพิ่งบันทึก
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

            saved_user = cursor.fetchone()

        print("Saved user:", saved_user)

        # ==========================================
        # 7. ส่งผลลัพธ์กลับ
        # ==========================================

        return response(200, {
            "success": True,
            "message": "User saved successfully",
            "user": saved_user
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