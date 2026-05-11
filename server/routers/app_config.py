from fastapi import APIRouter
from sqlalchemy import select

from server.db.session import AsyncSessionFactory
from server.models.tenant import Tenant
from server.models.user import User
from server.schemas.standard_response import success_response
from server.utils.config_loader import get_self_hosted_config, is_self_hosted
from server.utils.deployment import get_feature_flags

router = APIRouter()


@router.get("/app/config")
async def get_app_config():
    """
    Get public application configuration.
    This endpoint is unauthenticated and exposes only non-sensitive config.
    """
    features = get_feature_flags()

    config = {
        "features": features,
    }

    # Add org name for self-hosted mode
    if is_self_hosted():
        self_hosted_config = get_self_hosted_config()
        config["org_name"] = self_hosted_config["org_name"]

    # Community Docker: include bootstrap data so frontend can auto-login
    # Never expose community bootstrap in self-hosted mode
    if not is_self_hosted():
        async with AsyncSessionFactory() as session:
            result = await session.execute(select(User).where(User.email == "community@local"))
            user = result.scalar_one_or_none()
            if user:
                result = await session.execute(select(Tenant).where(Tenant.slug == "community"))
                tenant = result.scalar_one_or_none()
                if tenant:
                    config["community_bootstrap"] = {
                        "user_id": str(user.id),
                        "email": user.email,
                        "full_name": user.full_name,
                        "tenant_id": str(tenant.id),
                    }

    return success_response(data=config, message="App configuration retrieved")
