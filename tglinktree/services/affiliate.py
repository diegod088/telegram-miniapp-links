"""Affiliate service — detects domains and appends affiliate tags."""

from __future__ import annotations

import logging
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from tglinktree.config import get_settings

logger = logging.getLogger("tglinktree")

def get_affiliate_url(url: str) -> str:
    """
    Detects if the URL belongs to a supported merchant and appends the affiliate tag.
    Returns the modified URL or the original one.
    """
    settings = get_settings()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # 1. Amazon
    if "amazon." in domain:
        if settings.AFFILIATE_TAG_AMAZON:
            return _append_param(url, "tag", settings.AFFILIATE_TAG_AMAZON)
            
    # 2. AliExpress
    if "aliexpress." in domain:
        if settings.AFFILIATE_TAG_ALIEXPRESS:
            return _append_param(url, "aff_id", settings.AFFILIATE_TAG_ALIEXPRESS)
            
    # 3. Temu
    if "temu.com" in domain:
        if settings.AFFILIATE_TAG_TEMU:
            return _append_param(url, "affiliate_id", settings.AFFILIATE_TAG_TEMU)
            
    # 4. Shein
    if "shein.com" in domain:
        if settings.AFFILIATE_TAG_SHEIN:
            return _append_param(url, "aff_id", settings.AFFILIATE_TAG_SHEIN)
            
    # 5. Terabox
    if "terabox.com" in domain:
        if settings.AFFILIATE_TAG_TERABOX:
            return _append_param(url, "affid", settings.AFFILIATE_TAG_TERABOX)

    # 6. Streamtape
    if "streamtape.com" in domain:
        if settings.AFFILIATE_TAG_STREAMTAPE:
            return _append_param(url, "affid", settings.AFFILIATE_TAG_STREAMTAPE)

    # 7. Doodstream
    if "doodstream.com" in domain:
        if settings.AFFILIATE_TAG_DOODSTREAM:
            return _append_param(url, "affid", settings.AFFILIATE_TAG_DOODSTREAM)

    # 8. Voe.sx
    if "voe.sx" in domain:
        if settings.AFFILIATE_TAG_VOE_SX:
            return _append_param(url, "affid", settings.AFFILIATE_TAG_VOE_SX)
            
    return url

def _append_param(url: str, key: str, value: str) -> str:
    """Helper to append a query parameter to a URL."""
    try:
        parsed = urlparse(url)
        params = dict(parse_qsl(parsed.query))
        params[key] = value
        new_query = urlencode(params)
        return urlunparse(parsed._replace(query=new_query))
    except Exception as e:
        logger.warning(f"Error appending param to {url}: {e}")
        return url
