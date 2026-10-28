import React from 'react';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <span className="footer-brand">
          PhishShift | Machine-learning-assisted phishing analysis
        </span>
        <p className="footer-disclaimer">
          Predictions are indicative, not guarantees of message or URL safety.
        </p>
      </div>
    </footer>
  );
}
