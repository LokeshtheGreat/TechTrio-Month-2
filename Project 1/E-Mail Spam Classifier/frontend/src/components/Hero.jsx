import React, { useState, useEffect } from 'react';
import { ShieldAlert, Activity, Mail, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import API_BASE_URL from '../api.js';

export default function Hero({ setActiveTab }) {
  const [connected, setConnected] = useState(false);
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}${p}`);
        setConnected(res.data.connected);
        if (res.data.connected) {
          setUserEmail(res.data.email);
        }
      } catch (err) {
        console.error("Status check failed", err);
      }
    };
    checkStatus();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="bg-white rounded-2xl p-10 shadow-sm border border-gray-100 text-center">
        <ShieldAlert className="w-16 h-16 text-blue-600 mx-auto mb-6" />
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Email Spam Shield</h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          AI-powered email classification using TF-IDF and Linear SVM.
          Detects spam and unwanted messages in real-time.
        </p>
        
        <div className="flex justify-center gap-4 mb-8">
          <button 
            onClick={() => setActiveTab('monitor')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Activity className="w-5 h-5" />
            Open Live Monitor
          </button>
          <button 
            onClick={() => setActiveTab('test')}
            className="px-6 py-3 bg-white text-gray-700 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <Mail className="w-5 h-5" />
            Test a Message
          </button>
        </div>

        {connected ? (
          <div className="inline-flex items-center gap-3 px-5 py-3 bg-green-50 border border-green-200 rounded-xl text-green-800">
            <CheckCircle2 className="w-6 h-6 text-green-600" />
            <div className="text-left">
              <div className="font-semibold text-sm">Gmail Connected</div>
              <div className="text-xs text-green-700">{userEmail}</div>
            </div>
          </div>
        ) : (
          <div className="inline-flex items-center gap-3 px-5 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-700">
            <AlertCircle className="w-6 h-6 text-gray-500" />
            <div className="text-left">
              <div className="font-semibold text-sm">Gmail Not Connected</div>
              <div className="text-xs text-gray-500">Go to Live Monitor to connect</div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <div className="text-sm font-medium text-gray-500 mb-1">Total Emails Analyzed</div>
          <div className="text-3xl font-bold text-gray-900">18</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <div className="text-sm font-medium text-gray-500 mb-1">Legitimate (Ham)</div>
          <div className="text-3xl font-bold text-green-600">13</div>
        </div>
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <div className="text-sm font-medium text-gray-500 mb-1">Spam Detected</div>
          <div className="text-3xl font-bold text-red-600">5</div>
        </div>
      </div>
    </div>
  );
}
