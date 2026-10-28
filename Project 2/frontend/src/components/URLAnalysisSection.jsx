import React from 'react';
import { Link2, AlertTriangle, CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react';

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

          const hasStrong = item.strong_signals && item.strong_signals.length > 0;
          const hasWeak = item.weak_signals && item.weak_signals.length > 0;
          const hasAnyWarnings = item.warnings && item.warnings.length > 0;

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

              {/* Domain hierarchy metadata */}
              {(item.registered_domain || item.subdomain) && (
                <div className="url-domain-meta">
                  {item.registered_domain && (
                    <div className="url-meta-segment">
                      Registered Domain: <span>{item.registered_domain}</span>
                    </div>
                  )}
                  {item.subdomain && (
                    <div className="url-meta-segment">
                      Subdomain: <span>{item.subdomain}</span>
                    </div>
                  )}
                  {item.tld && (
                    <div className="url-meta-segment">
                      TLD: <span>.{item.tld}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Trusted domain notice (with explicit safety non-guarantee disclaimer) */}
              {item.is_trusted_domain && (
                <div className="url-trusted-notice">
                  <ShieldCheck size={16} className="url-trusted-icon" />
                  <div>
                    <strong>Configured Trusted Domain:</strong> Matches allowlist entity{' '}
                    <code>{item.matched_trusted_domain || item.hostname}</code>.
                    <br />
                    <em>
                      Notice: Matching a trusted domain does not guarantee destination safety, protect against compromised accounts, or prevent open redirects.
                    </em>
                  </div>
                </div>
              )}

              {/* URL rendered as plain text for safe inspection without navigation */}
              <div className="url-raw-text" title="Extracted URL (non-navigable)">
                {item.url}
              </div>

              {/* Partitioned Risk Signals */}
              {hasAnyWarnings ? (
                <div className="url-signals-container">
                  {hasStrong && (
                    <div className="url-signal-group">
                      <span className="url-signal-group-label">Critical Structural Indicators</span>
                      {item.strong_signals.map((sig, sIdx) => (
                        <div key={sIdx} className="url-signal-item strong">
                          <ShieldAlert size={14} className="url-signal-bullet" />
                          <span>{sig}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {hasWeak && (
                    <div className="url-signal-group">
                      <span className="url-signal-group-label">Advisory Structural Signals</span>
                      {item.weak_signals.map((sig, wIdx) => (
                        <div key={wIdx} className="url-signal-item weak">
                          <AlertTriangle size={14} className="url-signal-bullet" />
                          <span>{sig}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Fallback for general warnings if strong/weak aren't populated */}
                  {!hasStrong && !hasWeak && item.warnings.map((warn, gIdx) => (
                    <div key={gIdx} className="url-warning-item">
                      <AlertTriangle size={14} className="url-warning-bullet" />
                      <span>{warn}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="url-clean-note">
                  <CheckCircle2 size={15} />
                  <span>
                    No configured structural warning patterns detected in this URL string. (Syntactic check only; destination content and server reputation are not verified.)
                  </span>
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
