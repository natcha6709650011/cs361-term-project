import json
import os
import time
import urllib.request
import urllib.error
import pymysql
import jwt


# =========================================================
# JWT CONFIGURATION
# =========================================================

KID = "d47c0efedabc6b33"
PRIVATE_KEY_PATH = "/var/task/private.pem"


# =========================================================
# MOCK USERS
# =========================================================
# ใช้สำหรับทดสอบ Login โดยไม่ต้องเรียก TU API
#
# employee:
#   teacher002
#   staff002
#   employee001
#
# student:
#   master001
#   doctoral001
#
# นักศึกษาปริญญาตรีจริง เช่น 6709650011
# จะเรียก TU API จริง
# =========================================================

MOCK_USERS = {

    "teacher002": {
        "password": "Teacher@123",
        "username": "teacher002",
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
        "status_work": "1",
        "status_emp": "1",
        "access_role": "teacher"
    },

    "staff002": {
        "password": "Staff@123",
        "username": "staff002",
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
        "status_work": "1",
        "status_emp": "1",
        "access_role": "facility_admin"
    },

    "employee001": {
        "password": "Employee@123",
        "username": "employee001",
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
        "status_work": "1",
        "status_emp": "1",
        "access_role": "employee"
    },

    "master001": {
        "password": "Master@123",
        "username": "master001",
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
        "access_role": "student"
    },

    "doctoral001": {
        "password": "Doctoral@123",
        "username": "doctoral001",
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
        "access_role": "student"
    }
}


# =========================================================
# RESPONSE
# =========================================================

def response(status_code, body):

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers":
                "Content-Type,Authorization",
            "Access-Control-Allow-Methods":
                "OPTIONS,POST"
        },
        "body": json.dumps(
            body,
            ensure_ascii=False
        )
    }


# =========================================================
# PARSE STUDENT INFORMATION FROM TU API
# =========================================================

def parse_student_info(tu_data):

    department = tu_data.get("department") or ""

    education_level = None
    program_type = None
    program = None

    # -----------------------------------------------------
    # ระดับการศึกษา
    # -----------------------------------------------------

    if "ปริญญาตรี" in department:
        education_level = "undergraduate"

    elif "ปริญญาโท" in department:
        education_level = "master"

    elif "ปริญญาเอก" in department:
        education_level = "doctoral"

    # -----------------------------------------------------
    # ภาคการศึกษา
    # -----------------------------------------------------

    if "ภาคพิเศษ" in department:
        program_type = "special"

    elif "ภาคปกติ" in department:
        program_type = "normal"

    # -----------------------------------------------------
    # สาขาวิชา
    # -----------------------------------------------------

    if "สาขาวิชา" in department:

        program = department[
            department.find("สาขาวิชา"):
        ].strip()

    return {
        "education_level": education_level,
        "program_type": program_type,
        "program": program
    }


# =========================================================
# MOCK USER LOGIN
# =========================================================

def get_mock_user(username, password):

    mock_user = MOCK_USERS.get(username)

    if not mock_user:
        return None

    if mock_user["password"] != password:
        return "INVALID_PASSWORD"

    return mock_user


# =========================================================
# SAVE / UPDATE USER
# =========================================================

def save_user(user):

    conn = None

    try:

        conn = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=int(
                os.environ.get(
                    "DB_PORT",
                    3306
                )
            ),
            connect_timeout=10
        )

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (user["username"],)
            )

            existing_user = cursor.fetchone()

            if existing_user:

                cursor.execute(
                    """
                    UPDATE users
                    SET
                        user_type = %s,
                        displayname_th = %s,
                        displayname_en = %s,
                        email = %s,
                        faculty = %s,
                        program = %s,
                        education_level = %s,
                        program_type = %s,
                        department = %s,
                        organization = %s,
                        tu_status = %s,
                        status_id = %s,
                        status_work = %s,
                        status_emp = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE username = %s
                    """,
                    (
                        user.get("user_type"),
                        user.get("displayname_th"),
                        user.get("displayname_en"),
                        user.get("email"),
                        user.get("faculty"),
                        user.get("program"),
                        user.get("education_level"),
                        user.get("program_type"),
                        user.get("department"),
                        user.get("organization"),
                        user.get("tu_status"),
                        user.get("status_id"),
                        user.get("status_work"),
                        user.get("status_emp"),
                        user.get("username")
                    )
                )

                print(
                    "User updated:",
                    user["username"]
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO users
                    (
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
                        status_emp
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        user.get("username"),
                        user.get("user_type"),
                        user.get("displayname_th"),
                        user.get("displayname_en"),
                        user.get("email"),
                        user.get("faculty"),
                        user.get("program"),
                        user.get("education_level"),
                        user.get("program_type"),
                        user.get("department"),
                        user.get("organization"),
                        user.get("tu_status"),
                        user.get("status_id"),
                        user.get("status_work"),
                        user.get("status_emp")
                    )
                )

                print(
                    "New user inserted:",
                    user["username"]
                )

            conn.commit()

    except Exception as db_error:

        print(
            "RDS ERROR:",
            str(db_error)
        )

        raise

    finally:

        if conn:
            conn.close()


