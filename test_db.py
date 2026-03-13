import asyncio
from sqlalchemy import select
from app.database import async_session_maker
from app.models import CoffeeShop

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(CoffeeShop.name, CoffeeShop.opening_hours).limit(5))
        for row in result:
            print(f"{row[0]}: {row[1]}")

asyncio.run(main())
