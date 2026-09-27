import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { ApiError, ComplaintResponse } from '../api/types';
import { PriorityBadge } from '../components/PriorityBadge';
import { StatusBadge } from '../components/StatusBadge';

export const SubmitPage: React.FC = () => {
  const [text, setText] = useState('');
  const [location, setLocation] = useState('');
  const [reporterContact, setReporterContact] = useState('');

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [submittedResult, setSubmittedResult] = useState<ComplaintResponse | null>(null);

  const validateClientSide = (): boolean => {
    const errors: Record<string, string> = {};

    if (!text.trim() || text.trim().length < 10) {
      errors.text = 'Complaint description must be at least 10 characters.';
    } else if (text.trim().length > 2000) {
      errors.text = 'Complaint description cannot exceed 2000 characters.';
    }

    if (!location.trim() || location.trim().length < 3) {
      errors.location = 'Location must be at least 3 characters.';
    } else if (location.trim().length > 200) {
      errors.location = 'Location cannot exceed 200 characters.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);
    setSubmittedResult(null);

    // Client-side mirror validation
    if (!validateClientSide()) {
      return;
    }

    setLoading(true);
    setLoadingStep('Submitting complaint & executing AI triage model (this takes a few seconds)...');

    try {
      const result = await apiClient.createComplaint({
        text: text.trim(),
        location: location.trim(),
        reporter_contact: reporterContact.trim() || undefined,
      });

      setSubmittedResult(result);
      setText('');
      setLocation('');
      setReporterContact('');
      setFieldErrors({});
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.errors && err.errors.length > 0) {
          const map: Record<string, string> = {};
          err.errors.forEach((fe) => {
            map[fe.field] = fe.message;
          });
          setFieldErrors(map);
        } else {
          setGeneralError(err.message);
        }
      } else {
        setGeneralError('An unexpected network or service error occurred.');
      }
    } finally {
      setLoading(false);
      setLoadingStep('');
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '0.5rem', color: '#0f172a' }}>
          Lodge Municipal Complaint
        </h2>
        <p style={{ color: '#64748b', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
          Describe the civic issue in your own words. Our AI triage system classifies urgency and routes it to municipal authorities.
        </p>

        {generalError && (
          <div style={{ padding: '0.75rem 1rem', background: '#fee2e2', border: '1px solid #f87171', borderRadius: '0.5rem', color: '#b91c1c', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
            {generalError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontWeight: '600', fontSize: '0.875rem', marginBottom: '0.375rem' }}>
              Complaint Description <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <textarea
              className="textarea-field"
              rows={4}
              placeholder="e.g. Burst water main flooding Street 12 since fajr, water entering ground floors..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
              data-testid="input-text"
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
              {fieldErrors.text ? (
                <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.text}</span>
              ) : (
                <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Min 10, max 2000 characters.</span>
              )}
              <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{text.length}/2000</span>
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontWeight: '600', fontSize: '0.875rem', marginBottom: '0.375rem' }}>
              Location / Address <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. Street 12, Sector F-8/2, Islamabad"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              disabled={loading}
              data-testid="input-location"
            />
            {fieldErrors.location && (
              <span style={{ color: '#ef4444', fontSize: '0.75rem', display: 'block', marginTop: '0.25rem' }}>
                {fieldErrors.location}
              </span>
            )}
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontWeight: '600', fontSize: '0.875rem', marginBottom: '0.375rem' }}>
              Contact Number / Email <span style={{ color: '#94a3b8', fontWeight: 'normal' }}>(Optional)</span>
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. +92 300 1234567"
              value={reporterContact}
              onChange={(e) => setReporterContact(e.target.value)}
              disabled={loading}
              data-testid="input-contact"
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              data-testid="btn-submit"
              style={{ minWidth: '160px' }}
            >
              {loading ? (
                <>
                  <div className="spinner" />
                  Triaging...
                </>
              ) : (
                'Submit Complaint'
              )}
            </button>

            {loading && (
              <span style={{ color: '#2563eb', fontSize: '0.875rem', fontWeight: '500' }}>
                {loadingStep}
              </span>
            )}
          </div>
        </form>
      </div>

      {submittedResult && (
        <div className="card" style={{ borderColor: '#86efac', backgroundColor: '#f0fdf4' }} data-testid="triage-result-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ color: '#166534', fontSize: '1.125rem', fontWeight: '700' }}>
              Complaint Triaged & Recorded Successfully
            </h3>
            <span style={{ fontSize: '0.75rem', color: '#166534', fontFamily: 'monospace' }}>
              ID: {submittedResult.id}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: '600', textTransform: 'uppercase' }}>
                Category
              </div>
              <div style={{ fontSize: '1rem', fontWeight: '700', textTransform: 'capitalize', color: '#0f172a' }}>
                {submittedResult.category}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: '600', textTransform: 'uppercase' }}>
                Priority
              </div>
              <div style={{ marginTop: '0.25rem' }}>
                <PriorityBadge priority={submittedResult.priority} />
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: '600', textTransform: 'uppercase' }}>
                Initial Status
              </div>
              <div style={{ marginTop: '0.25rem' }}>
                <StatusBadge status={submittedResult.status} />
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: '600', textTransform: 'uppercase' }}>
                Triaged By
              </div>
              <div style={{ fontSize: '0.875rem', fontFamily: 'monospace', fontWeight: '600', color: '#1e40af' }}>
                {submittedResult.triaged_by}
              </div>
            </div>
          </div>

          {submittedResult.ai_summary && (
            <div style={{ background: '#ffffff', padding: '0.75rem 1rem', borderRadius: '0.5rem', border: '1px solid #bbf7d0', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: '600', marginBottom: '0.25rem' }}>
                AI Summary:
              </div>
              <div style={{ fontSize: '0.875rem', color: '#1e293b' }}>
                {submittedResult.ai_summary}
              </div>
            </div>
          )}

          <div style={{ fontSize: '0.75rem', color: '#15803d' }}>
            Triage latency: <strong>{submittedResult.triage_latency_ms} ms</strong> | Recorded at:{' '}
            {new Date(submittedResult.created_at).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};
