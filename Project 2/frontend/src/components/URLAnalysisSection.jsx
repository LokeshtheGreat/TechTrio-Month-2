import React from 'react';
import { Link2, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function URLAnalysisSection({ urlAnalysis = [] }) {
  if (!urlAnalysis || urlAnalysis.length === 0) {
    return null;
  }

  return (
    <div className="url-section-card">
      <div className="url-section-title-row">
        <Link2 size={18} className="text-secondary" />
        <h3 className="url-section-title">Supporting URL Structural Analysis</h3>
        <span className="url-count-pill">
          {urlAnalysis.length} {urlAnalysis.length === 1 ? 'URL' : 'URLs'} detected
        </span>
      </div>

      <div className="url-items-list">
        {urlAnalysis.map((item, idx) => {
          const riskClass =
            item.risk_level === 'High'
              ? 'risk-high'
              : item.risk_level === 'Medium'
              ? 'risk-medium'
              : 'risk-low';

          return (
            <div key={idx} className="url-item-box">
              <div className="url-item-header">
                <span className="url-hostname">
                  Host: {item.hostname || 'Unspecified'}
                </span>
                <span className={`url-risk-tag ${riskClass}`}>
                  {item.risk_level} Structural Risk
                </span>
              </div>

              {/* URL rendered as plain text for safe inspection without navigation */}
              <div className="url-raw-text" title="Extracted URL (non-navigable)">
                {item.url}
              </div>

              {item.warnings && item.warnings.length > 0 ? (
                <div className="url-warnings-list">
                  {item.warnings.map((warn, wIdx) => (
                    <div key={wIdx} className="url-warning-item">
                      <AlertTriangle size={14} className="url-warning-bullet" />
                      <span>{warn}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="url-clean-note">
                  <CheckCircle2 size={15} />
                  <span>No configured structural warning patterns detected in this URL string.</span>
                </div>
              )}

              <p className="url-disclaimer-note">
                {item.notice ||
                  'Structural analysis inspects URL format only and does not verify server reputation, destination safety, or live content.'}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
