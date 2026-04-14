"""Social service — URL scrubbing, title scraping, and upvotes."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import httpx
from sqlalchemy import select, func, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tglinktree.models.link import ProfileLink, LinkUpvote
from tglinktree.models.user import User

logger = logging.getLogger("tglinktree")

# Tracking parameters to scrub
SCRUB_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "pclid", "msclkid", "ref", "mc_cid", "mc_eid"
}

async def scrub_url(url: str) -> str:
    """Remove tracking parameters from a URL."""
    try:
        parsed = urlparse(url)
        query_params = parse_qsl(parsed.query)
        clean_params = [(k, v) for k, v in query_params if k.lower() not in SCRUB_PARAMS]
        
        new_query = urlencode(clean_params)
        return urlunparse(parsed._replace(query=new_query))
    except Exception as e:
        logger.warning(f"Error scrubbing URL {url}: {e}")
        return url

async def scrape_page_title(url: str) -> Optional[str]:
    """
    Attempt to fetch og:title or <title> from a URL.
    Timeout: 3s.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "TGLinktree-Bot/1.0"})
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # 1. Try og:title
            og_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if og_match:
                return og_match.group(1)
            
            # 2. Try <title>
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                # Clean up nested tags if any
                return re.sub(r'<[^>]+>', '', title)
                
            return None
    except Exception as e:
        logger.debug(f"Scraping failed for {url}: {e}")
        return None

async def toggle_upvote(db: AsyncSession, user_id: int, link_id: int) -> Tuple[int, bool]:
    """
    Toggle upvote for a link. 
    Returns (new_upvotes_count, is_now_upvoted).
    """
    # 1. Check if upvote exists
    stmt = select(LinkUpvote).where(LinkUpvote.user_id == user_id, LinkUpvote.link_id == link_id)
    result = await db.execute(stmt)
    upvote = result.scalar_one_or_none()
    
    is_upvoted = False
    
    # 2. Fetch the link to update its counter
    link_stmt = select(ProfileLink).where(ProfileLink.id == link_id).with_for_update()
    link_result = await db.execute(link_stmt)
    link = link_result.scalar_one_or_none()
    
    if not link:
        raise ValueError("Link not found")

    if upvote:
        # Remove upvote
        await db.delete(upvote)
        link.upvotes = max(0, link.upvotes - 1)
        is_upvoted = False
    else:
        # Add upvote
        new_upvote = LinkUpvote(user_id=user_id, link_id=link_id)
        db.add(new_upvote)
        link.upvotes += 1
        is_upvoted = True
        
    await db.flush()
    return link.upvotes, is_upvoted

def get_explore_score_expr():
    """
    Returns the SQL expression for ranking links.
    Score = (upvotes * 1.5 * boost) / POWER(T / 3600 + 2, 1.5)
    """
    from tglinktree.models.profile import Profile
    
    # PostgreSQL specific formula + Boost
    return (ProfileLink.upvotes * 1.5 * Profile.boost_score) / func.pow(
        (func.extract('epoch', func.now() - ProfileLink.created_at) / 3600) + 2,
        1.5
    )
