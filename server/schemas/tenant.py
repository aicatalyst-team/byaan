from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_serializer

# ==================== User Info (for joins) ====================


class UserInfo(BaseModel):
    """Basic user info for display in member/invitation responses."""

    id: UUID
    email: str
    full_name: str | None = None

    model_config = {
        "from_attributes": True,
    }


# ==================== Tenant Invitation Schemas ====================


class InvitationCreate(BaseModel):
    """Request schema for creating a new invitation."""

    email: EmailStr
    role: str  # "admin" or "member"
    message: str | None = None  # Optional personal message


class InvitationRead(BaseModel):
    """Response schema for invitation details."""

    id: UUID
    tenant_id: UUID
    email: str
    role: str
    invited_by_id: UUID
    token_id: UUID
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime
    invited_by: UserInfo | None = None
    invitation_link: str | None = None

    @field_serializer("expires_at", "accepted_at", "created_at")
    def serialize_datetime(self, dt: datetime | None, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()

    model_config = {
        "from_attributes": True,
    }


class InvitationListResponse(BaseModel):
    """Response schema for listing invitations."""

    items: list[InvitationRead]
    total: int


# ==================== Tenant Member Schemas ====================


class MemberRead(BaseModel):
    """Response schema for tenant member details."""

    id: UUID
    user_id: UUID
    tenant_id: UUID
    role: str
    invited_at: datetime | None = None
    joined_at: datetime | None = None
    created_at: datetime
    user: UserInfo | None = None

    @field_serializer("invited_at", "joined_at", "created_at")
    def serialize_datetime(self, dt: datetime | None, _info):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()

    model_config = {
        "from_attributes": True,
    }


class MemberListResponse(BaseModel):
    """Response schema for listing members."""

    items: list[MemberRead]
    total: int


class UpdateMemberRoleRequest(BaseModel):
    """Request schema for updating member role."""

    role: str  # "owner", "admin", or "member"


# ==================== Tenant Schemas ====================


class TenantRead(BaseModel):
    """Response schema for tenant details."""

    id: UUID
    name: str
    slug: str
    owner_id: UUID
    is_personal: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TenantCreate(BaseModel):
    """Request schema for creating a new tenant."""

    name: str


class TenantUpdate(BaseModel):
    """Request schema for updating tenant details."""

    name: str | None = None


# ==================== Accept Invitation ====================


class AcceptInvitationRequest(BaseModel):
    """Request schema for accepting an invitation."""

    token: str
