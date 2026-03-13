import asyncio
import json
from app.database import async_session_maker
from app.models import CoffeeShop
from sqlalchemy import select

async def main():
    async with async_session_maker() as s:
        res = await s.execute(select(CoffeeShop.opening_hours).where(CoffeeShop.opening_hours.isnot(None)).limit(10))
        print(json.dumps([r[0] for r in res.all()]))

asyncio.run(main())
