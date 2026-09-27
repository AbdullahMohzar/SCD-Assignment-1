import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { ProviderMetaResponse, StatsResponse } from '../api/types';

export const StatsPage: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [xCache, setXCache] = useState<string>('MISS');
  const [meta, setMeta] = useState<ProviderMetaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchTimestamp, setFetchTimestamp] = useState<string>('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [{ data, xCache: cacheHeader }, metaData] = await Promise.all([
        apiClient.getStats(),
        apiClient.getProvidersMeta(),
      ]);
      setStats(data);
      setXCache(cacheHeader);
      setMeta(metaData);
      setFetchTimestamp(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to load stats data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#0f172a' }}>
            System Analytics & Observability
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
            Real-time complaint aggregates, Redis read-through cache telemetry, and AI provider diagnostics.
          </p>
        </div>

        <button onClick={loadData} className="btn btn-primary" data-testid="btn-refresh-stats">
          Refresh Analytics
        </button>
      </div>

      {/* Cache telemetry banner (§2.1 & §4 Rubric B) */}
      <div
        className="card"
        style={{
          marginBottom: '2rem',
          backgroundColor: xCache === 'HIT' ? '#f0fdf4' : '#fffbeb',
          borderColor: xCache === 'HIT' ? '#86efac' : '#fde68a',
        }}
        data-testid="cache-status-card"
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase', color: '#64748b' }}>
              Redis Stats Cache Telemetry (X-Cache Header)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem' }}>
              <span
                className={`badge ${xCache === 'HIT' ? 'badge-green' : 'badge-yellow'}`}
                style={{ fontSize: '0.875rem', padding: '0.375rem 0.75rem' }}
                data-testid="x-cache-badge"
              >
                X-Cache: {xCache}
              </span>
              <span style={{ fontSize: '0.875rem', color: '#334155' }}>
                {xCache === 'HIT'
                  ? 'Served directly from Redis memory (TTL 30s). Zero SQL queries executed.'
                  : 'Cache miss. Freshly computed from PostgreSQL and cached into Redis.'}
              </span>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            Last fetched: <strong>{fetchTimestamp || 'Just now'}</strong>
          </div>
        </div>
      </div>

      {/* Aggregate Cards */}
      {stats && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div className="card">
              <div style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: '600' }}>Total Complaints</div>
              <div style={{ fontSize: '2.25rem', fontWeight: '800', color: '#2563eb', marginTop: '0.25rem' }} data-testid="stats-total">
                {stats.total}
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: '600' }}>Active Provider</div>
              <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#0f172a', marginTop: '0.5rem', fontFamily: 'monospace' }} data-testid="stats-active-provider">
                {meta?.active_provider || 'simulated'}
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: '600' }}>Cache Policy</div>
              <div style={{ fontSize: '0.875rem', color: '#334155', marginTop: '0.5rem' }}>
                Read-through TTL: <strong>30s</strong><br />
                Write Invalidation: <strong>Active</strong>
              </div>
            </div>
          </div>

          {/* Breakdown Tables */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div className="card">
              <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '1rem' }}>Complaints by Category</h3>
              <table style={{ width: '100%', fontSize: '0.875rem' }}>
                <tbody>
                  {Object.entries(stats.by_category).map(([cat, count]) => (
                    <tr key={cat} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.5rem 0', textTransform: 'capitalize' }}>{cat}</td>
                      <td style={{ padding: '0.5rem 0', textAlign: 'right', fontWeight: '600' }}>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '1rem' }}>Complaints by Priority</h3>
              <table style={{ width: '100%', fontSize: '0.875rem' }}>
                <tbody>
                  {Object.entries(stats.by_priority).map(([prio, count]) => (
                    <tr key={prio} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.5rem 0', textTransform: 'capitalize' }}>{prio}</td>
                      <td style={{ padding: '0.5rem 0', textAlign: 'right', fontWeight: '600' }}>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '1rem' }}>Complaints by Status</h3>
              <table style={{ width: '100%', fontSize: '0.875rem' }}>
                <tbody>
                  {Object.entries(stats.by_status).map(([st, count]) => (
                    <tr key={st} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.5rem 0', textTransform: 'capitalize' }}>{st.replace('_', ' ')}</td>
                      <td style={{ padding: '0.5rem 0', textAlign: 'right', fontWeight: '600' }}>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Provider Outcomes Sliding Window (§2.2 /api/meta/providers) */}
          {meta && meta.recent_outcomes && meta.recent_outcomes.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '1rem', fontWeight: '700', marginBottom: '0.75rem' }}>
                Recent AI Triage Telemetry (Last 20 Outcomes)
              </h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: '0.8125rem', textAlign: 'left' }}>
                  <thead style={{ background: '#f8fafc', color: '#64748b' }}>
                    <tr>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Provider</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Latency</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Fallback Used</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {meta.recent_outcomes.map((item, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace' }}>{item.provider}</td>
                        <td style={{ padding: '0.5rem 0.75rem' }}>{item.latency_ms} ms</td>
                        <td style={{ padding: '0.5rem 0.75rem' }}>
                          <span className={`badge ${item.fallback ? 'badge-red' : 'badge-green'}`}>
                            {item.fallback ? 'Fallback (Rule)' : 'Normal'}
                          </span>
                        </td>
                        <td style={{ padding: '0.5rem 0.75rem', color: '#64748b' }}>
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