# =========================================================
# GET USER FROM DB
# =========================================================

def get_user_from_db(username):

    conn = None

    try:

        conn = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            port=int(
                os.environ.get(
                    "DB_PORT",
                    3306
                )
            ),
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    user_id,
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
                    status_emp
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,)
            )

            return cursor.fetchone()

    finally:

        if conn:
            conn.close()


# =========================================================
# CREATE JWT
# =========================================================

def create_token(user):

    with open(
        PRIVATE_KEY_PATH,
        "r"
    ) as f:

        private_key = f.read()

    current_time = int(time.time())

    # -----------------------------------------------------
    # สิทธิ์หลัก
    #
    # employee:
    #   teacher / facility_admin / employee
    #
    # student:
    #   student
    # -----------------------------------------------------

    if user["user_type"] == "employee":

        if user["username"] == "teacher002":
            access_role = "teacher"

        elif user["username"] == "staff002":
            access_role = "facility_admin"

        else:
            access_role = "employee"

    else:

        access_role = "student"

    payload = {

        "sub":
            str(user["username"]),

        "username":
            str(user["username"]),

        "user_type":
            user["user_type"],

        "role":
            access_role,

        "education_level":
            user.get("education_level"),

        "program_type":
            user.get("program_type"),

        "program":
            user.get("program"),

        "department":
            user.get("department"),

        "faculty":
            user.get("faculty"),

        "organization":
            user.get("organization"),

        "tu_status":
            user.get("tu_status"),

        "status_id":
            user.get("status_id"),

        "iat":
            current_time,

        "exp":
            current_time + 3600
    }

    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={
            "kid": KID
        }
    )

    return token, access_role


# =========================================================
# LAMBDA HANDLER
# =========================================================

