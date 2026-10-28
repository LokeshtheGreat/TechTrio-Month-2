import React from 'react';
import { Sparkles } from 'lucide-react';

export default function WordInfluences({ wordInfluences }) {
  if (!wordInfluences) return null;

  const {
    suspicious_words = [],
    legitimate_words = [],
    has_influences,
    suspicious_note,
    legitimate_note,
    summary,
  } = wordInfluences;

  if (!has_influences) {
    return (
      <div className="report-card">
        <div className="section-title-row">
          <Sparkles size={18} className="text-secondary" />
          <h3 className="section-title">Words That Influenced the Result</h3>
        </div>
        <p className="neutral-influence-note">
          No specific words in the message strongly influenced the assessment.
        </p>
      </div>
    );
  }

  return (
    <div className="report-card">
      <div className="section-title-row">
        <Sparkles size={18} className="text-secondary" />
        <h3 className="section-title">Words That Influenced the Result</h3>
      </div>

      {summary && <p className="influence-summary-text">{summary}</p>}

      <div className="word-groups-grid">
        {suspicious_words.length > 0 && (
          <div className="word-group suspicious-group">
            <div className="word-group-header">
              <span className="word-group-title">Suspicious Indicators</span>
              <span className="word-group-note">
                {suspicious_note || 'These words pushed the assessment toward a suspicious result.'}
              </span>
            </div>
            <div className="word-pills-wrap">
              {suspicious_words.map((word, idx) => (
                <span key={idx} className="word-pill pill-suspicious">
                  {word}
                </span>
              ))}
            </div>
          </div>
        )}

        {legitimate_words.length > 0 && (
          <div className="word-group legitimate-group">
            <div className="word-group-header">
              <span className="word-group-title">Ordinary Communication</span>
              <span className="word-group-note">
                {legitimate_note || 'These words were more consistent with ordinary messages.'}
              </span>
            </div>
            <div className="word-pills-wrap">
              {legitimate_words.map((word, idx) => (
                <span key={idx} className="word-pill pill-legitimate">
                  {word}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="influence-disclaimer">
        Individual words represent overall linguistic patterns and do not, on their own, prove that a message is malicious or safe.
      </p>
    </div>
  );
}
