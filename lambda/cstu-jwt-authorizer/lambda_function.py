import json
import time
import jwt


# =========================
# Configuration
# =========================

PUBLIC_KEY_PATH = "/var/task/public.pem"

EXPECTED_KID = "d47c0efedabc6b33"


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    try:

        # =========================
        # Get Authorization header
        # =========================

        headers = event.get("headers") or {}

        authorization = (
            headers.get("authorization")
            or headers.get("Authorization")
        )

        if not authorization:
            print("No Authorization header")
            return deny()

        # =========================
        # Check Bearer token
        # =========================

        if not authorization.startswith("Bearer "):
            print("Invalid Authorization format")
            return deny()

        token = authorization[7:].strip()

        if not token:
            print("Empty token")
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

        print("JWT header:", unverified_header)

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
            algorithms=["RS256"]
        )

        print("JWT payload:", payload)

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
        user_type = payload.get("type")

        print("Authenticated user:", username)
        print("Role:", role)
        print("Type:", user_type)

        # =========================
        # Allow
        # =========================

        return allow(
            username=username,
            role=role
        )

    except jwt.ExpiredSignatureError:

        print("JWT expired")
        return deny()

    except jwt.InvalidTokenError as e:

        print("Invalid JWT:", str(e))
        return deny()

    except Exception as e:

        print("ERROR:", str(e))
        return deny()


# =========================
# Allow
# =========================

def allow(username=None, role=None):

    return {
        "isAuthorized": True,
        "context": {
            "username": username or "",
            "role": role or ""
        }
    }


# =========================
# Deny
# =========================

def deny():

    return {
        "isAuthorized": False
    }
