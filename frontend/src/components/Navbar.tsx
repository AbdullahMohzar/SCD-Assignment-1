import React from 'react';

interface NavbarProps {
  currentTab: 'submit' | 'dashboard' | 'stats';
  onSelectTab: (tab: 'submit' | 'dashboard' | 'stats') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab }) => {
  return (
    <header style={{ backgroundColor: '#ffffff', borderBottom: '1px solid #e2e8f0', marginBottom: '2rem' }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => onSelectTab('submit')}>
          <div style={{ width: '2rem', height: '2rem', borderRadius: '0.5rem', backgroundColor: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>
            CP
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#0f172a' }}>CivicPulse</h1>
            <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Municipal Complaint Intake & Triage</p>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '0.5rem' }} aria-label="Main Navigation">
          <button
            onClick={() => onSelectTab('submit')}
            className={`btn ${currentTab === 'submit' ? 'btn-primary' : 'btn-outline'}`}
            data-testid="nav-submit"
            aria-label="Submit a new municipal complaint"
            aria-current={currentTab === 'submit' ? 'page' : undefined}
          >
            Submit Complaint
          </button>
          <button
            onClick={() => onSelectTab('dashboard')}
            className={`btn ${currentTab === 'dashboard' ? 'btn-primary' : 'btn-outline'}`}
            data-testid="nav-dashboard"
            aria-label="View municipal operations dashboard"
            aria-current={currentTab === 'dashboard' ? 'page' : undefined}
          >
            Operations Dashboard
          </button>
          <button
            onClick={() => onSelectTab('stats')}
            className={`btn ${currentTab === 'stats' ? 'btn-primary' : 'btn-outline'}`}
            data-testid="nav-stats"
            aria-label="View real-time complaint analytics and cache telemetry"
            aria-current={currentTab === 'stats' ? 'page' : undefined}
          >
            Real-time Stats
          </button>
        </nav>
      </div>
    </header>
  );
};
