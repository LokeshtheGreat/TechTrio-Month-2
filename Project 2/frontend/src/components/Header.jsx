import React from 'react';
import { Shield } from 'lucide-react';

export default function Header({ backendStatus }) {
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

        <div className="header-status" title="Backend ML inference service status">
          <span
            className={`status-indicator-dot ${
              backendStatus.healthy ? 'online' : backendStatus.checking ? '' : 'degraded'
            }`}
          />
          <span>
            {backendStatus.checking
              ? 'Connecting...'
              : backendStatus.healthy
              ? 'Model Engine Ready'
              : 'Backend Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}
