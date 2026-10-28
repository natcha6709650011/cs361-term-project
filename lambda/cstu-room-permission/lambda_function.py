import json
import os

import pymysql

ROLE_APPROVER = "APPROVER"
ROLE_FACILITY_ADMIN = "FACILITY_ADMIN"

def response(status_code, body, methods="GET,OPTIONS"):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": methods,
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def forbidden(message="You do not have permission to perform this action"):
    return response(403, {"error": "Forbidden", "message": message})


def get_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        port=int(os.environ.get("DB_PORT", "3306")),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
    )

def get_authenticated_username(event):
    """username from the Lambda Authorizer context (verified JWT)."""
    authorizer = (event.get("requestContext") or {}).get("authorizer") or {}

    lambda_ctx = authorizer.get("lambda")
    if isinstance(lambda_ctx, dict) and lambda_ctx.get("username"):
        return lambda_ctx["username"]

    return authorizer.get("username") or None


def get_user(connection, username):
    """Return the users row (user_id, username, user_type, education_level)."""
    if not username:
        return None
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, username, user_type, education_level
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,),
        )
        return cursor.fetchone()


def get_user_roles(connection, user_id):
    """Set of role names, e.g. {'APPROVER'}. Empty set = normal user."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT r.role_name
            FROM user_roles ur
            JOIN roles r ON r.role_id = ur.role_id
            WHERE ur.user_id = %s
            """,
            (user_id,),
        )
        return {row["role_name"].upper() for row in cursor.fetchall()}


def load_caller(connection, event):
    """
    Resolve the caller from the event.
    Returns (user, roles, error_response). If error_response is not None,
    return it directly from the handler.
    """
    username = get_authenticated_username(event)
    if not username:
        return None, set(), response(
            401, {"error": "Unauthorized", "message": "Authentication required"}
        )

    user = get_user(connection, username)
    if not user:
        return None, set(), forbidden("User not found")

    return user, get_user_roles(connection, user["user_id"]), None


def require_role(connection, event, role):
    """
    Use at the top of any role-protected action:

        user, roles, err = require_role(conn, event, ROLE_FACILITY_ADMIN)
        if err:
            return err
    """
    user, roles, err = load_caller(connection, event)
    if err:
        return None, roles, err
    if role.upper() not in roles:
        return user, roles, forbidden()
    return user, roles, None

def policy_user_type(user):
    """
    Key used in room_policies.user_type
      employee            -> 'employee'
      student             -> undergraduate / master / doctoral
    A student with unknown education_level gets 'student', which has no
    policy row, so access is denied (safe default).
    """
    if user["user_type"] == "employee":
        return "employee"
    return user.get("education_level") or "student"


