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

def response(status_code, body, cookie=None):

    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin":
            os.environ.get(
                "FRONTEND_ORIGIN",
                "*"
            ),
        "Access-Control-Allow-Headers":
            "Content-Type,Authorization",
        "Access-Control-Allow-Methods":
            "OPTIONS,POST",
        "Access-Control-Allow-Credentials":
            "true"
    }

    if cookie:
        headers["Set-Cookie"] = cookie

    return {
        "statusCode": status_code,
        "headers": headers,
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

    user = MOCK_USERS.get(username)

    if not user:
        return None

    if user["password"] != password:
        return None

    return user


# =========================================================
# TU API
# =========================================================

def get_tu_user(username, password):

    # -----------------------------------------------------
    # URL ของ TU API
    # -----------------------------------------------------

    url = os.environ.get(
        "TU_API_URL",
        ""
    )

    if not url:
        raise Exception(
            "TU_API_URL is not configured"
        )

    # -----------------------------------------------------
    # Request
    # -----------------------------------------------------

    payload = json.dumps({
        "username": username,
        "password": password
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type":
                "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response_data:

            raw_data = response_data.read()

            return json.loads(
                raw_data.decode("utf-8")
            )

    except urllib.error.HTTPError as e:

        print(
            "TU API HTTP Error:",
            e.code
        )

        return None

    except Exception as e:

        print(
            "TU API Error:",
            str(e)
        )

        return None


# =========================================================
# GET USER FROM DATABASE
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
                    "3306"
                )
            ),
            cursorclass=
                pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
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
# SAVE / UPDATE USER
# =========================================================

def save_user_to_db(user):

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
                    "3306"
                )
            ),
            cursorclass=
                pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:

            cursor.execute(
                """
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
                    status_emp
                )
                VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s
                )
                ON DUPLICATE KEY UPDATE
                    user_type = VALUES(user_type),
                    displayname_th =
                        VALUES(displayname_th),
                    displayname_en =
                        VALUES(displayname_en),
                    email =
                        VALUES(email),
                    faculty =
                        VALUES(faculty),
                    program =
                        VALUES(program),
                    education_level =
                        VALUES(education_level),
                    program_type =
                        VALUES(program_type),
                    department =
                        VALUES(department),
                    organization =
                        VALUES(organization),
                    tu_status =
                        VALUES(tu_status),
                    status_id =
                        VALUES(status_id),
                    status_work =
                        VALUES(status_work),
                    status_emp =
                        VALUES(status_emp)
                """,
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

            conn.commit()

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
            current_time + 604800  # 7 days
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


        # =================================================
        # ตรวจสอบ MOCK USER
        # =================================================

        mock_user = get_mock_user(
            username,
            password
        )

        if mock_user:

            user = mock_user

        else:

            # =============================================
            # เรียก TU API
            # =============================================

            tu_data = get_tu_user(
                username,
                password
            )

            if not tu_data:

                return response(
                    401,
                    {
                        "status": False,
                        "message":
                            "Invalid username or password"
                    }
                )


            # =============================================
            # แปลงข้อมูลนักศึกษา
            # =============================================

            education_info = \
                parse_student_info(
                    tu_data
                )


            user = {

                "username":
                    tu_data.get(
                        "username",
                        username
                    ),

                "user_type":
                    "student",

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
                    education_info[
                        "program"
                    ],

                "education_level":
                    education_info[
                        "education_level"
                    ],

                "program_type":
                    education_info[
                        "program_type"
                    ],

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
                        "status_id"
                    ),

                "status_work":
                    None,

                "status_emp":
                    None
            }


            # =============================================
            # บันทึกข้อมูล User
            # =============================================

            save_user_to_db(
                user
            )


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

        session_cookie = (
            "session_token="
            + token
            + "; "
            + "HttpOnly; "
            + "Secure; "
            + "SameSite=None; "
            + "Path=/; "
            + "Max-Age=604800"
        )

        return response(
            200,
            {
                "status": True,

                "message":
                    "Login successful",

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
            },
            cookie=session_cookie
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