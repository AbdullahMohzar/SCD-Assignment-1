/** Municipal service categories mapped to city departments */
export type Category = 'water' | 'electricity' | 'sanitation' | 'roads' | 'streetlights' | 'other';

/** Triage priority levels computed by AI model */
export type Priority = 'high' | 'normal' | 'low';

/** Lifecycle status for ticket state machine (open -> in_progress -> resolved/rejected) */
export type Status = 'open' | 'in_progress' | 'resolved' | 'rejected';

/** Payload submitted by citizens via web form */
export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string;
}

export interface ComplaintResponse {
  id: string;
  text: string;
  location: string;
  reporter_contact?: string | null;
  category: Category;
  priority: Priority;
  status: Status;
  ai_summary?: string | null;
  triaged_by: string;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintListResponse {
  total: number;
  page: number;
  page_size: number;
  items: ComplaintResponse[];
}

export interface StatsResponse {
  total: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  by_status: Record<string, number>;
}

export interface TriageOutcomeItem {
  provider: string;
  latency_ms: number;
  fallback: boolean;
  timestamp: string;
}

export interface ProviderMetaResponse {
  active_provider: string;
  recent_outcomes: TriageOutcomeItem[];
}

export interface ApiFieldError {
  field: string;
  message: string;
}

export interface ApiErrorResponse {
  detail: string;
  errors?: ApiFieldError[];
}

export class ApiError extends Error {
  statusCode: number;
  errors?: ApiFieldError[];

  constructor(statusCode: number, detail: string, errors?: ApiFieldError[]) {
    super(detail);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.errors = errors;
  }
}
