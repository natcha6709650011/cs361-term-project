import json
import time
import jwt


# =========================
# Configuration
# =========================

PUBLIC_KEY_PATH = "/var/task/public.pem"

EXPECTED_KID = "d47c0efedabc6b33"


def lambda_handler(event, context):


    try:

        # =========================
        # Get JWT from Cookie
        # =========================

        headers = event.get("headers") or {}

        cookie_header = (
            headers.get("cookie")
            or headers.get("Cookie")
        )

        if not cookie_header:
            print("No Cookie header")
            return deny()

        token = None

        for cookie in cookie_header.split(";"):
            cookie = cookie.strip()

            if cookie.startswith("session_token="):
                token = cookie[len("session_token="):].strip()
                break

        if not token:
            print("No session_token cookie")
            return deny()

        # =========================
        # Load public key
        # =========================

        with open(PUBLIC_KEY_PATH, "r") as f:
            public_key = f.read()

        # =========================
        # Check JWT header
        # =========================

        unverified_header = jwt.get_unverified_header(token)


        if unverified_header.get("kid") != EXPECTED_KID:
            print("Invalid kid")
            return deny()

        if unverified_header.get("alg") != "RS256":
            print("Invalid algorithm")
            return deny()

        # =========================
        # Verify JWT
        # =========================

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"require": ["exp"]}
        )


        # =========================
        # Check expiration
        # =========================

        if payload.get("exp") is not None:

            if int(time.time()) >= int(payload["exp"]):
                print("Token expired")
                return deny()

        # =========================
        # Get user information
        # =========================

        username = payload.get("username")
        role = payload.get("role")
        # The login Lambda issues this claim as `user_type`.
        # Reading `type` here made the value disappear before it reached
        # protected APIs.
        user_type = payload.get("user_type")


        # =========================
        # Allow
        # =========================

        return allow(
            username=username,
            role=role,
            user_type=user_type,
        )

    except jwt.ExpiredSignatureError:

        print("JWT expired")
        return deny()

    except jwt.InvalidTokenError as e:

        print("Invalid JWT")
        return deny()

    except Exception as e:

        print("Authorizer internal error")
        return deny()


# =========================
# Allow
# =========================

def allow(username=None, role=None, user_type=None):

    return {
        "isAuthorized": True,
        "context": {
            "username": username or "",
            "role": role or "",
            "user_type": user_type or "",
        }
    }


# =========================
# Deny
# =========================

def deny():

    return {
        "isAuthorized": False
    }





