import asyncio
import sys
from app.db.session import SessionLocal
from app.services.discovery_service import DiscoveryService

async def test():
    async with SessionLocal() as db:
        service = DiscoveryService(db)
        res, total = await service.get_profile_ranking("likes", None, 10, 0)
        print("Total profiles:", total)
        for p, likes in res:
            print(p.display_name, likes)

asyncio.run(test())
