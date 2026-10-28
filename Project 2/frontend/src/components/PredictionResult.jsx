import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info
} from 'lucide-react';
import MessageContentAnalysis from './MessageContentAnalysis';
import WordInfluences from './WordInfluences';
import URLAnalysisSection from './URLAnalysisSection';

export default function PredictionResult({ result }) {
  if (!result) return null;

  const {
    final_prediction,
    url_analysis,
    reason,
    content_analysis,
    word_influences,
  } = result;

  // Outcome styling configuration
  const outcomeConfig = {
    Phishing: {
      className: 'phishing',
      icon: ShieldAlert,
      title: 'Phishing',
      label: 'Potential Threat Detected',
    },
    'Review Required': {
      className: 'review',
      icon: AlertTriangle,
      title: 'Review Required',
      label: 'Uncertain / Verification Needed',
    },
    Legitimate: {
      className: 'legitimate',
      icon: ShieldCheck,
      title: 'Legitimate',
      label: 'No Suspicious Indicators Identified',
    },
  }[final_prediction] || {
    className: 'review',
    icon: AlertTriangle,
    title: final_prediction,
    label: 'Analysis Result',
  };

  const OutcomeIcon = outcomeConfig.icon;

  return (
    <section className="result-section" aria-label="Analysis Results">
      {/* 1. Main Outcome Banner */}
      <div className={`outcome-card ${outcomeConfig.className}`}>
        <div className="outcome-header-row">
          <div className="outcome-badge-group">
            <div className="outcome-icon" aria-hidden="true">
              <OutcomeIcon size={22} strokeWidth={2.4} />
            </div>
            <div className="outcome-title-wrap">
              <span className="outcome-meta-label">{outcomeConfig.label}</span>
              <h3 className="outcome-title">{outcomeConfig.title}</h3>
            </div>
          </div>
        </div>

        <p className="outcome-explanation">{reason}</p>
      </div>

      {/* 2. Message Content Analysis (rule-based) */}
      <MessageContentAnalysis contentAnalysis={content_analysis} />

      {/* 3. Words That Influenced the Result (model explanation) */}
      <WordInfluences wordInfluences={word_influences} />

      {/* 4. Supporting URL Structural Analysis (rendered only when URLs were extracted) */}
      <URLAnalysisSection urlAnalysis={url_analysis} />

      {/* 5. Important Safety Notice Card */}
      <div className="notice-card" role="note">
        <Info size={20} className="notice-icon" />
        <div className="notice-content">
          <div className="notice-title">Important Verification Notice</div>
          <div>
            PhishShift analyzes stylistic text patterns and local URL syntax.
            Destination servers and real-time domain reputation have not been contacted or verified.
            Predictions are indicative guides, not absolute guarantees of safety.
            Always confirm unexpected requests or banking alerts through verified, out-of-band communication channels.
          </div>
        </div>
      </div>
    </section>
  );
}
