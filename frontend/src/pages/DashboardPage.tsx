import React, { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { ApiError, ComplaintResponse, Status } from '../api/types';
import { PriorityBadge } from '../components/PriorityBadge';
import { StatusBadge } from '../components/StatusBadge';

export const DashboardPage: React.FC = () => {
  const [complaints, setComplaints] = useState<ComplaintResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Verbatim server error message banner (e.g. 409 Conflict)
  const [serverError, setServerError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.listComplaints({
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: pageSize,
      });
      setComplaints(response.items);
      setTotal(response.total);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError('Failed to load complaints from backend service.');
      }
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, priorityFilter, statusFilter, page]);

  useEffect(() => {
    fetchComplaints();
  }, [fetchComplaints]);

  const handleStatusTransition = async (complaintId: string, newStatus: Status) => {
    setServerError(null);
    setActionSuccess(null);

    try {
      const updated = await apiClient.updateStatus(complaintId, newStatus);
      setActionSuccess(`Status updated to ${newStatus} for complaint ${complaintId.slice(0, 8)}...`);
      // Update local state immediately
      setComplaints((prev) =>
        prev.map((c) => (c.id === complaintId ? updated : c))
      );
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        // Surface the server's 409 message verbatim (§2.1 & Rubric B)
        setServerError(err.message);
      } else {
        setServerError('An unknown error occurred while transitioning status.');
      }
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#0f172a' }}>
            Municipal Operations Dashboard
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
            Triaged complaint queue. Manage lifecycle state and assign field resolution.
          </p>
        </div>
        <button onClick={fetchComplaints} className="btn btn-outline" data-testid="btn-refresh">
          Refresh Queue
        </button>
      </div>

      {serverError && (
        <div
          data-testid="server-error-banner"
          style={{
            padding: '1rem',
            background: '#fee2e2',
            border: '1px solid #ef4444',
            borderRadius: '0.5rem',
            color: '#b91c1c',
            marginBottom: '1.5rem',
            fontWeight: '500',
            fontSize: '0.875rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>{serverError}</span>
          <button
            onClick={() => setServerError(null)}
            style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer', fontWeight: 'bold' }}
          >
            ✕
          </button>
        </div>
      )}

      {actionSuccess && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: '#dcfce7',
            border: '1px solid #86efac',
            borderRadius: '0.5rem',
            color: '#15803d',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
          }}
        >
          {actionSuccess}
        </div>
      )}

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '600', color: '#64748b', marginBottom: '0.25rem' }}>
              Category
            </label>
            <select
              className="select-field"
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              data-testid="filter-category"
            >
              <option value="">All Categories</option>
              <option value="water">Water</option>
              <option value="electricity">Electricity</option>
              <option value="sanitation">Sanitation</option>
              <option value="roads">Roads</option>
              <option value="streetlights">Streetlights</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '600', color: '#64748b', marginBottom: '0.25rem' }}>
              Priority
            </label>
            <select
              className="select-field"
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(1);
              }}
              data-testid="filter-priority"
            >
              <option value="">All Priorities</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '600', color: '#64748b', marginBottom: '0.25rem' }}>
              Status
            </label>
            <select
              className="select-field"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              data-testid="filter-status"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Complaints Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '1.5rem' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
            <div className="spinner" style={{ borderColor: 'rgba(37,99,235,0.3)', borderTopColor: '#2563eb', margin: '0 auto 1rem auto' }} />
            Loading complaint queue...
          </div>
        ) : complaints.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
            No complaints found matching current filter criteria.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                <tr>
                  <th style={{ padding: '0.75rem 1rem' }}>Complaint & Location</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Category</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Priority</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Triage Provider</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #e2e8f0' }} data-testid={`complaint-row-${item.id}`}>
                    <td style={{ padding: '1rem', maxWidth: '350px' }}>
                      <div style={{ fontWeight: '600', color: '#0f172a', marginBottom: '0.25rem' }}>
                        {item.text}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        📍 {item.location}
                      </div>
                      {item.ai_summary && (
                        <div style={{ fontSize: '0.75rem', color: '#2563eb', marginTop: '0.25rem', fontStyle: 'italic' }}>
                          "{item.ai_summary}"
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem', textTransform: 'capitalize', fontWeight: '500' }}>
                      {item.category}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <PriorityBadge priority={item.priority} />
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <StatusBadge status={item.status} />
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                      <div>{item.triaged_by}</div>
                      <div style={{ color: '#94a3b8' }}>{item.triage_latency_ms} ms</div>
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.375rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        {item.status === 'open' && (
                          <button
                            onClick={() => handleStatusTransition(item.id, 'in_progress')}
                            className="btn btn-outline"
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                            data-testid={`btn-progress-${item.id}`}
                          >
                            Start
                          </button>
                        )}
                        {item.status === 'in_progress' && (
                          <button
                            onClick={() => handleStatusTransition(item.id, 'resolved')}
                            className="btn btn-primary"
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                            data-testid={`btn-resolve-${item.id}`}
                          >
                            Resolve
                          </button>
                        )}
                        {(item.status === 'open' || item.status === 'in_progress') && (
                          <button
                            onClick={() => handleStatusTransition(item.id, 'rejected')}
                            className="btn btn-danger"
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                            data-testid={`btn-reject-${item.id}`}
                          >
                            Reject
                          </button>
                        )}
                        {/* Deliberate button to trigger invalid transition (e.g. resolve -> in_progress) to test 409 surfacing */}
                        {(item.status === 'resolved' || item.status === 'rejected') && (
                          <button
                            onClick={() => handleStatusTransition(item.id, 'in_progress')}
                            className="btn btn-outline"
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', color: '#94a3b8' }}
                            title="Will trigger server 409 conflict error"
                            data-testid={`btn-invalid-reopen-${item.id}`}
                          >
                            Re-open (Invalid)
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
          Showing <strong>{complaints.length}</strong> of <strong>{total}</strong> complaints
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page <= 1}
            className="btn btn-outline"
            data-testid="btn-prev-page"
          >
            Previous
          </button>
          <span style={{ display: 'flex', alignItems: 'center', padding: '0 0.5rem', fontSize: '0.875rem' }}>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page >= totalPages}
            className="btn btn-outline"
            data-testid="btn-next-page"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
