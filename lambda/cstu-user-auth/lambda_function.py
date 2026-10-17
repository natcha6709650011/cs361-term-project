import json
import os
import urllib.request


def lambda_handler(event, context):

    try:
        # รับ username/password จาก API Gateway
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

        # =========================
        # เรียก TU API
        # =========================

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

        with urllib.request.urlopen(request, timeout=10) as res:

            tu_data = json.loads(
                res.read().decode("utf-8")
            )

        print("TU API response:", tu_data)

        # =========================
        # ตรวจสอบ Login
        # =========================

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

        # =========================
        # ตรวจสอบประเภทผู้ใช้
        # =========================

        user_type = tu_data.get("type")

        if user_type == "student":

            role = "student"

        elif user_type == "employee":

            role = "employee"

        else:

            role = "unknown"

        # =========================
        # ส่งข้อมูลกลับ
        # =========================

        return response(
            200,
            {
                "status": True,
                "message": "Login successful",

                "user": {
                    "username": tu_data.get("username"),
                    "displayname_th": tu_data.get("displayname_th"),
                    "displayname_en": tu_data.get("displayname_en"),
                    "email": tu_data.get("email"),

                    "type": user_type,
                    "role": role,

                    "department": tu_data.get("department"),
                    "faculty": tu_data.get("faculty"),
                    "organization": tu_data.get("organization")
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
        "body": json.dumps(body, ensure_ascii=False)
    }