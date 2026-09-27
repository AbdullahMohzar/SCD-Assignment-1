import React, { useState } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { StatsPage } from './pages/StatsPage';
import { SubmitPage } from './pages/SubmitPage';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'submit' | 'dashboard' | 'stats'>('submit');

  return (
    <ErrorBoundary>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} />

        <main className="container" style={{ flex: 1, paddingBottom: '3rem' }}>
          {currentTab === 'submit' && <SubmitPage />}
          {currentTab === 'dashboard' && <DashboardPage />}
          {currentTab === 'stats' && <StatsPage />}
        </main>

        <footer style={{ borderTop: '1px solid #e2e8f0', background: '#ffffff', padding: '1.5rem 0', textAlign: 'center', fontSize: '0.875rem', color: '#64748b' }}>
          <div className="container">
            CivicPulse Municipal Complaint & AI Triage Platform • CS4032 Software Construction and Design
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
};

export default App;
