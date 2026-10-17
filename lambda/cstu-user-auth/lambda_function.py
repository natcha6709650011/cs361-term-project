import json
import os
import urllib.request
import pymysql


def lambda_handler(event, context):

    try:
        # ==========================================
        # 1. รับ username / password
        # ==========================================

        body = event.get("body", {})

        if isinstance(body, str):
            body = json.loads(body)

        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            return response(
                400,
                {
                    "status": False,
                    "message": "Username and password are required"
                }
            )

        # ==========================================
        # 2. เรียก TU API
        # ==========================================

        tu_api_url = os.environ["TU_API_URL"]
        tu_api_key = os.environ["TU_API_KEY"]

        request_data = json.dumps({
            "UserName": username,
            "PassWord": password
        }).encode("utf-8")

        request = urllib.request.Request(
            tu_api_url,
            data=request_data,
            method="POST"
        )

        request.add_header(
            "Content-Type",
            "application/json"
        )

        request.add_header(
            "Application-Key",
            tu_api_key
        )

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as res:

            tu_data = json.loads(
                res.read().decode("utf-8")
            )

        print("TU API response:", tu_data)

        # ==========================================
        # 3. ตรวจสอบ Login
        # ==========================================

        if not tu_data.get("status"):

            return response(
                401,
                {
                    "status": False,
                    "message": tu_data.get(
                        "message",
                        "Invalid username or password"
                    )
                }
            )

        # ==========================================
        # 4. เตรียมข้อมูลจาก TU API
        # ==========================================

        user_type = tu_data.get("type")

        user = {
            "username": tu_data.get("username"),
            "user_type": user_type,
            "displayname_th": tu_data.get("displayname_th"),
            "displayname_en": tu_data.get("displayname_en"),
            "email": tu_data.get("email"),

            "faculty": tu_data.get("faculty"),
            "program": tu_data.get("program"),
            "education_level": tu_data.get(
                "education_level"
            ),
            "program_type": tu_data.get(
                "program_type"
            ),

            "department": tu_data.get("department"),
            "organization": tu_data.get(
                "organization"
            ),

            "tu_status": tu_data.get("tu_status"),
            "status_id": tu_data.get("statusid"),

            "status_work": tu_data.get(
                "status_work"
            ),

            "status_emp": tu_data.get(
                "status_emp"
            )
        }

        # ==========================================
        # 5. EMPLOYEE MOCK
        # ==========================================

        employee_mock = {

            "teacher002": {
                "user_type": "employee",
                "displayname_th": "อาจารย์อนุมัติ",
                "displayname_en": "Test Approver",
                "email": "teacher002@tu.ac.th",
                "department": "สาขาวิทยาการคอมพิวเตอร์",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "role": "teacher"
            },

            "staff002": {
                "user_type": "employee",
                "displayname_th": "เจ้าหน้าที่ดูแลสถานที่",
                "displayname_en": "Test Facility Admin",
                "email": "staff002@tu.ac.th",
                "department": "งานบริหารและจัดการทั่วไป",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "role": "staff"
            },

            "employee001": {
                "user_type": "employee",
                "displayname_th": "บุคลากรทดสอบ",
                "displayname_en": "Test Employee",
                "email": "employee001@tu.ac.th",
                "department": "งานบริหารทั่วไป",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "role": "employee"
            }
        }

        # ==========================================
        # 6. ถ้าเป็น employee mock
        #    ให้ใช้ข้อมูล mock
        # ==========================================

        role = "student"

        if username in employee_mock:

            mock = employee_mock[username]

            user_type = "employee"

            user["user_type"] = "employee"
            user["displayname_th"] = mock[
                "displayname_th"
            ]
            user["displayname_en"] = mock[
                "displayname_en"
            ]
            user["email"] = mock["email"]

            user["department"] = mock[
                "department"
            ]

            user["organization"] = mock[
                "organization"
            ]

            role = mock["role"]

        elif user_type == "student":

            role = "student"

        elif user_type == "employee":

            role = "employee"

        else:

            role = "unknown"

        # ==========================================
        # 7. Connect RDS
        # ==========================================

        connection = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )

        try:

            with connection.cursor() as cursor:

                # ==================================
                # 8. INSERT / UPDATE users
                # ==================================

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
                    department,
                    organization,
                    tu_status,
                    status_id,
                    status_work,
                    status_emp,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    NOW(), NOW()
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
                    department = VALUES(department),
                    organization = VALUES(organization),
                    tu_status = VALUES(tu_status),
                    status_id = VALUES(status_id),
                    status_work = VALUES(status_work),
                    status_emp = VALUES(status_emp),
                    updated_at = NOW()
                """

                cursor.execute(
                    sql,
                    (
                        user["username"],
                        user["user_type"],
                        user["displayname_th"],
                        user["displayname_en"],
                        user["email"],

                        user["faculty"],
                        user["program"],
                        user["education_level"],
                        user["program_type"],

                        user["department"],
                        user["organization"],

                        user["tu_status"],
                        user["status_id"],
                        user["status_work"],
                        user["status_emp"]
                    )
                )

                # ==================================
                # 9. หา user_id
                # ==================================

                cursor.execute(
                    """
                    SELECT user_id
                    FROM users
                    WHERE username = %s
                    """,
                    (user["username"],)
                )

                db_user = cursor.fetchone()

                if not db_user:
                    raise Exception(
                        "User was not found after INSERT/UPDATE"
                    )

                user_id = db_user["user_id"]

                # ==================================
                # 10. หา role_id
                # ==================================

                cursor.execute(
                    """
                    SELECT role_id
                    FROM roles
                    WHERE role_name = %s
                    """,
                    (role,)
                )

                db_role = cursor.fetchone()

                if not db_role:
                    raise Exception(
                        f"Role '{role}' not found"
                    )

                role_id = db_role["role_id"]

                # ==================================
                # 11. ผูก user กับ role
                # ==================================

                cursor.execute(
                    """
                    INSERT INTO user_roles (
                        user_id,
                        role_id
                    )
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        role_id = VALUES(role_id)
                    """,
                    (
                        user_id,
                        role_id
                    )
                )

                connection.commit()

        finally:

            connection.close()

        # ==========================================
        # 12. Response กลับไป frontend
        # ==========================================

        return response(
            200,
            {
                "status": True,
                "message": "Login successful",

                "user": {
                    "user_id": user_id,

                    "username": user["username"],

                    "displayname_th":
                        user["displayname_th"],

                    "displayname_en":
                        user["displayname_en"],

                    "email":
                        user["email"],

                    "type":
                        user["user_type"],

                    "role":
                        role,

                    "faculty":
                        user["faculty"],

                    "program":
                        user["program"],

                    "education_level":
                        user["education_level"],

                    "program_type":
                        user["program_type"],

                    "department":
                        user["department"],

                    "organization":
                        user["organization"],

                    "tu_status":
                        user["tu_status"],

                    "status_id":
                        user["status_id"],

                    "status_work":
                        user["status_work"],

                    "status_emp":
                        user["status_emp"]
                }
            }
        )

    except Exception as e:

        print("ERROR:", str(e))

        return response(
            500,
            {
                "status": False,
                "message": "Internal server error"
            }
        )


def response(status_code, body):

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(
            body,
            ensure_ascii=False
        )
    }