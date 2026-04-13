"""Telegram WebApp initData verification.

Implements the exact algorithm from:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs

from tglinktree.core.exceptions import AuthenticationError


def verify_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validate Telegram WebApp initData and return the parsed user dict.

    Steps:
    1. Parse query string → extract hash, auth_date, user JSON
    2. Reject if expired (> 86400 seconds)
    3. Build data-check-string: sorted key=value pairs (excluding hash)
    4. secret_key = HMAC-SHA256("WebAppData", bot_token)
    5. expected_hash = HMAC-SHA256(secret_key, data_check_string)
    6. Timing-safe comparison

    Returns:
        dict with keys: user (parsed JSON), auth_date, etc.

    Raises:
        AuthenticationError on any validation failure.
    """
    if not init_data:
        raise AuthenticationError("Missing initData")

    # 1. Parse query string
    parsed = parse_qs(init_data, keep_blank_values=True)

    # Extract hash
    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        raise AuthenticationError("Missing hash in initData")

    # Extract auth_date
    auth_date_str = parsed.get("auth_date", [None])[0]
    if not auth_date_str:
        raise AuthenticationError("Missing auth_date in initData")

    # 2. Reject if expired
    try:
        auth_date = int(auth_date_str)
    except ValueError:
        raise AuthenticationError("Invalid auth_date")

    if time.time() - auth_date > 86400:
        raise AuthenticationError("initData expired (older than 24 hours)")

    # 3. Build data-check-string
    # Flatten: each key has one value (take the first)
    data_pairs = []
    for key in sorted(parsed.keys()):
        if key == "hash":
            continue
        # parse_qs returns lists; join back if multiple values (shouldn't happen)
        value = parsed[key][0]
        data_pairs.append(f"{key}={value}")

    data_check_string = "\n".join(data_pairs)

    # 4. secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # 5. expected_hash = HMAC-SHA256(secret_key, data_check_string)
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # 6. Timing-safe comparison
    if not hmac.compare_digest(expected_hash, received_hash):
        raise AuthenticationError("Invalid initData signature")

    # Parse user JSON
    user_json_str = parsed.get("user", [None])[0]
    if not user_json_str:
        raise AuthenticationError("Missing user in initData")

    try:
        user_data = json.loads(user_json_str)
    except json.JSONDecodeError:
        raise AuthenticationError("Invalid user JSON in initData")

    return {
        "user": user_data,
        "auth_date": auth_date,
        "hash": received_hash,
        "raw": parsed,
    }
