import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import User, Base
from app.config import settings

async def seed_admin():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create tables if not exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        from app.security import get_password_hash
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if not user:
            new_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("Thuan1995@"),
                full_name="Administrator",
                is_active=True,
                is_superuser=True
            )
            session.add(new_user)
            await session.commit()
            print("Admin user created successfully!")
        else:
            user.hashed_password = get_password_hash("Thuan1995@")
            user.is_superuser = True
            await session.commit()
            print("Admin user updated successfully with hashed password!")

if __name__ == "__main__":
    asyncio.run(seed_admin())
