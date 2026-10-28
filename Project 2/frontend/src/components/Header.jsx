import React from 'react';
import { Shield } from 'lucide-react';

export default function Header({ backendStatus }) {
  const { state = 'checking', message = 'Checking...' } = backendStatus || {};

  return (
    <header className="header">
      <div className="header-inner">
        <div className="brand-group">
          <div className="brand-icon-wrapper" aria-hidden="true">
            <Shield size={20} strokeWidth={2.2} />
          </div>
          <div className="brand-text-col">
            <div className="brand-title-row">
              <span className="brand-title">PhishShift</span>
              <span className="brand-badge">ML-Powered Message Analysis</span>
            </div>
            <span className="brand-tagline">
              Understand suspicious messages before you trust them.
            </span>
          </div>
        </div>

        <div
          className="header-status"
          role="status"
          aria-live="polite"
          title={`Backend API Status: ${message}`}
        >
          <span
            className={`status-indicator-dot ${state}`}
            aria-hidden="true"
          />
          <span>{message}</span>
        </div>
      </div>
    </header>
  );
}
