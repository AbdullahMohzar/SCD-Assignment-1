import {
  ApiError,
  ApiErrorResponse,
  ComplaintCreate,
  ComplaintListResponse,
  ComplaintResponse,
  ProviderMetaResponse,
  StatsResponse,
  Status,
} from './types';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    let errors = undefined;

    try {
      const errJson: ApiErrorResponse = await res.json();
      if (errJson.detail) detail = errJson.detail;
      if (errJson.errors) errors = errJson.errors;
    } catch {
      // response body was not json
    }

    throw new ApiError(res.status, detail, errors);
  }

  return (await res.json()) as T;
}

export const apiClient = {
  async createComplaint(data: ComplaintCreate): Promise<ComplaintResponse> {
    const res = await fetch(`${BASE_URL}/complaints`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse<ComplaintResponse>(res);
  },

  async getComplaint(id: string): Promise<ComplaintResponse> {
    const res = await fetch(`${BASE_URL}/complaints/${encodeURIComponent(id)}`);
    return handleResponse<ComplaintResponse>(res);
  },

  async listComplaints(params?: {
    category?: string;
    priority?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<ComplaintListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append('category', params.category);
    if (params?.priority) searchParams.append('priority', params.priority);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());

    const url = `${BASE_URL}/complaints${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    const res = await fetch(url);
    return handleResponse<ComplaintListResponse>(res);
  },

  async updateStatus(id: string, status: Status): Promise<ComplaintResponse> {
    const res = await fetch(`${BASE_URL}/complaints/${encodeURIComponent(id)}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    });
    return handleResponse<ComplaintResponse>(res);
  },

  async getStats(): Promise<{ data: StatsResponse; xCache: string }> {
    const res = await fetch(`${BASE_URL}/stats`);
    const xCache = res.headers.get('X-Cache') || 'MISS';
    const data = await handleResponse<StatsResponse>(res);
    return { data, xCache };
  },

  async getProvidersMeta(): Promise<ProviderMetaResponse> {
    const res = await fetch(`${BASE_URL}/meta/providers`);
    return handleResponse<ProviderMetaResponse>(res);
  },
};
