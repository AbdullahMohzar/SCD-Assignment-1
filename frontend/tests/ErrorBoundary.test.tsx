import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ErrorBoundary } from '../src/components/ErrorBoundary';

const FaultyComponent = () => {
  throw new Error('Explosive component error');
};

describe('ErrorBoundary Component', () => {
  it('catches render error and displays safe fallback UI without crashing', () => {
    // Suppress console.error during expected throw
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <FaultyComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeDefined();
    expect(screen.getByText(/Explosive component error/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /try again/i })).toBeDefined();

    spy.mockRestore();
  });
});
