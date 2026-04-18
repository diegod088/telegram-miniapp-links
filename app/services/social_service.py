"""Social service — URL scrubbing, title scraping, and upvotes."""

from __future__ import annotations

import logging
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.link_repository import LinkRepository
from app.services.activity_service import ActivityService
from app.models.user import User

logger = logging.getLogger("app")

# Tracking parameters to scrub
SCRUB_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "pclid", "msclkid", "ref", "mc_cid", "mc_eid"
}


class SocialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.link_repo = LinkRepository(db)

    async def scrub_url(self, url: str) -> str:
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

    async def scrape_page_title(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Attempt to fetch og:title/title and og:image from a URL."""
        try:
            async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
                response = await client.get(url, headers={"User-Agent": "TGLinktree-Bot/1.0"})
                if response.status_code != 200:
                    return None, None
                
                html = response.text
                
                # 1. Try og:title and og:image
                title = None
                image = None
                
                og_title_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                if og_title_match:
                    title = og_title_match.group(1)
                
                og_image_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                if og_image_match:
                    image = og_image_match.group(1)
                
                # 2. Try <title> if og:title failed
                if not title:
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        title = re.sub(r'<[^>]+>', '', title_match.group(1).strip())
                    
                return title, image
        except Exception as e:
            logger.debug(f"Scraping failed for {url}: {e}")
            return None, None

    async def toggle_like(self, user_id: int, link_id: int) -> Tuple[int, bool]:
        """
        Toggle like for a link.
        Returns (new_likes_count, is_now_liked).
        """
        existing_like = await self.link_repo.get_like(user_id, link_id)
        
        link = await self.link_repo.get(link_id)
        if not link:
            raise ValueError("Link not found")

        is_now_liked = False
        if existing_like:
            # Remove like
            from app.models.link import LinkLike
            from sqlalchemy import delete
            stmt = delete(LinkLike).where(
                LinkLike.user_id == user_id, 
                LinkLike.link_id == link_id
            )
            await self.db.execute(stmt)
            link.likes = max(0, link.likes - 1)
            is_now_liked = False
            # Add like
            await self.link_repo.add_like(user_id, link_id)
            link.likes += 1
            is_now_liked = True
            
        if is_now_liked:
            # 3. Record Activity (Pulse)
            activity_svc = ActivityService(self.db)
            # Re-fetch user name if possible, or use generic
            user = await self.db.get(User, user_id)
            await activity_svc.record_activity(
                type="link_trending",
                message=f"{(user.first_name if user else 'Alguien')} le dio like a un enlace popular!",
                user_id=user_id,
                target_id=str(link_id),
                target_type="link"
            )

        await self.db.commit()
        return link.likes, is_now_liked

    async def toggle_dislike(self, user_id: int, link_id: int) -> Tuple[int, bool]:
        """
        Toggle dislike for a link.
        Returns (new_dislikes_count, is_now_disliked).
        """
        existing_dislike = await self.link_repo.get_dislike(user_id, link_id)
        
        link = await self.link_repo.get(link_id)
        if not link:
            raise ValueError("Link not found")

        is_now_disliked = False
        if existing_dislike:
            # Remove dislike
            from app.models.link import LinkDislike
            from sqlalchemy import delete
            stmt = delete(LinkDislike).where(
                LinkDislike.user_id == user_id, 
                LinkDislike.link_id == link_id
            )
            await self.db.execute(stmt)
            link.dislikes = max(0, link.dislikes - 1)
            is_now_disliked = False
        else:
            # Add dislike
            await self.link_repo.add_dislike(user_id, link_id)
            is_now_disliked = True
            
        await self.db.flush()
        return link.dislikes, is_now_disliked
