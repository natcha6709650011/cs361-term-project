import json
import os
import re
import traceback
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
        # 2. TEST MOCK ACCOUNTS / TU API
        # ==========================================
        #
        # Mock accounts are for testing the web login only.
        # Their passwords are NOT stored in the users table.
        # They are checked here, then the same users INSERT/UPDATE
        # flow below stores the user profile in RDS.
        #
        # Existing real students continue to authenticate through TU API.
        # ==========================================

        mock_accounts = {

            # ------------------------------------------
            # Employee mock accounts
            # ------------------------------------------
            "teacher002": {
                "password": "teacher123",
                "user_type": "employee",
                "displayname_th": "อาจารย์ผู้อนุมัติ",
                "displayname_en": "Test Approver",
                "email": "teacher002@tu.ac.th",
                "faculty": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "program": None,
                "education_level": None,
                "program_type": None,
                "department": "สาขาวิชาวิทยาการคอมพิวเตอร์",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "tu_status": "ปกติ",
                "status_id": None,
                "status_work": None,
                "status_emp": None,
                "role": "APPROVER"
            },

            "staff002": {
                "password": "staff123",
                "user_type": "employee",
                "displayname_th": "เจ้าหน้าที่ดูแลสถานที่",
                "displayname_en": "Test Facility Admin",
                "email": "staff002@tu.ac.th",
                "faculty": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "program": None,
                "education_level": None,
                "program_type": None,
                "department": "งานบริการและจัดการห้อง",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "tu_status": "ปกติ",
                "status_id": None,
                "status_work": None,
                "status_emp": None,
                "role": "FACILITY_ADMIN"
            },

            "employee001": {
                "password": "employee123",
                "user_type": "employee",
                "displayname_th": "บุคลากรทดสอบ",
                "displayname_en": "Test Employee",
                "email": "employee001@tu.ac.th",
                "faculty": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "program": None,
                "education_level": None,
                "program_type": None,
                "department": "งานบริหารทั่วไป",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "tu_status": "ปกติ",
                "status_id": None,
                "status_work": None,
                "status_emp": None,
                "role": None
            },

            # ------------------------------------------
            # Student master mock
            # Same faculty/program as undergraduate,
            # but education_level = master.
            # ------------------------------------------
            "master001": {
                "password": "master123",
                "user_type": "student",
                "displayname_th": "นักศึกษาปริญญาโททดสอบ",
                "displayname_en": "Test Master Student",
                "email": "master001@dome.tu.ac.th",
                "faculty": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "program": "สาขาวิชาวิทยาการคอมพิวเตอร์",
                "education_level": "master",
                "program_type": "special",
                "department": "ปริญญาโท ภาคพิเศษ สาขาวิชาวิทยาการคอมพิวเตอร์",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "tu_status": "ปกติ",
                "status_id": "10",
                "status_work": None,
                "status_emp": None,
                "role": None
            },

            # ------------------------------------------
            # Student doctoral mock
            # Same faculty/program as undergraduate,
            # but education_level = doctoral.
            # ------------------------------------------
            "doctoral001": {
                "password": "doctoral123",
                "user_type": "student",
                "displayname_th": "นักศึกษาปริญญาเอกทดสอบ",
                "displayname_en": "Test Doctoral Student",
                "email": "doctoral001@dome.tu.ac.th",
                "faculty": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "program": "สาขาวิชาวิทยาการคอมพิวเตอร์",
                "education_level": "doctoral",
                "program_type": "special",
                "department": "ปริญญาเอก ภาคพิเศษ สาขาวิชาวิทยาการคอมพิวเตอร์",
                "organization": "คณะวิทยาศาสตร์และเทคโนโลยี",
                "tu_status": "ปกติ",
                "status_id": "10",
                "status_work": None,
                "status_emp": None,
                "role": None
            }
        }

        if username in mock_accounts:

            mock = mock_accounts[username]

            if password != mock["password"]:
                return response(
                    401,
                    {
                        "status": False,
                        "message": "Invalid username or password"
                    }
                )

            # Build the same data shape as TU API so the
            # existing RDS INSERT/UPDATE logic is reused.
            tu_data = {
                "status": True,
                "message": "Success",
                "type": mock["user_type"],
                "username": username,
                "displayname_th": mock["displayname_th"],
                "displayname_en": mock["displayname_en"],
                "email": mock["email"],
                "faculty": mock["faculty"],
                "program": mock["program"],
                "education_level": mock["education_level"],
                "program_type": mock["program_type"],
                "department": mock["department"],
                "organization": mock["organization"],
                "tu_status": mock["tu_status"],
                "statusid": mock["status_id"],
                "status_work": mock["status_work"],
                "status_emp": mock["status_emp"]
            }

            print(
                "MOCK LOGIN:",
                username,
                "type=",
                mock["user_type"],
                "role=",
                mock["role"]
            )

        else:

            # ==========================================
            # Real login -> TU API
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

        # -------------------------------------------------
        # Student education mapping
        #
        # TU API may return the education information in
        # "department" as one combined string, for example:
        #
        # "ปริญญาตรี ภาคพิเศษ สาขาวิชาวิทยาการคอมพิวเตอร์"
        #
        # We keep the original department value AND derive
        # separate fields for permission comparison:
        #   education_level -> undergraduate / master / doctoral
        #   program_type    -> regular / special
        #   program         -> สาขาวิชาวิทยาการคอมพิวเตอร์
        # -------------------------------------------------

        department = tu_data.get("department")

        education_level = tu_data.get("education_level")
        program_type = tu_data.get("program_type")
        program = tu_data.get("program")

        if user_type == "student" and department:
            education_text = str(department).strip()

            # Degree level
            if "ปริญญาตรี" in education_text:
                education_level = "undergraduate"
            elif "ปริญญาโท" in education_text:
                education_level = "master"
            elif "ปริญญาเอก" in education_text:
                education_level = "doctoral"

            # Study type
            if "ภาคพิเศษ" in education_text:
                program_type = "special"
            elif "ภาคปกติ" in education_text:
                program_type = "regular"

            # Program / major
            # Keep everything after "สาขา" as the program name.
            # This supports "สาขาวิชา..." and "สาขา..."
            program_match = re.search(
                r"(สาข(?:าวิชา)?[^,;|]*)",
                education_text
            )

            if program_match:
                program = program_match.group(1).strip()

        # For employees, education/program fields are not applicable.
        if user_type == "employee":
            program = None
            education_level = None
            program_type = None

        user = {
            "username": tu_data.get("username"),
            "user_type": user_type,
            "displayname_th": tu_data.get("displayname_th"),
            "displayname_en": tu_data.get("displayname_en"),
            "email": tu_data.get("email"),

            "faculty": tu_data.get("faculty"),
            "program": program,
            "education_level": education_level,
            "program_type": program_type,

            # Keep the original TU API value for traceability.
            "department": department,
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
        # 5. MOCK ROLE
        # ==========================================

        mock = mock_accounts.get(username)

        # ==========================================
        # 6. Role
        # ==========================================

        # Special roles come only from the existing DB:
        # APPROVER / FACILITY_ADMIN.
        # Mock students and normal employees have no special role.

        role = None

        if mock:
            role = mock["role"]

        elif user_type == "student":
            role = None

        elif user_type == "employee":
            role = None

        else:
            role = None

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
                # 10-11. หา role_id และผูก user กับ role
                # ==================================
                # Only special roles from the existing DB are linked.
                # Students/normal employees have role = None.

                role_id = None

                if role:

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
        print("TRACEBACK:")
        print(traceback.format_exc())

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