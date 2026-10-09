import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import API_BASE_URL from '../api.js';
import DOMPurify from 'dompurify';
import { Mail, AlertCircle, CheckCircle2, RefreshCw, X, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function LiveMonitor() {
  const [connected, setConnected] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [emails, setEmails] = useState([]);
  const [statusLoading, setStatusLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [monitoring, setMonitoring] = useState(false);

  const [expiration, setExpiration] = useState(null);
  const [renewalStatus, setRenewalStatus] = useState('active');
  const [serverTime, setServerTime] = useState(null);

  const detailScrollRef = useRef(null);

  useEffect(() => {
    if (detailScrollRef.current) {
      detailScrollRef.current.scrollTop = 0;
    }
  }, [selectedEmail?.id]);

  useEffect(() => {
    checkStatus();
  }, []);

  useEffect(() => {
    let interval;
    if (monitoring) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE_URL}${p}`);
          if (res.data.emails) {
            setEmails(res.data.emails);
          }
          if (res.data.monitoring !== undefined) {
            setMonitoring(res.data.monitoring);
          }
          if (res.data.expiration !== undefined) {
            setExpiration(res.data.expiration);
          }
          if (res.data.renewal_status !== undefined) {
            setRenewalStatus(res.data.renewal_status);
          }
          if (res.data.current_time !== undefined) {
            setServerTime(res.data.current_time);
          }
        } catch (err) {
          console.error(err);
        }
      }, 5000);
    }
  return () => {
      if (interval) clearInterval(interval);
    };
  }, [monitoring]);


  const checkStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}${p}`);
      setConnected(res.data.connected);
      if (res.data.connected) {
        setUserEmail(res.data.email);
        handleSync(); // Auto sync on load if connected
      }
    } catch (err) {
      console.error(err);
      setError('Unable to check Gmail connection status.');
    } finally {
      setStatusLoading(false);
    }
  };

  const handleConnect = () => {
    window.location.href = `${API_BASE_URL}${p}`;
  };

  const handleDisconnect = async () => {
    try {
      await axios.post(`${API_BASE_URL}${p}`);
      setConnected(false);
      setUserEmail('');
      setEmails([]);
    } catch (err) {
      setError('Failed to disconnect.');
    }
  };

  
  const handleStartWatch = async () => {
    try {
      await axios.post(`${API_BASE_URL}${p}`);
      setMonitoring(true);
    } catch(err) {
      setError('Failed to start monitoring');
    }
  };

  
  const handleRenewWatch = async () => {
    try {
      const res = await axios.post(`${API_BASE_URL}${p}`);
      setExpiration(res.data.expiration);
      setRenewalStatus('active');
    } catch(err) {
      setError('Failed to renew monitoring');
    }
  };

  const handleStopWatch = async () => {
    try {
      await axios.post(`${API_BASE_URL}${p}`);
      setMonitoring(false);
    } catch(err) {
      setError('Failed to stop monitoring');
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setError('');
    try {
      const res = await axios.post(`${API_BASE_URL}${p}`);
      setEmails(res.data.emails || []);
    } catch (err) {
      console.error(err);
      setError('Unable to access Gmail right now. Please try again.');
    } finally {
      setSyncing(false);
    }
  };

  if (statusLoading) {
    return <div className="p-8 text-center text-gray-500">Checking connection...</div>;
  }

  if (!connected) {
  return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Live Monitor</h2>
          <p className="text-gray-500">Connect your Gmail account to enable Live Monitoring.</p>
        </div>
        <div className="bg-white rounded-xl p-10 shadow-sm border border-gray-200 text-center">
          <Mail className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">Gmail is not connected.</h3>
          <p className="text-gray-500 mb-6">Authorize this application to read your recent emails and classify them.</p>
          <button 
            onClick={handleConnect}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Connect Gmail
          </button>
        </div>
        {error && <div className="text-red-500 text-center">{error}</div>}
      </div>
    );
  }

  // Calculate Stats
  const total = emails.length;
  const spamCount = emails.filter(e => e.prediction === 'SPAM').length;
  const hamCount = total - spamCount;
  const spamPercentage = total > 0 ? Math.round((spamCount / total) * 100) : 0;

  const renderWatchStatus = () => {
    if (!monitoring) return <div className="text-sm font-medium text-gray-500">Real-time monitoring paused</div>;
    
    if (renewalStatus === 'failed') {
      return (
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-red-600">Monitoring renewal failed</span>
          <button onClick={handleRenewWatch} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200">Renew Monitoring</button>
        </div>
      );
    }

    if (!expiration || !serverTime) {
      return <div className="text-sm font-medium text-green-600">Real-time monitoring active</div>;
    }

    const timeLeftMs = expiration - serverTime;
    
    if (timeLeftMs <= 0) {
      return (
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-red-600">Real-time monitoring paused (expired)</span>
          <button onClick={handleRenewWatch} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200">Renew Monitoring</button>
        </div>
      );
    } else if (timeLeftMs < 86400000) { // < 24 hours
      const hours = Math.floor(timeLeftMs / 3600000);
      return <div className="text-sm font-medium text-yellow-600">Monitoring expires in {hours} hours (auto-renewing...)</div>;
    } else {
      return <div className="text-sm font-medium text-green-600">Real-time monitoring active</div>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Live Monitor</h2>
          <p className="text-gray-500 flex items-center gap-2 mb-1">
            Connected to: <span className="font-semibold">{userEmail}</span>
            <button onClick={handleDisconnect} className="text-sm text-red-500 hover:underline ml-2">
              [ Disconnect ]
            </button>
          </p>
          {renderWatchStatus()}
        </div>

        <div className="flex items-center gap-3">
          {monitoring ? (
            <button 
              onClick={handleStopWatch}
              className="flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors"
            >
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
              Stop Monitoring
            </button>
          ) : (
            <button 
              onClick={handleStartWatch}
              className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm font-medium hover:bg-green-100 transition-colors"
            >
              Start Monitoring
            </button>
          )}
          <button 
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>

      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-100 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <div className="text-xs text-gray-500">Total</div>
          <div className="text-xl font-bold">{total}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <div className="text-xs text-gray-500">Ham</div>
          <div className="text-xl font-bold text-green-600">{hamCount}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <div className="text-xs text-gray-500">Spam</div>
          <div className="text-xl font-bold text-red-600">{spamCount}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <div className="text-xs text-gray-500">Spam %</div>
          <div className="text-xl font-bold text-gray-900">{spamPercentage}%</div>
        </div>
      </div>

      {emails.length === 0 && !syncing && !error ? (
        <div className="bg-white p-10 rounded-xl border shadow-sm text-center">
          <p className="text-gray-500">No recent emails found.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex h-[700px]">
          {/* Email List */}
          <div className="w-[400px] shrink-0 border-r flex flex-col">
            <div className="overflow-y-auto flex-1 divide-y divide-gray-200">
              {emails.map((email) => (
                <div 
                  key={email.id} 
                  onClick={() => setSelectedEmail(email)}
                  className={`p-4 cursor-pointer transition-colors flex items-start gap-3 ${selectedEmail?.id === email.id ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                >
                  <div className="pt-1">
                    {email.prediction === 'SPAM' ? (
                      <div className="w-3 h-3 rounded-full bg-red-500" title="SPAM"></div>
                    ) : email.prediction === 'HAM' ? (
                      <div className="w-3 h-3 rounded-full bg-green-500" title="HAM"></div>
                    ) : (
                      <div className="w-3 h-3 rounded-full bg-gray-400" title="ERROR"></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline mb-1">
                      <h3 className="font-semibold text-gray-900 truncate text-sm">{email.sender.split('<')[0].trim()}</h3>
                      <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                        {email.timestamp ? new Date(email.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : ''}
                      </span>
                    </div>
                    <div className="font-medium text-gray-800 text-sm mb-1 truncate">{email.subject}</div>
                    <div className="text-gray-500 text-xs truncate">{email.snippet}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {email.prediction === 'ERROR' ? (
                      <span className="text-xs font-bold text-gray-500">ERROR</span>
                    ) : (
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        email.prediction === 'SPAM' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {email.prediction}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Email Detail */}
          <div className="flex-1 min-w-0 flex flex-col bg-gray-50">
            {selectedEmail ? (
              <div className="flex-1 overflow-y-auto" ref={detailScrollRef}>
                <div className="p-6 bg-white border-b">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-bold text-xl text-gray-900 mb-1">{selectedEmail.subject}</h3>
                      <div className="text-sm text-gray-600">From: <span className="font-medium text-gray-900">{selectedEmail.sender}</span></div>
                      <div className="text-sm text-gray-500">Date: {selectedEmail.timestamp}</div>
                    </div>
                    <button onClick={() => setSelectedEmail(null)} className="text-gray-400 hover:text-gray-600">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  
                  <div className={`mt-4 p-4 rounded-lg border ${selectedEmail.prediction === 'SPAM' ? 'bg-red-50 border-red-100' : selectedEmail.prediction === 'HAM' ? 'bg-green-50 border-green-100' : 'bg-gray-100'}`}>
                    <div className="flex items-center gap-3 mb-2">
                      {selectedEmail.prediction === 'SPAM' ? <ShieldAlert className="w-6 h-6 text-red-600" /> : selectedEmail.prediction === 'HAM' ? <ShieldCheck className="w-6 h-6 text-green-600" /> : <AlertCircle className="w-6 h-6 text-gray-600" />}
                      <span className={`font-bold text-lg ${selectedEmail.prediction === 'SPAM' ? 'text-red-700' : selectedEmail.prediction === 'HAM' ? 'text-green-700' : 'text-gray-700'}`}>
                        {selectedEmail.prediction}
                      </span>
                    </div>
                    {selectedEmail.prediction !== 'ERROR' && (
                      <div className="text-sm font-medium text-gray-700">Classification Strength: {selectedEmail.classification_strength}</div>
                    )}
                    {selectedEmail.prediction === 'ERROR' && (
                      <div className="text-sm font-medium text-gray-700">Unable to classify this email</div>
                    )}
                    {selectedEmail.spam_indicators && selectedEmail.spam_indicators.length > 0 && (
                      <div className="mt-3">
                        <div className="text-xs font-bold text-gray-500 uppercase mb-2">Spam Indicators</div>
                        <div className="flex flex-wrap gap-2">
                          {selectedEmail.spam_indicators.map((ind, i) => (
                            <span key={i} className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-md">
                              {ind.term} ({ind.weight.toFixed(2)})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                {selectedEmail.body_html ? (
                  <div 
                    className="p-6 text-sm text-gray-800 break-words max-w-full overflow-x-auto bg-white email-content"
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(selectedEmail.body_html) }} 
                  />
                ) : (
                  <div className="p-6 text-sm text-gray-800 whitespace-pre-wrap break-words">
                    {selectedEmail.body || selectedEmail.snippet}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-400">
                Select an email to view details
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
