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
    healthy: false,
    modelLoaded: false,
    checking: true,
  });

  // Verify backend health on mount
  useEffect(() => {
    let isMounted = true;
    const verifyHealth = async () => {
      const status = await checkBackendHealth();
      if (isMounted) {
        setBackendStatus({
          healthy: status.healthy,
          modelLoaded: status.modelLoaded,
          checking: false,
        });
      }
    };

    verifyHealth();
    // Periodic check every 15 seconds
    const intervalId = setInterval(verifyHealth, 15000);
    return () => {
      isMounted = false;
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
