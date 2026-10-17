import json
import os
import time
import urllib.request
import pymysql
import jwt


KID = "d47c0efedabc6b33"
PRIVATE_KEY_PATH = "/var/task/private.pem"


# =========================================================
# MOCK USERS
# ข้อมูลตัวบุคคลอ้างอิงจาก users table
# Password มีไว้สำหรับทดสอบ Login เท่านั้น
# =========================================================

MOCK_USERS = {

    "teacher002": {
        "password": "Teacher@123"
    },

    "staff002": {
        "password": "Staff@123"
    },

    "employee001": {
        "password": "Employee@123"
    },

    "master001": {
        "password": "Master@123"
    },

    "doctoral001": {
        "password": "Doctoral@123"
    }
}


# =========================================================
# แยกระดับนักศึกษาและภาค
# =========================================================

def parse_student_program(department):

    department = department or ""

    # ระดับการศึกษา
    if "ปริญญาเอก" in department:
        education_level = "doctoral"

    elif "ปริญญาโท" in department:
        education_level = "master"

    elif "ปริญญาตรี" in department:
        education_level = "undergraduate"

    else:
        education_level = None


    # ภาคการศึกษา
    if "ภาคพิเศษ" in department:
        program_type = "special"

    elif "ภาคปกติ" in department:
        program_type = "regular"

    else:
        program_type = None


    return education_level, program_type


# =========================================================
# Response
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
# Lambda Handler
# =========================================================

