import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { StatsPage } from '../src/pages/StatsPage';
import { apiClient } from '../src/api/client';

describe('StatsPage Component', () => {
  it('renders stats aggregates and displays X-Cache HIT badge', async () => {
    vi.spyOn(apiClient, 'getStats').mockResolvedValueOnce({
      data: {
        total: 42,
        by_category: { water: 15, electricity: 10, sanitation: 7, roads: 5, streetlights: 3, other: 2 },
        by_priority: { high: 20, normal: 15, low: 7 },
        by_status: { open: 25, in_progress: 10, resolved: 5, rejected: 2 },
      },
      xCache: 'HIT',
    });

    vi.spyOn(apiClient, 'getProvidersMeta').mockResolvedValueOnce({
      active_provider: 'llm:groq',
      recent_outcomes: [],
    });

    render(<StatsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('x-cache-badge').textContent).toContain('X-Cache: HIT');
      expect(screen.getByTestId('stats-total').textContent).toBe('42');
      expect(screen.getByTestId('stats-active-provider').textContent).toBe('llm:groq');
    });
  });
});
