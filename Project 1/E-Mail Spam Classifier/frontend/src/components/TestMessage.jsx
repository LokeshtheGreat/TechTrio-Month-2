import React, { useState } from 'react';
import axios from 'axios';
import { Send, AlertTriangle, ShieldCheck, Loader2 } from 'lucide-react';
import { getBackendUrl } from '../config/api';

export default function TestMessage() {
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTest = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await axios.post(`${getBackendUrl()}/api/predict`, { message });
      setResult(res.data);
    } catch (err) {
      setError('Failed to analyze message. Ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Test a Message</h2>
        <p className="text-gray-500">Manually check if a message is Spam or Ham</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste the email content or SMS message here..."
          className="w-full h-48 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
        />
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={handleTest}
            disabled={loading || !message.trim()}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            Analyze Message
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-100 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      {result && (
        <div className={`p-6 rounded-xl border animate-in slide-in-from-bottom-4 duration-300 ${
          result.prediction === 'SPAM' 
            ? 'bg-red-50 border-red-200' 
            : 'bg-green-50 border-green-200'
        }`}>
          <div className="flex items-start gap-4">
            {result.prediction === 'SPAM' ? (
              <AlertTriangle className="w-8 h-8 text-red-600 mt-1" />
            ) : (
              <ShieldCheck className="w-8 h-8 text-green-600 mt-1" />
            )}
            <div className="flex-1">
              <h3 className="text-xl font-bold flex items-center gap-3">
                <span className={result.prediction === 'SPAM' ? 'text-red-700' : 'text-green-700'}>
                  {result.prediction}
                </span>
              </h3>
              
              <div className="mt-2 text-sm text-gray-700 font-medium">
                Classification Strength: {result.strength}
              </div>

              {result.prediction === 'SPAM' && result.indicators && result.indicators.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wider">
                    Important Spam Indicators
                  </h4>
                  <div className="space-y-3">
                    {result.indicators.map((ind, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="w-24 text-sm font-medium text-gray-700 truncate">{ind.term}</span>
                        <div className="flex-1 h-3 bg-red-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-red-500 rounded-full"
                            style={{ width: `${Math.min(100, (ind.weight / 2) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
