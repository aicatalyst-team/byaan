export type TenantRole = 'owner' | 'admin' | 'member' | 'viewer'

export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'revoked'

export interface TenantMember {
  id: string
  user_id: string
  tenant_id: string
  role: TenantRole
  invited_at: string | null
  joined_at: string | null
  created_at: string
  // User details (from join)
  user?: {
    id: string
    email: string
    full_name?: string
    is_active: boolean
  }
}

export interface TenantInvitation {
  id: string
  tenant_id: string
  email: string
  role: Exclude<TenantRole, 'owner'> // Can only invite as admin or member
  invited_by_id: string
  token_id: string
  status: InvitationStatus
  expires_at: string
  accepted_at: string | null
  created_at: string
  // Invited by details (from join)
  invited_by?: {
    id: string
    email: string
    full_name?: string
  }
  invitation_link?: string
}

export interface InviteMemberRequest {
  email: string
  role: Exclude<TenantRole, 'owner'> // admin or member only
  message?: string // Optional personal message
}

export interface UpdateMemberRoleRequest {
  role: TenantRole
}

export interface ResendInvitationRequest {
  invitation_id: string
}