def can_book_room_type(connection, room_type_id, user):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT is_allowed
            FROM room_policies
            WHERE room_type_id = %s AND user_type = %s
            LIMIT 1
            """,
            (room_type_id, policy_user_type(user)),
        )
        policy = cursor.fetchone()
    return bool(policy and policy["is_allowed"])


def get_allowed_room_types(connection, user):
    """All room types with whether this user may book them."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rt.room_type_id, rt.type_name,
                   COALESCE(rp.is_allowed, FALSE) AS is_allowed
            FROM room_types rt
            LEFT JOIN room_policies rp
              ON rp.room_type_id = rt.room_type_id AND rp.user_type = %s
            ORDER BY rt.room_type_id
            """,
            (policy_user_type(user),),
        )
        rows = cursor.fetchall()
    return [
        {
            "room_type_id": r["room_type_id"],
            "type_name": r["type_name"],
            "can_book": bool(r["is_allowed"]),
        }
        for r in rows
    ]


def check_room_booking_permission(connection, room_number, user):
    """
    Can `user` book this room?
    Returns (http_status, result_dict). Reason codes:
      OK | ROOM_NOT_FOUND | ROOM_INACTIVE | ROOM_NOT_BOOKABLE |
      ROOM_LOCKED | POLICY_DENIED
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT room_id, room_number, room_type_id,
                   is_active, is_bookable, is_permanent_locked
            FROM rooms
            WHERE room_number = %s
            LIMIT 1
            """,
            (room_number,),
        )
        room = cursor.fetchone()

    if not room:
        return 404, {
            "room_number": room_number,
            "can_book": False,
            "reason": "ROOM_NOT_FOUND",
        }

    base = {
        "room_number": room["room_number"],
        "room_type_id": room["room_type_id"],
    }

    if not room["is_active"]:
        return 200, {**base, "can_book": False, "reason": "ROOM_INACTIVE"}
    if not room["is_bookable"]:
        return 200, {**base, "can_book": False, "reason": "ROOM_NOT_BOOKABLE"}
    if room["is_permanent_locked"]:
        return 200, {**base, "can_book": False, "reason": "ROOM_LOCKED"}

    if not can_book_room_type(connection, room["room_type_id"], user):
        return 200, {**base, "can_book": False, "reason": "POLICY_DENIED"}

    return 200, {**base, "can_book": True, "reason": "OK"}

def get_request_info(event):
    method = (
        event.get("httpMethod")
        or (event.get("requestContext") or {}).get("http", {}).get("method")
        or ""
    ).upper()

    path = (
        event.get("rawPath")
        or event.get("path")
        or (event.get("requestContext") or {}).get("http", {}).get("path")
        or ""
    ).rstrip("/")

    return method, path


def parse_room_number(event, path):
    room_number = (event.get("pathParameters") or {}).get("room_number")

    if room_number is None:
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "rooms" and parts[2] == "permission":
            room_number = parts[1]

    if room_number is None:
        return None

    room_number = str(room_number)
    if not room_number.isdigit() or int(room_number) <= 0:
        return None
    return int(room_number)


def user_summary(user, roles):
    return {
        "username": user["username"],
        "user_type": user["user_type"],
        "education_level": user["education_level"],
        "roles": sorted(roles),
        "is_approver": ROLE_APPROVER in roles,
        "is_facility_admin": ROLE_FACILITY_ADMIN in roles,
    }


def handle_api_request(event, context):
    method, path = get_request_info(event)

    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    if method != "GET":
        return response(405, {"message": "Method not allowed"})

    is_me = path.endswith("/me/permissions")
    is_room = path.endswith("/permission") and "/rooms/" in path

    if not is_me and not is_room:
        return response(404, {"message": "API not found"})

    room_number = None
    if is_room:
        room_number = parse_room_number(event, path)
        if room_number is None:
            return response(400, {"message": "Invalid room_number"})

    connection = None
    try:
        connection = get_connection()

        user, roles, err = load_caller(connection, event)
        if err:
            return err

        if is_me:
            return response(200, {
                "user": user_summary(user, roles),
                "room_types": get_allowed_room_types(connection, user),
            })

        status, result = check_room_booking_permission(
            connection, room_number, user
        )
        return response(status, result)

    except Exception:
        print("Room permission request failed")
        return response(500, {"message": "Internal server error"})

    finally:
        if connection:
            connection.close()



PUBLIC_KEY_PATH = "/var/task/public.pem"
EXPECTED_KID = "d47c0efedabc6b33"

APPROVER = ROLE_APPROVER
FACILITY_ADMIN = ROLE_FACILITY_ADMIN


ROUTE_ROLES = {
    "PATCH /rooms/{room_id}": [FACILITY_ADMIN],
    "PATCH /rooms/{room_id}/status": [FACILITY_ADMIN],
}

def deny():
    return {"isAuthorized": False}


def get_token(event):
    headers = event.get("headers") or {}

    cookie_header = (
        headers.get("cookie")
        or headers.get("Cookie")
    )

    if not cookie_header:
        return None

    for cookie in cookie_header.split(";"):
        cookie = cookie.strip()

        if cookie.startswith("session_token="):
            return cookie[len("session_token="):].strip() or None

    return None

def verify_token(token):
    import jwt  

    unverified = jwt.get_unverified_header(token)
    if unverified.get("kid") != EXPECTED_KID or unverified.get("alg") != "RS256":
        raise jwt.InvalidTokenError("bad kid/alg")

    with open(PUBLIC_KEY_PATH, "r") as f:
        public_key = f.read()

    return jwt.decode(token, public_key, algorithms=["RS256"])


def load_user_and_roles(username):
    """Return (user_row, set_of_roles) or (None, set()) if user not in DB."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.user_id, u.user_type, r.role_name
                FROM users u
                LEFT JOIN user_roles ur ON ur.user_id = u.user_id
                LEFT JOIN roles r ON r.role_id = ur.role_id
                WHERE u.username = %s
                """,
                (username,),
            )
            rows = cursor.fetchall()
    finally:
        connection.close()

    if not rows:
        return None, set()

    user = {"user_id": rows[0]["user_id"], "user_type": rows[0]["user_type"]}
    roles = {r["role_name"].upper() for r in rows if r["role_name"]}
    return user, roles


def primary_role(roles):
    if FACILITY_ADMIN in roles:
        return "facility_admin"
    if APPROVER in roles:
        return "approver"
    return ""


def handle_authorizer(event, context):
    try:
        token = get_token(event)
        if not token:
            return deny()

        payload = verify_token(token)
        username = payload.get("username")
        if not username:
            return deny()

        user, roles = load_user_and_roles(username)
        if user is None:
            return deny()

        required = ROUTE_ROLES.get(event.get("routeKey"))
        if required and not (roles & {r.upper() for r in required}):
            print("DENY", username, event.get("routeKey"), sorted(roles))
            return deny()

        return {
            "isAuthorized": True,
            "context": {
                "username": username,
                "user_id": user["user_id"],
                "user_type": user["user_type"] or "",
                "roles": ",".join(sorted(roles)),
                "role": primary_role(roles),
            },
        }

    except Exception as e:
        print("Authorizer error:", type(e).__name__)
        return deny()


def is_authorizer_event(event):
    return event.get("type") == "REQUEST" and "routeArn" in event


def lambda_handler(event, context):
    if is_authorizer_event(event):
        return handle_authorizer(event, context)
    return handle_api_request(event, context)