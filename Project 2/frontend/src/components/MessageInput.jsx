import React, { useState } from 'react';
import { Search, Loader2, RotateCcw, AlertCircle } from 'lucide-react';

const MAX_CHARS = 5000;

export default function MessageInput({ onAnalyze, isLoading, error, onClearError }) {
  const [message, setMessage] = useState('');
  const [localValidation, setLocalValidation] = useState('');

  const charCount = message.length;
  const isOverLimit = charCount > MAX_CHARS;
  const isNearLimit = charCount > MAX_CHARS * 0.9;

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (isLoading) return;

    const trimmed = message.trim();
    if (!trimmed) {
      setLocalValidation('Please enter or paste message text to analyze.');
      return;
    }

    if (trimmed.length > MAX_CHARS) {
      setLocalValidation(`Message exceeds maximum limit of ${MAX_CHARS.toLocaleString()} characters.`);
      return;
    }

    setLocalValidation('');
    if (onClearError) onClearError();
    onAnalyze(trimmed);
  };

  const handleKeyDown = (e) => {
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleClear = () => {
    setMessage('');
    setLocalValidation('');
    if (onClearError) onClearError();
  };

  const activeError = localValidation || error;

  return (
    <section className="card" aria-labelledby="input-heading">
      <div className="card-header">
        <h2 id="input-heading" className="card-title">Analyse a Message</h2>
        <p className="card-subtitle">
          Paste an SMS or email message to evaluate potential phishing characteristics and examine URL structures.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="input-group">
        <div className="textarea-wrapper">
          <textarea
            className="message-textarea"
            rows={5}
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
              if (localValidation) setLocalValidation('');
              if (error && onClearError) onClearError();
            }}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Paste suspicious SMS or email message content here (e.g. security warnings, account alerts, or unexpected notifications)..."
            aria-label="Message content to analyze"
            spellCheck="false"
          />
        </div>

        <div className="input-meta-row">
          <span className="input-hint">Tip: Press Ctrl+Enter to analyze</span>
          <span
            className={`char-counter ${
              isOverLimit ? 'limit-exceeded' : isNearLimit ? 'limit-near' : ''
            }`}
          >
            {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters
          </span>
        </div>

        {activeError && (
          <div className="error-banner" role="alert">
            <AlertCircle size={18} className="error-banner-icon" />
            <span>{activeError}</span>
          </div>
        )}

        <div className="action-row">
          {message && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClear}
              disabled={isLoading}
            >
              <RotateCcw size={15} />
              <span>Clear</span>
            </button>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading || !message.trim() || isOverLimit}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="spinner" />
                <span>Analyzing message...</span>
              </>
            ) : (
              <>
                <Search size={16} />
                <span>Analyse Message</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
