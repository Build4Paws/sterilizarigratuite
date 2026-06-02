import type { Species } from './campaign'

/**
 * Campaign lifecycle as the BACKEND/DB models it (lowercase) — distinct from the
 * public-facing `CampaignStatus` in `campaign.ts` (uppercase, presentation-only).
 * The admin works in the DB's terms. See docs/BACKEND-SCHEMA.md `campaign_status`.
 */
export type AdminCampaignStatus = 'pending' | 'approved' | 'rejected' | 'cancelled' | 'finished'

/** Citizen lifecycle (DB `citizen_status`). */
export type CitizenStatus = 'pending_confirm' | 'active' | 'unsubscribed' | 'deleted'

/** Identity returned by GET /api/admin/auth/me. */
export interface AdminMe {
  email: string
  groups: string[]
}

/** Dashboard overview tiles (GET /api/admin/stats/overview). */
export interface AdminOverview {
  pendingCampaigns: number
  approvedUpcoming: number
  citizensActive: number
  registrationsToday: number
  byStatus: Partial<Record<AdminCampaignStatus, number>>
}

// --- Campaigns ---

/** Row shape for the moderation list (GET /api/admin/campaigns). */
export interface AdminCampaign {
  submissionId: string
  organizationName: string
  county: string
  countyName: string
  locality: string
  dateStart: string
  dateEnd: string | null
  status: AdminCampaignStatus
  createdAt: string
  reviewedAt?: string | null
  reviewedBy?: string | null
}

/** Full detail (GET /api/admin/campaigns/{id}) — includes private contact + audit fields. */
export interface AdminCampaignDetail extends AdminCampaign {
  phonePublic: string
  address: string
  timeStart: string
  timeEnd: string
  doctor: string | null
  species: Partial<Record<Species, number>>
  contactEmail: string
  contactPhone: string
  rejectionReason?: string | null
  submittedIp?: string | null
  submittedUa?: string | null
}

export interface AdminCampaignList {
  campaigns: AdminCampaign[]
  total: number
}

// --- Citizens (PII — minimized) ---

/** Minimized list row — NO raw phone/email; just which channels exist. */
export interface AdminCitizenRow {
  citizenId: string
  name: string
  countyName: string
  locality: string
  status: CitizenStatus
  channelMask: { phone: boolean; email: boolean }
  createdAt: string
}

/** Detail — phone/email present (access is audited backend-side). */
export interface AdminCitizenDetail extends AdminCitizenRow {
  phone: string | null
  email: string | null
  species: Partial<Record<Species, number>>
  gdprConsentAt: string
  notes: string | null
}

export interface AdminCitizenList {
  citizens: AdminCitizenRow[]
  total: number
}

// --- Organizers ---

export interface AdminOrganizer {
  organizerId: string
  name: string
  contactEmail: string
  contactPhone: string
  campaignCount: number
  createdAt: string
}

export interface AdminOrganizerDetail extends AdminOrganizer {
  notes: string | null
  campaigns: AdminCampaign[]
}

export interface AdminOrganizerList {
  organizers: AdminOrganizer[]
  total: number
}

// --- Audit log ---

export interface AuditEntry {
  id: number
  occurredAt: string
  actor: string | null
  action: string
  entityType: string
  entityId: number | null
  ipAddress?: string | null
  metadata?: Record<string, unknown> | null
}

export interface AuditList {
  entries: AuditEntry[]
  total: number
}
