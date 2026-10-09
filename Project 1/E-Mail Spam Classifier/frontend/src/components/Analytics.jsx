import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../../api.js';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Analytics() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE_URL}${p}`)
      .then(res => setStats(res.data))
      .catch(err => console.error(err));
  }, []);

  if (!stats) return <div className="p-8 text-center text-gray-500">Loading analytics...</div>;

  const distData = [
    { name: 'Ham', value: stats.ham, fill: '#10b981' },
    { name: 'Spam', value: stats.spam, fill: '#ef4444' }
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Analytics & Performance</h2>
        <p className="text-gray-500">System statistics and final model evaluation metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">Total Analyzed</div>
          <div className="text-2xl font-bold text-gray-900">{stats.totalEmails}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">Spam Detected</div>
          <div className="text-2xl font-bold text-red-600">{stats.spam}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">Legitimate (Ham)</div>
          <div className="text-2xl font-bold text-green-600">{stats.ham}</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">Spam Rate</div>
          <div className="text-2xl font-bold text-gray-900">{stats.spamRate}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-6">Live Inbox Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-6">Model Performance (UCI Test Set)</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600">Accuracy</span>
              <span className="font-semibold">{stats.uci_performance.accuracy}</span>
            </div>
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600">Precision</span>
              <span className="font-semibold">{stats.uci_performance.precision}</span>
            </div>
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600">Recall</span>
              <span className="font-semibold">{stats.uci_performance.recall}</span>
            </div>
            <div className="flex justify-between items-center border-b pb-2">
              <span className="text-gray-600">F1 Score</span>
              <span className="font-semibold">{stats.uci_performance.f1}</span>
            </div>
          </div>
          
          <div className="mt-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Confusion Matrix</h4>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="p-2"></div>
              <div className="p-2 font-medium bg-gray-50 rounded">Pred Ham</div>
              <div className="p-2 font-medium bg-gray-50 rounded">Pred Spam</div>
              
              <div className="p-2 font-medium bg-gray-50 rounded flex items-center justify-center">Act Ham</div>
              <div className="p-2 border rounded">897</div>
              <div className="p-2 border rounded">{stats.uci_performance.false_positives}</div>
              
              <div className="p-2 font-medium bg-gray-50 rounded flex items-center justify-center">Act Spam</div>
              <div className="p-2 border rounded">{stats.uci_performance.false_negatives}</div>
              <div className="p-2 border rounded">118</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
