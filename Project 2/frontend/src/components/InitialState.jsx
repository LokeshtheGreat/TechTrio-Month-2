import React from 'react';
import { SearchCheck } from 'lucide-react';

export default function InitialState() {
  return (
    <div className="initial-state-card" aria-live="polite">
      <div className="initial-state-icon-wrap" aria-hidden="true">
        <SearchCheck size={24} />
      </div>

      <h3 className="initial-state-title">Ready to analyse</h3>
      <p className="initial-state-desc">
        Paste a message above to examine its content for potential phishing indicators.
      </p>
    </div>
  );
}
