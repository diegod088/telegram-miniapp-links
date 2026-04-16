"""Security utilities — sanitization, URL validation, and antispam."""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse


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
