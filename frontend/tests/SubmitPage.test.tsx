import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SubmitPage } from '../src/pages/SubmitPage';
import { apiClient } from '../src/api/client';

describe('SubmitPage Component', () => {
  it('enforces client-side validation for short text input', async () => {
    render(<SubmitPage />);

    const textInput = screen.getByTestId('input-text');
    const locInput = screen.getByTestId('input-location');
    const submitBtn = screen.getByTestId('btn-submit');

    // Type text under 10 chars
    fireEvent.change(textInput, { target: { value: 'short' } });
    fireEvent.change(locInput, { target: { value: 'Street 1' } });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/at least 10 characters/i)).toBeDefined();
  });

  it('submits valid complaint and displays triage results', async () => {
    const mockCreated = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      text: 'Water pipe leaking badly and entering ground floor',
      location: 'Sector F-8/2, Islamabad',
      category: 'water' as const,
      priority: 'high' as const,
      status: 'open' as const,
      ai_summary: 'Major pipeline leak entering ground floor',
      triaged_by: 'llm:groq',
      triage_latency_ms: 250,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.spyOn(apiClient, 'createComplaint').mockResolvedValueOnce(mockCreated);

    render(<SubmitPage />);

    fireEvent.change(screen.getByTestId('input-text'), {
      target: { value: 'Water pipe leaking badly and entering ground floor' },
    });
    fireEvent.change(screen.getByTestId('input-location'), {
      target: { value: 'Sector F-8/2, Islamabad' },
    });

    fireEvent.click(screen.getByTestId('btn-submit'));

    await waitFor(() => {
      expect(screen.getByTestId('triage-result-card')).toBeDefined();
      expect(screen.getByText('llm:groq')).toBeDefined();
      expect(screen.getByText(/Major pipeline leak/i)).toBeDefined();
    });
  });
});
