import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Navbar } from '../src/components/Navbar';

describe('Navbar Component', () => {
  it('renders all tab navigation buttons and triggers selection callback', () => {
    const handleSelect = vi.fn();
    render(<Navbar currentTab="submit" onSelectTab={handleSelect} />);

    expect(screen.getByText('CivicPulse')).toBeDefined();
    const dashboardBtn = screen.getByTestId('nav-dashboard');
    const statsBtn = screen.getByTestId('nav-stats');

    fireEvent.click(dashboardBtn);
    expect(handleSelect).toHaveBeenCalledWith('dashboard');

    fireEvent.click(statsBtn);
    expect(handleSelect).toHaveBeenCalledWith('stats');
  });
});
