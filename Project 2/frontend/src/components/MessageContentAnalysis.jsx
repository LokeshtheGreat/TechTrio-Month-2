import React from 'react';
import { FileSearch, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function MessageContentAnalysis({ contentAnalysis }) {
  if (!contentAnalysis) return null;

  const { findings = [], has_findings, summary } = contentAnalysis;

  return (
    <div className="report-card">
      <div className="section-title-row">
        <FileSearch size={18} className="text-secondary" />
        <h3 className="section-title">Message Content Analysis</h3>
        {has_findings && (
          <span className="count-pill">
            {findings.length} {findings.length === 1 ? 'finding' : 'findings'}
          </span>
        )}
      </div>

      {has_findings ? (
        <div className="findings-list">
          {findings.map((item, idx) => (
            <div key={idx} className="finding-box">
              <div className="finding-header">
                <div className="finding-title-wrap">
                  <AlertTriangle size={15} className="finding-icon-warn" />
                  <span className="finding-category">{item.category}</span>
                </div>
              </div>
              <p className="finding-desc">{item.description}</p>
              {item.excerpt && (
                <div className="finding-excerpt-wrap">
                  <span className="excerpt-label">Detected wording:</span>
                  <span className="finding-excerpt">"{item.excerpt}"</span>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="content-clean-box">
          <CheckCircle2 size={16} className="clean-icon" />
          <div className="clean-text-wrap">
            <span className="clean-title">{summary || 'No obvious suspicious wording was detected.'}</span>
            <span className="clean-subtitle">
              The message text does not exhibit common pressuring language, threat warnings, or sensitive credential requests. Note that this alone does not guarantee the message is safe.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
