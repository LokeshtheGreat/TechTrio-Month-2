import React, { useState } from 'react';
import { Shield, LayoutDashboard, BarChart3, Mail, Info, FileText } from 'lucide-react';
import Hero from './components/Hero';
import LiveMonitor from './components/LiveMonitor';
import Analytics from './components/Analytics';
import TestMessage from './components/TestMessage';
import ModelInsights from './components/ModelInsights';
import HowItWorks from './components/HowItWorks';

function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Shield },
    { id: 'monitor', label: 'Live Monitor', icon: LayoutDashboard },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'test', label: 'Test Message', icon: Mail },
    { id: 'insights', label: 'Model Insights', icon: Info },
    { id: 'how', label: 'How It Works', icon: FileText },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'overview': return <Hero setActiveTab={setActiveTab} />;
      case 'monitor': return <LiveMonitor />;
      case 'analytics': return <Analytics />;
      case 'test': return <TestMessage />;
      case 'insights': return <ModelInsights />;
      case 'how': return <HowItWorks />;
      default: return <Hero setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar Navigation */}
      <nav className="w-64 bg-white border-r border-gray-200 h-screen fixed">
        <div className="p-6">
          <h1 className="text-xl font-bold text-blue-600 flex items-center gap-2">
            <Shield className="w-6 h-6" />
            Spam Shield
          </h1>
        </div>
        <ul className="space-y-1 px-3">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <li key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 max-w-6xl">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
