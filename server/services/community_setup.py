import asyncio
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from server.db.session import AsyncSessionFactory
from server.models.tenant import Tenant
from server.models.tenant_member import TenantMember, TenantRole
from server.models.user import User
from server.utils.custom_logger import get_logger
from server.utils.seed_notebook import seed_demo_notebooks_for_user

logger = get_logger(__name__)

COMMUNITY_EMAIL = "community@local"
COMMUNITY_TENANT_NAME = "Community"
COMMUNITY_TENANT_SLUG = "community"


async def setup_community_environment() -> None:
    """
    Initialize a community Docker environment with a default user and tenant.
    No authentication required — provides the same single-user experience as the Mac app.
    Idempotent — skips creation if entities already exist.
    """
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.email == COMMUNITY_EMAIL))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            result = await session.execute(select(Tenant).where(Tenant.owner_id == existing_user.id))
            if result.scalar_one_or_none():
                return

            user = existing_user
        else:
            user = User(
                id=uuid4(),
                email=COMMUNITY_EMAIL,
                hashed_password="community-no-auth",
                is_active=True,
                is_verified=True,
                is_superuser=True,
                full_name="Community User",
            )
            session.add(user)
            await session.flush()

        result = await session.execute(select(Tenant).where(Tenant.slug == COMMUNITY_TENANT_SLUG))
        if not result.scalar_one_or_none():
            tenant = Tenant(
                id=uuid4(),
                name=COMMUNITY_TENANT_NAME,
                slug=COMMUNITY_TENANT_SLUG,
                owner_id=user.id,
                is_personal=True,
            )
            session.add(tenant)
            await session.flush()

            member = TenantMember(
                id=uuid4(),
                user_id=user.id,
                tenant_id=tenant.id,
                role=TenantRole.OWNER.value,
                joined_at=datetime.utcnow(),
            )
            session.add(member)

            await session.commit()
            logger.info("Community environment ready (single-user, no auth)")

            user_id_copy = user.id
            tenant_id_copy = tenant.id

            async def seed_in_background():
                try:
                    async with AsyncSessionFactory() as seed_session:
                        await seed_demo_notebooks_for_user(seed_session, user_id_copy, tenant_id_copy)
                except Exception as e:
                    logger.error(f"Failed to seed demo notebooks: {e}")

            asyncio.create_task(seed_in_background())
