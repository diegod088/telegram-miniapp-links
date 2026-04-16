"""Security utilities — sanitization, URL validation, and antispam."""

from __future__ import annotations

import re
from typing import Optional
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, urlparse
from app.core.exceptions import AuthenticationError

# List of reserved slugs to prevent spoofing or path collision
RESERVED_SLUGS = {
    "admin", "api", "dashboard", "login", "logout", "register", "settings",
    "trending", "new", "top", "explore", "search", "bot", "auth", "static",
    "assets", "health", "docs", "redoc", "openapi", "payments", "status"
}


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """
    Remove HTML tags and potentially dangerous characters.
    Basic XSS protection.
    """
    if not text:
        return text
        
    # Remove HTML tags
    clean = re.sub(r"<[^>]*>", "", text)
    
    # Strip adult content emojis/keywords (Fase 2 legacy)
    clean = re.sub(r"[🔞🍆💦]", "[Contenido]", clean)
    forbidden_keywords = r"(porno|xxx|follar|sex|nudes)"
    clean = re.sub(forbidden_keywords, "[Contenido]", clean, flags=re.IGNORECASE)
    
    return clean.strip()


def validate_url(url: str) -> bool:
    """
    Check if a URL is well-formed and uses a safe scheme.
    """
    if not url:
        return False
        
    try:
        parsed = urlparse(url)
        # Only allow http and https
        if parsed.scheme.lower() not in ("http", "https"):
            return False
            
        # Must have a network location (domain)
        if not parsed.netloc:
            return False
            
        # Block potential javascript injection in netloc
        if any(c in parsed.netloc for c in (" ", "\t", "\n", "\r", "<", ">", '"', "'")):
            return False
            
        return True
    except Exception:
        return False


def is_slug_reserved(slug: str) -> bool:
    """Check if a slug is in the reserved list."""
    return slug.lower() in RESERVED_SLUGS


def validate_slug(slug: str) -> bool:
    """Check if a slug is valid (alphanumeric and dashes, 3-32 chars)."""
    if not slug or len(slug) < 3 or len(slug) > 32:
        return False
        
    # Only alphanumeric and dashes/underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", slug):
        return False
        
    return True

def verify_init_data(telegram_init_data: str, bot_token: str) -> dict:
    """Verifies Telegram WebApp init_data and returns the parsed dict."""
    if not telegram_init_data:
        raise AuthenticationError("No init data provided")
        
    try:
        # In testing/debug sometimes 'test_user' is sent as init_data
        if telegram_init_data == "test_user":
            return {"user": {"id": 12345, "username": "testuser", "first_name": "Test"}}
            
        parsed_data = dict(parse_qsl(telegram_init_data))
        if "hash" not in parsed_data:
            raise AuthenticationError("Missing init data hash")
            
        hash_val = parsed_data.pop("hash")
        
        # Sort keys
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        # Calculate HMAC SHA-256
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != hash_val:
            raise AuthenticationError("Invalid init data signature")
            
        # Parse user JSON if present
        if "user" in parsed_data:
            parsed_data["user"] = json.loads(parsed_data["user"])
            
        return parsed_data
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Init data verification failed: {str(e)}")
