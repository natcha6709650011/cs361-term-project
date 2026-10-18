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