def lambda_handler(event, context):

    try:

        # =================================================
        # รับ username / password
        # =================================================

        body = event.get(
            "body",
            {}
        )

        if isinstance(body, str):

            body = json.loads(body)

        username = body.get("username")
        password = body.get("password")

        if not username or not password:

            return response(
                400,
                {
                    "status": False,
                    "message":
                        "Username and password are required"
                }
            )

        print(
            "Login attempt:",
            username
        )


        # =================================================
        # 1. ตรวจสอบ MOCK USER ก่อน
        # =================================================

        mock_result = get_mock_user(
            username,
            password
        )

        if mock_result == "INVALID_PASSWORD":

            return response(
                401,
                {
                    "status": False,
                    "message":
                        "Invalid username or password"
                }
            )


        # =================================================
        # 2. ถ้าเป็น MOCK USER
        #    ไม่ต้องเรียก TU API
        # =================================================

        if mock_result:

            user = mock_result.copy()

            print(
                "Using MOCK user:",
                username
            )

            save_user(user)

        else:

            # =================================================
            # 3. ไม่ใช่ mock -> เรียก TU API จริง
            # =================================================

            tu_api_url = os.environ["TU_API_URL"]
            tu_api_key = os.environ["TU_API_KEY"]

            request_data = json.dumps(
                {
                    "UserName": username,
                    "PassWord": password
                }
            ).encode("utf-8")

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

            try:

                with urllib.request.urlopen(
                    request,
                    timeout=10
                ) as res:

                    tu_data = json.loads(
                        res.read().decode("utf-8")
                    )

            except urllib.error.HTTPError as api_error:

                print(
                    "TU API HTTP ERROR:",
                    api_error.code
                )

                return response(
                    401,
                    {
                        "status": False,
                        "message":
                            "Invalid username or password"
                    }
                )

            except Exception as api_error:

                print(
                    "TU API ERROR:",
                    str(api_error)
                )

                return response(
                    500,
                    {
                        "status": False,
                        "message":
                            "Unable to connect to TU API"
                    }
                )


            print(
                "TU API response:",
                tu_data
            )


            # =================================================
            # ตรวจสอบ TU API Login
            # =================================================

            if not tu_data.get("status"):

                return response(
                    401,
                    {
                        "status": False,
                        "message":
                            tu_data.get(
                                "message",
                                "Invalid username or password"
                            )
                    }
                )


            # =================================================
            # TU API -> Student
            # =================================================

            user_type = "student"

            parsed = parse_student_info(
                tu_data
            )


            user = {

                "username":
                    tu_data.get(
                        "username",
                        username
                    ),

                "user_type":
                    user_type,

                "displayname_th":
                    tu_data.get(
                        "displayname_th"
                    ),

                "displayname_en":
                    tu_data.get(
                        "displayname_en"
                    ),

                "email":
                    tu_data.get(
                        "email"
                    ),

                "faculty":
                    tu_data.get(
                        "faculty"
                    ),

                "program":
                    parsed.get(
                        "program"
                    ),

                "education_level":
                    parsed.get(
                        "education_level"
                    ),

                "program_type":
                    parsed.get(
                        "program_type"
                    ),

                "department":
                    tu_data.get(
                        "department"
                    ),

                "organization":
                    tu_data.get(
                        "organization"
                    ),

                "tu_status":
                    tu_data.get(
                        "tu_status"
                    ),

                "status_id":
                    tu_data.get(
                        "statusid"
                    ),

                "status_work":
                    tu_data.get(
                        "StatusWork"
                    ),

                "status_emp":
                    tu_data.get(
                        "StatusEmp"
                    )
            }


            print(
                "Parsed student:",
                user
            )


            # =================================================
            # เก็บข้อมูล API ลง DB
            # =================================================

            save_user(user)


        # =================================================
        # อ่านข้อมูลล่าสุดจาก DB
        # =================================================
        # DB เป็น source of truth สำหรับสิทธิ์
        # =================================================

        db_user = get_user_from_db(
            username
        )

        if not db_user:

            return response(
                500,
                {
                    "status": False,
                    "message":
                        "User was not found in database"
                }
            )


        # =================================================
        # สร้าง JWT จากข้อมูล DB
        # =================================================

        token, access_role = create_token(
            db_user
        )


        print(
            "JWT created successfully"
        )

        print(
            "username:",
            db_user["username"]
        )

        print(
            "user_type:",
            db_user["user_type"]
        )

        print(
            "education_level:",
            db_user["education_level"]
        )

        print(
            "program_type:",
            db_user["program_type"]
        )

        print(
            "role:",
            access_role
        )


        # =================================================
        # Response
        # =================================================

        return response(
            200,
            {
                "status": True,

                "message":
                    "Login successful",

                "token":
                    token,

                "user": {

                    "username":
                        db_user["username"],

                    "displayname_th":
                        db_user["displayname_th"],

                    "displayname_en":
                        db_user["displayname_en"],

                    "email":
                        db_user["email"],

                    "user_type":
                        db_user["user_type"],

                    "role":
                        access_role,

                    "faculty":
                        db_user["faculty"],

                    "program":
                        db_user["program"],

                    "education_level":
                        db_user["education_level"],

                    "program_type":
                        db_user["program_type"],

                    "department":
                        db_user["department"],

                    "organization":
                        db_user["organization"],

                    "tu_status":
                        db_user["tu_status"],

                    "status_id":
                        db_user["status_id"],

                    "status_work":
                        db_user["status_work"],

                    "status_emp":
                        db_user["status_emp"]
                }
            }
        )


    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )

        return response(
            500,
            {
                "status": False,
                "message":
                    "Internal server error"
            }
        )