def lambda_handler(event, context):

    try:

        # =================================================
        # รับ username / password
        # =================================================

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
                    "message":
                        "Username and password are required"
                }
            )


        print("Login username:", username)


        # =================================================
        # เชื่อมต่อ RDS
        # =================================================

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


        # =================================================
        # MOCK LOGIN
        # =================================================

        if username in MOCK_USERS:

            print(
                "MOCK LOGIN:",
                username
            )


            # -------------------------------------------------
            # ตรวจ password
            # -------------------------------------------------

            if password != MOCK_USERS[username]["password"]:

                conn.close()

                return response(
                    401,
                    {
                        "status": False,
                        "message":
                            "Invalid username or password"
                    }
                )


            # -------------------------------------------------
            # ดึงข้อมูลจาก DB
            # DB เป็น source of truth
            # -------------------------------------------------

            with conn.cursor(
                pymysql.cursors.DictCursor
            ) as cursor:

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

                user = cursor.fetchone()


            conn.close()


            # -------------------------------------------------
            # ไม่มี user ใน DB
            # -------------------------------------------------

            if not user:

                return response(
                    404,
                    {
                        "status": False,
                        "message":
                            "User not found in database"
                    }
                )


            # -------------------------------------------------
            # กำหนด role จาก DB
            # -------------------------------------------------

            if user["user_type"] == "student":

                role = "student"

            elif user["user_type"] == "employee":

                role = "employee"

            else:

                role = "unknown"


            education_level = user.get(
                "education_level"
            )

            program_type = user.get(
                "program_type"
            )


            # -------------------------------------------------
            # สร้าง JWT
            # -------------------------------------------------

            with open(
                PRIVATE_KEY_PATH,
                "r"
            ) as f:

                private_key = f.read()


            current_time = int(time.time())


            payload = {

                "sub":
                    str(user["username"]),

                "username":
                    str(user["username"]),

                "type":
                    user["user_type"],

                "role":
                    role,

                "education_level":
                    education_level,

                "program_type":
                    program_type,

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


            print(
                "MOCK JWT created"
            )

            print(
                "username:",
                username
            )

            print(
                "role:",
                role
            )

            print(
                "education_level:",
                education_level
            )

            print(
                "program_type:",
                program_type
            )


            return response(
                200,
                {

                    "status":
                        True,

                    "message":
                        "Login successful",

                    "token":
                        token,

                    "user": {

                        "username":
                            user["username"],

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

                        "education_level":
                            education_level,

                        "program_type":
                            program_type,

                        "program":
                            user["program"],

                        "department":
                            user["department"],

                        "faculty":
                            user["faculty"],

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


        # =================================================
        # REAL TU API LOGIN
        # =================================================

        print(
            "REAL TU API LOGIN:",
            username
        )


        tu_api_url = os.environ["TU_API_URL"]

        tu_api_key = os.environ["TU_API_KEY"]


        request_data = json.dumps({

            "UserName":
                username,

            "PassWord":
                password

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


        try:

            with urllib.request.urlopen(
                request,
                timeout=10
            ) as res:

                tu_data = json.loads(
                    res.read().decode("utf-8")
                )


        except urllib.error.HTTPError as api_error:

            error_body = ""

            try:
                error_body = api_error.read().decode(
                    "utf-8",
                    errors="ignore"
                )
            except Exception:
                pass


            print(
                "TU API ERROR:",
                api_error.code,
                error_body
            )


            conn.close()


            return response(
                401,
                {
                    "status": False,
                    "message":
                        "Invalid username or password"
                }
            )


        print(
            "TU API response:",
            tu_data
        )


        # =================================================
        # ตรวจ Login จาก TU API
        # =================================================

        if not tu_data.get("status"):

            conn.close()

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
        # User Type
        # =================================================

        user_type = tu_data.get("type")


        if user_type == "student":

            role = "student"

        elif user_type == "employee":

            role = "employee"

        else:

            role = "unknown"


        # =================================================
        # นักศึกษา
        # แยกระดับ + ภาค
        # =================================================

        education_level = None

        program_type = None


        if user_type == "student":

            education_level, program_type = \
                parse_student_program(
                    tu_data.get("department")
                )


        print(
            "education_level:",
            education_level
        )

        print(
            "program_type:",
            program_type
        )


        # =================================================
        # Employee ไม่มี education/program
        # =================================================

        if user_type == "employee":

            education_level = None

            program_type = None


        # =================================================
        # INSERT / UPDATE RDS
        # =================================================

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (username,)
            )

            existing_user = cursor.fetchone()


            # -------------------------------------------------
            # UPDATE
            # -------------------------------------------------

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
                        updated_at = NOW()
                    WHERE username = %s
                    """,

                    (

                        user_type,

                        tu_data.get(
                            "displayname_th"
                        ),

                        tu_data.get(
                            "displayname_en"
                        ),

                        tu_data.get(
                            "email"
                        ),

                        tu_data.get(
                            "faculty"
                        ),

                        tu_data.get(
                            "program"
                        ),

                        education_level,

                        program_type,

                        tu_data.get(
                            "department"
                        ),

                        tu_data.get(
                            "organization"
                        ),

                        tu_data.get(
                            "tu_status"
                        ),

                        tu_data.get(
                            "statusid"
                        ),

                        tu_data.get(
                            "StatusWork"
                        ),

                        tu_data.get(
                            "StatusEmp"
                        ),

                        username
                    )
                )


                print(
                    "User updated:",
                    username
                )


            # -------------------------------------------------
            # INSERT
            # -------------------------------------------------

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

                        tu_data.get(
                            "username",
                            username
                        ),

                        user_type,

                        tu_data.get(
                            "displayname_th"
                        ),

                        tu_data.get(
                            "displayname_en"
                        ),

                        tu_data.get(
                            "email"
                        ),

                        tu_data.get(
                            "faculty"
                        ),

                        tu_data.get(
                            "program"
                        ),

                        education_level,

                        program_type,

                        tu_data.get(
                            "department"
                        ),

                        tu_data.get(
                            "organization"
                        ),

                        tu_data.get(
                            "tu_status"
                        ),

                        tu_data.get(
                            "statusid"
                        ),

                        tu_data.get(
                            "StatusWork"
                        ),

                        tu_data.get(
                            "StatusEmp"
                        )
                    )
                )


                print(
                    "New user inserted:",
                    username
                )


            conn.commit()


        conn.close()


        # =================================================
        # JWT
        # =================================================

        with open(
            PRIVATE_KEY_PATH,
            "r"
        ) as f:

            private_key = f.read()


        current_time = int(time.time())


        payload = {

            "sub":
                str(username),

            "username":
                str(username),

            "type":
                user_type,

            "role":
                role,

            "education_level":
                education_level,

            "program_type":
                program_type,

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


        print(
            "JWT created successfully"
        )

        print(
            "username:",
            username
        )

        print(
            "role:",
            role
        )

        print(
            "education_level:",
            education_level
        )

        print(
            "program_type:",
            program_type
        )


        # =================================================
        # Return
        # =================================================

        return response(
            200,
            {

                "status":
                    True,

                "message":
                    "Login successful",

                "token":
                    token,

                "user": {

                    "username":
                        tu_data.get(
                            "username",
                            username
                        ),

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

                    "type":
                        user_type,

                    "role":
                        role,

                    "education_level":
                        education_level,

                    "program_type":
                        program_type,

                    "program":
                        tu_data.get(
                            "program"
                        ),

                    "department":
                        tu_data.get(
                            "department"
                        ),

                    "faculty":
                        tu_data.get(
                            "faculty"
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
                "status":
                    False,

                "message":
                    "Internal server error"
            }
        )
