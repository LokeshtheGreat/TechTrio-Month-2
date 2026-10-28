import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MessageInput from './components/MessageInput';
import PredictionResult from './components/PredictionResult';
import InitialState from './components/InitialState';
import Footer from './components/Footer';
import { analyzeMessage, checkBackendHealth } from './services/api';

export default function App() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [backendStatus, setBackendStatus] = useState({
    state: 'checking',
    healthy: false,
    modelLoaded: false,
    message: 'Checking...',
  });

  // Verify backend health on mount and periodically every 30 seconds
  useEffect(() => {
    let isMounted = true;
    let abortController = new AbortController();

    const verifyHealth = async () => {
      try {
        const status = await checkBackendHealth({
          externalSignal: abortController.signal,
        });
        if (isMounted) {
          setBackendStatus(status);
        }
      } catch {
        if (isMounted) {
          setBackendStatus({
            state: 'offline',
            healthy: false,
            modelLoaded: false,
            message: 'Offline / Unreachable',
          });
        }
      }
    };

    verifyHealth();
    const intervalId = setInterval(verifyHealth, 30000);

    return () => {
      isMounted = false;
      abortController.abort();
      clearInterval(intervalId);
    };
  }, []);

  const handleAnalyze = async (messageText) => {
    setIsLoading(true);
    setError('');
    try {
      const data = await analyzeMessage(messageText);
      setResult(data);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred while communicating with the analysis engine.');
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearError = () => {
    setError('');
  };

  return (
    <div className="app-container">
      <Header backendStatus={backendStatus} />

      <main className="main-content">
        <MessageInput
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          error={error}
          onClearError={handleClearError}
        />

        {result ? (
          <PredictionResult result={result} />
        ) : (
          <InitialState />
        )}
      </main>

      <Footer />
    </div>
  );
}
