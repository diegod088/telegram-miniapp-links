import asyncio
from app.db.session import async_session_factory
from app.services.discovery_service import DiscoveryService

async def test():
    async with async_session_factory() as db:
        service = DiscoveryService(db)
        res, _ = await service.get_profile_ranking("likes", None, 10, 0)
        p, likes = res[0]
        try:
            print("Trying hasattr...")
            has_l = hasattr(p, 'links')
            print("hasattr:", has_l)
        except Exception as e:
            print("Error:", type(e), e)

asyncio.run(test())
