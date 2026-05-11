from __future__ import annotations

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from server.db.session import AsyncSessionFactory
from server.models.tenant_invitation import InvitationStatus, TenantInvitation
from server.models.tenant_member import TenantMember, TenantRole
from server.models.user import User
from server.models.verification_token import VerificationToken
from server.repositories.tenant import TenantRepository
from server.repositories.tenant_invitation import TenantInvitationRepository
from server.repositories.tenant_member import TenantMemberRepository
from server.services.email_service import EmailService, SMTPEmailService
from server.utils.config_loader import get_email_config, get_smtp_config
from server.utils.custom_logger import get_logger
from server.utils.seed_notebook import seed_demo_notebooks_for_user

logger = get_logger(__name__)


def _get_email_service() -> EmailService | SMTPEmailService | None:
    """
    Get email service based on configuration priority:
    1. SMTP (if configured) - for self-hosted deployments
    2. Resend API (if configured) - for deployments using Resend service
    3. None - if neither configured
    """
    smtp_config = get_smtp_config()
    if smtp_config:
        return SMTPEmailService(
            smtp_host=smtp_config["smtp_host"],
            smtp_port=smtp_config["smtp_port"],
            smtp_username=smtp_config["smtp_username"],
            smtp_password=smtp_config["smtp_password"],
            smtp_from_email=smtp_config["smtp_from_email"],
            smtp_from_name=smtp_config["smtp_from_name"],
            smtp_use_tls=smtp_config["smtp_use_tls"],
        )

    email_config = get_email_config()
    if email_config["api_key"]:
        return EmailService(api_key=email_config["api_key"], from_email=email_config["from_email"])

    return None


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class TenantService:
    """Service for managing tenant invitations and members."""

    @staticmethod
    async def send_invitation(
        tenant_id: UUID,
        email: str,
        role: str,
        invited_by_id: UUID,
        session: AsyncSession,
        message: str | None = None,
        base_url: str | None = None,
    ) -> tuple[TenantInvitation, str]:
        """
        Send an invitation to join a tenant.

        Args:
            tenant_id: The tenant ID to invite to
            email: The email address to invite
            role: The role to assign (admin or member)
            invited_by_id: The user ID sending the invitation
            session: Database session
            message: Optional personal message
            base_url: Optional base URL for the invitation link (from request origin)

        Returns:
            Tuple of (invitation, invitation_link)

        Raises:
            HTTPException: If validation fails
        """
        # Validate role
        if role not in ["admin", "member", "viewer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Can only invite as 'admin', 'member', or 'viewer'.",
            )

        # Get repositories
        tenant_repo = TenantRepository(session)
        invitation_repo = TenantInvitationRepository(session)
        member_repo = TenantMemberRepository(session)

        # Check tenant exists
        tenant = await tenant_repo.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Check if user is already a member
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            existing_membership = await member_repo.get_membership(str(existing_user.id), str(tenant_id))
            if existing_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This user is already a member of the organization",
                )

        # Check if pending invitation already exists
        existing_invitation = await invitation_repo.get_by_email_and_tenant(email, tenant_id)
        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user already has a pending invitation",
            )

        # Generate token
        token = generate_token()
        token_hash_value = hash_token(token)

        # Create verification token
        verification_token = VerificationToken(
            user_id=invited_by_id,  # Associate with inviter for now
            token_hash=token_hash_value,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        session.add(verification_token)
        await session.flush()  # Get ID without committing

        # Create invitation
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            invited_by_id=invited_by_id,
            token_id=verification_token.id,
            status=InvitationStatus.PENDING.value,
            plain_token=token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)

        # Load relationships
        await session.refresh(invitation, ["tenant", "invited_by"])

        # Send invitation email
        email_service = _get_email_service()
        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service is not configured. Cannot send invitation.",
            )

        config = get_email_config()
        frontend_url = base_url or config["frontend_url"]
        invitation_link = f"{frontend_url}/accept-invitation?token={token}"

        inviter_name = invitation.invited_by.full_name or invitation.invited_by.email

        try:
            result = await email_service.send_invitation_email(
                to_email=email,
                invitation_link=invitation_link,
                tenant_name=tenant.name,
                inviter_name=inviter_name,
                role=role,
            )
            if result.get("success"):
                logger.info(f"Invitation email sent successfully to {email} for tenant {tenant.name}")
            else:
                error_detail = result.get("error", "Unknown error")
                logger.error(f"Failed to send invitation email to {email}: {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to send invitation email: {error_detail}",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending invitation email to {email}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send invitation email: {str(e)}",
            )

        return invitation, invitation_link

    @staticmethod
    async def verify_invitation_token(token: str, session: AsyncSession) -> dict:
        """
        Verify an invitation token and return basic info without accepting it.

        Args:
            token: The invitation token
            session: Database session

        Returns:
            Dict with invitation email, tenant name, and whether user exists

        Raises:
            HTTPException: If token is invalid or expired
        """
        token_hash_value = hash_token(token)

        # Find verification token
        result = await session.execute(
            select(VerificationToken).where(VerificationToken.token_hash == token_hash_value)
        )
        verification_token = result.scalar_one_or_none()

        if not verification_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation link",
            )

        if verification_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation link has expired",
            )

        if verification_token.verified_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation link has already been used",
            )

        # Find invitation
        invitation_repo = TenantInvitationRepository(session)
        invitation = await invitation_repo.get_by_token_id(verification_token.id)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation not found",
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation is {invitation.status}",
            )

        # Check if user exists
        result = await session.execute(select(User).where(User.email == invitation.email))
        user = result.scalar_one_or_none()

        # Load tenant info
        await session.refresh(invitation, ["tenant"])

        return {
            "email": invitation.email,
            "tenant_name": invitation.tenant.name,
            "tenant_id": str(invitation.tenant_id),
            "role": invitation.role,
            "user_exists": user is not None,
            "user_verified": user.is_verified if user else False,
        }

    @staticmethod
    async def accept_invitation(token: str, session: AsyncSession) -> dict:
        """
        Accept an invitation and create tenant membership.

        Args:
            token: The invitation token
            session: Database session

        Returns:
            Dict with success status and member info

        Raises:
            HTTPException: If token is invalid or expired
        """
        token_hash_value = hash_token(token)

        # Find verification token
        result = await session.execute(
            select(VerificationToken).where(VerificationToken.token_hash == token_hash_value)
        )
        verification_token = result.scalar_one_or_none()

        if not verification_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invitation link",
            )

        if verification_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation link has expired",
            )

        if verification_token.verified_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation link has already been used",
            )

        # Find invitation
        invitation_repo = TenantInvitationRepository(session)
        invitation = await invitation_repo.get_by_token_id(verification_token.id)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation not found",
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation is {invitation.status}",
            )

        # Check if user exists
        result = await session.execute(select(User).where(User.email == invitation.email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account not found. Please register first.",
            )

        # Check if already a member (race condition protection)
        member_repo = TenantMemberRepository(session)
        existing_membership = await member_repo.get_membership(str(user.id), str(invitation.tenant_id))
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this tenant",
            )

        # Create tenant membership
        member = TenantMember(
            user_id=user.id,
            tenant_id=invitation.tenant_id,
            role=invitation.role,
            invited_at=invitation.created_at,
            joined_at=datetime.utcnow(),
        )
        session.add(member)

        # Mark invitation as accepted
        invitation.status = InvitationStatus.ACCEPTED.value
        invitation.accepted_at = datetime.utcnow()

        # Mark token as verified
        verification_token.verified_at = datetime.utcnow()

        await session.commit()
        await session.refresh(member)

        logger.info(f"User {user.email} accepted invitation to tenant {invitation.tenant_id}")

        # Seed demo notebooks in background for the accepting user
        tenant_id_copy = invitation.tenant_id
        accepting_user_id = user.id

        async def seed_in_background():
            try:
                async with AsyncSessionFactory() as seed_session:
                    await seed_demo_notebooks_for_user(seed_session, accepting_user_id, tenant_id_copy)
            except Exception as e:
                logger.error(f"Failed to seed demo notebooks for user {accepting_user_id}: {e}")

        asyncio.create_task(seed_in_background())

        return {
            "success": True,
            "member_id": str(member.id),
            "tenant_id": str(member.tenant_id),
            "role": member.role,
        }

    @staticmethod
    async def resend_invitation(
        invitation_id: UUID, session: AsyncSession, base_url: str | None = None
    ) -> tuple[TenantInvitation, str]:
        """
        Resend an invitation email.

        Args:
            invitation_id: The invitation ID
            session: Database session
            base_url: Optional base URL for the invitation link (from request origin)

        Returns:
            Tuple of (invitation, invitation_link)

        Raises:
            HTTPException: If invitation not found or not pending
        """
        invitation_repo = TenantInvitationRepository(session)
        invitation = await invitation_repo.get(invitation_id)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resend invitation with status: {invitation.status}",
            )

        # Generate new token
        token = generate_token()
        token_hash_value = hash_token(token)

        # Update verification token
        result = await session.execute(select(VerificationToken).where(VerificationToken.id == invitation.token_id))
        verification_token = result.scalar_one_or_none()

        if verification_token:
            verification_token.token_hash = token_hash_value
            verification_token.expires_at = datetime.utcnow() + timedelta(days=7)
        else:
            # Create new verification token if missing
            verification_token = VerificationToken(
                user_id=invitation.invited_by_id,
                token_hash=token_hash_value,
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            session.add(verification_token)
            await session.flush()
            invitation.token_id = verification_token.id

        # Update invitation expiration and store plain token
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation.plain_token = token

        await session.commit()
        await session.refresh(invitation)

        # Load relationships
        await session.refresh(invitation, ["tenant", "invited_by"])

        # Resend email
        email_service = _get_email_service()
        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email service is not configured. Cannot resend invitation.",
            )

        config = get_email_config()
        frontend_url = base_url or config["frontend_url"]
        invitation_link = f"{frontend_url}/accept-invitation?token={token}"

        inviter_name = invitation.invited_by.full_name or invitation.invited_by.email

        try:
            result = await email_service.send_invitation_email(
                to_email=invitation.email,
                invitation_link=invitation_link,
                tenant_name=invitation.tenant.name,
                inviter_name=inviter_name,
                role=invitation.role,
            )
            if result.get("success"):
                logger.info(f"Invitation email resent successfully to {invitation.email}")
            else:
                error_detail = result.get("error", "Unknown error")
                logger.error(f"Failed to resend invitation email to {invitation.email}: {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to resend invitation email: {error_detail}",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error resending invitation email to {invitation.email}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resend invitation email: {str(e)}",
            )

        return invitation, invitation_link

    @staticmethod
    async def get_invitation_link(
        invitation_id: UUID, session: AsyncSession, base_url: str | None = None
    ) -> tuple[TenantInvitation, str]:
        """
        Return the existing invitation link if the token is still valid,
        otherwise regenerate the token, send a new email, and return the new link.

        Args:
            invitation_id: The invitation ID
            session: Database session
            base_url: Optional base URL for the invitation link (from request origin)

        Returns:
            Tuple of (invitation, invitation_link)

        Raises:
            HTTPException: If invitation not found or not pending
        """
        invitation_repo = TenantInvitationRepository(session)
        invitation = await invitation_repo.get(invitation_id)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot get link for invitation with status: {invitation.status}",
            )

        config = get_email_config()
        frontend_url = base_url or config["frontend_url"]

        if invitation.plain_token and invitation.expires_at > datetime.utcnow():
            invitation_link = f"{frontend_url}/accept-invitation?token={invitation.plain_token}"
            return invitation, invitation_link

        token = generate_token()
        token_hash_value = hash_token(token)

        result = await session.execute(select(VerificationToken).where(VerificationToken.id == invitation.token_id))
        verification_token = result.scalar_one_or_none()

        if verification_token:
            verification_token.token_hash = token_hash_value
            verification_token.expires_at = datetime.utcnow() + timedelta(days=7)
        else:
            verification_token = VerificationToken(
                user_id=invitation.invited_by_id,
                token_hash=token_hash_value,
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            session.add(verification_token)
            await session.flush()
            invitation.token_id = verification_token.id

        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation.plain_token = token

        await session.commit()
        await session.refresh(invitation)
        await session.refresh(invitation, ["tenant", "invited_by"])

        invitation_link = f"{frontend_url}/accept-invitation?token={token}"

        email_service = _get_email_service()
        if email_service:
            inviter_name = invitation.invited_by.full_name or invitation.invited_by.email
            try:
                await email_service.send_invitation_email(
                    to_email=invitation.email,
                    invitation_link=invitation_link,
                    tenant_name=invitation.tenant.name,
                    inviter_name=inviter_name,
                    role=invitation.role,
                )
                logger.info(f"Regenerated token and resent invitation email to {invitation.email}")
            except Exception as e:
                logger.error(f"Failed to send email after token regeneration: {str(e)}")

        return invitation, invitation_link

    @staticmethod
    async def revoke_invitation(invitation_id: UUID, session: AsyncSession) -> TenantInvitation:
        """
        Revoke a pending invitation.

        Args:
            invitation_id: The invitation ID
            session: Database session

        Returns:
            The updated invitation

        Raises:
            HTTPException: If invitation not found or not pending
        """
        invitation_repo = TenantInvitationRepository(session)
        invitation = await invitation_repo.get(invitation_id)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revoke invitation with status: {invitation.status}",
            )

        invitation.status = InvitationStatus.REVOKED.value
        await session.commit()
        await session.refresh(invitation)

        logger.info(f"Invitation {invitation_id} revoked")

        return invitation

    @staticmethod
    async def list_members_with_users(tenant_id: UUID, session: AsyncSession) -> list[TenantMember]:
        """
        List all members of a tenant with user details.

        Args:
            tenant_id: The tenant ID
            session: Database session

        Returns:
            List of tenant members with user relationships loaded
        """
        result = await session.execute(
            select(TenantMember)
            .where(TenantMember.tenant_id == tenant_id)
            .options(selectinload(TenantMember.user))
            .order_by(TenantMember.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_member_role(
        member_id: UUID,
        new_role: str,
        tenant_id: UUID,
        current_user_id: UUID,
        current_user_role: TenantRole,
        session: AsyncSession,
    ) -> TenantMember:
        """
        Update a member's role.

        Args:
            member_id: The member ID
            new_role: The new role (admin or member)
            tenant_id: The tenant ID (for verification)
            current_user_id: The ID of the user making the change
            current_user_role: The role of the user making the change
            session: Database session

        Returns:
            The updated member with user relationship loaded

        Raises:
            HTTPException: If member not found, role invalid, or permission denied
        """
        # Validate role
        if new_role not in [TenantRole.ADMIN.value, TenantRole.MEMBER.value, TenantRole.VIEWER.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Can only assign 'admin', 'member', or 'viewer'.",
            )

        member_repo = TenantMemberRepository(session)
        member = await member_repo.get(member_id)

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )

        if member.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Member does not belong to this tenant",
            )

        # Owner's role cannot be changed by anyone
        if member.role == TenantRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner's role cannot be changed",
            )

        # Admins cannot change their own role
        if current_user_role == TenantRole.ADMIN and member.user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot change their own role",
            )

        member.role = new_role
        await session.commit()
        await session.refresh(member)

        logger.info(f"Member {member_id} role updated to {new_role}")

        # Eagerly load the user relationship to avoid lazy-loading issues
        result = await session.execute(
            select(TenantMember).where(TenantMember.id == member_id).options(joinedload(TenantMember.user))
        )
        member_with_user = result.scalar_one()

        return member_with_user

    @staticmethod
    async def remove_member(
        member_id: UUID, tenant_id: UUID, current_user_id: UUID, current_user_role: TenantRole, session: AsyncSession
    ) -> None:
        """
        Remove a member from a tenant.

        Role-based restrictions:
        - Owner: Can remove admins and members (but not themselves)
        - Admin: Can remove other admins and members (but not themselves)

        Args:
            member_id: The member ID
            tenant_id: The tenant ID (for verification)
            current_user_id: The ID of the user performing the removal
            current_user_role: Role of the user performing the removal
            session: Database session

        Raises:
            HTTPException: If member not found or removal not allowed
        """
        member_repo = TenantMemberRepository(session)
        member = await member_repo.get(member_id)

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )

        if member.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Member does not belong to this tenant",
            )

        member_role = TenantRole(member.role)

        # Rule 1: Owner cannot be removed by anyone
        if member_role == TenantRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner cannot be removed from the tenant",
            )

        # Rule 2: Users cannot remove themselves (including admins)
        if member.user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot remove yourself from the tenant",
            )

        # All checks passed, proceed with removal
        await member_repo.delete(member_id)
        logger.info(f"Member {member_id} removed from tenant {tenant_id}")
