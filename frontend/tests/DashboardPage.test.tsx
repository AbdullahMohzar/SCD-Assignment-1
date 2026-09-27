import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DashboardPage } from '../src/pages/DashboardPage';
import { apiClient } from '../src/api/client';
import { ApiError } from '../src/api/types';

describe('DashboardPage Component', () => {
  it('renders complaints list correctly', async () => {
    vi.spyOn(apiClient, 'listComplaints').mockResolvedValueOnce({
      total: 1,
      page: 1,
      page_size: 10,
      items: [
        {
          id: 'test-uuid-1',
          text: 'Pothole on main boulevard road',
          location: 'Main Boulevard, Lahore',
          category: 'roads',
          priority: 'normal',
          status: 'open',
          ai_summary: 'Pothole issue on main road',
          triaged_by: 'rules',
          triage_latency_ms: 10,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Pothole on main boulevard road')).toBeDefined();
      expect(screen.getByText('📍 Main Boulevard, Lahore')).toBeDefined();
    });
  });

  it("surfaces server's 409 message verbatim upon invalid transition", async () => {
    vi.spyOn(apiClient, 'listComplaints').mockResolvedValueOnce({
      total: 1,
      page: 1,
      page_size: 10,
      items: [
        {
          id: 'complaint-409-id',
          text: 'Resolved water problem',
          location: 'Islamabad',
          category: 'water',
          priority: 'low',
          status: 'resolved',
          ai_summary: null,
          triaged_by: 'simulated',
          triage_latency_ms: 5,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    });

    // Mock API 409 error
    vi.spyOn(apiClient, 'updateStatus').mockRejectedValueOnce(
      new ApiError(409, 'Invalid transition from resolved to in_progress')
    );

    render(<DashboardPage />);

    const reopenBtn = await screen.findByTestId('btn-invalid-reopen-complaint-409-id');
    fireEvent.click(reopenBtn);

    await waitFor(() => {
      const banner = screen.getByTestId('server-error-banner');
      expect(banner.textContent).toContain('Invalid transition from resolved to in_progress');
    });
  });
});
