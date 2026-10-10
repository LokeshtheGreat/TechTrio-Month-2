import React, { useState, useEffect } from 'react';
import { Shield, LayoutDashboard, BarChart3, Mail, Info, FileText, LogIn, LogOut } from 'lucide-react';
import Hero from './components/Hero';
import LiveMonitor from './components/LiveMonitor';
import Analytics from './components/Analytics';
import TestMessage from './components/TestMessage';
import ModelInsights from './components/ModelInsights';
import HowItWorks from './components/HowItWorks';
import AuthModal from './components/AuthModal';
import PrivacyPolicy from './components/PrivacyPolicy';
import TermsOfService from './components/TermsOfService';
import { AuthProvider, useAuth } from './context/AuthContext';
import { getRouteFromUrl, getRoutePath } from './utils/routes';

function AppContent() {
  const [currentRoute, setCurrentRoute] = useState(getRouteFromUrl);
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('gmail_connected') === 'true') {
        return 'monitor';
      }
    }
    return 'overview';
  });
  const { user, openAuthModal, signOut } = useAuth();

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentRoute(getRouteFromUrl());
    };
    window.addEventListener('popstate', handleLocationChange);
    window.addEventListener('hashchange', handleLocationChange);
    return () => {
      window.removeEventListener('popstate', handleLocationChange);
      window.removeEventListener('hashchange', handleLocationChange);
    };
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('gmail_connected') === 'true') {
        setActiveTab('monitor');
        // Clean up the URL query parameter cleanly without reloading
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  }, []);

  const navigateTo = (route) => {
    const targetPath = getRoutePath(route);
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', targetPath);
      setCurrentRoute(route);
      window.scrollTo(0, 0);
    }
  };

  if (currentRoute === 'privacy-policy') {
    return <PrivacyPolicy onNavigate={navigateTo} />;
  }

  if (currentRoute === 'terms') {
    return <TermsOfService onNavigate={navigateTo} />;
  }

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
      <nav className="w-64 bg-white border-r border-gray-200 h-screen fixed flex flex-col justify-between">
        <div>
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
        </div>

        <div>
          {/* Legal Navigation Links */}
          <div className="px-4 py-2 border-t border-gray-100 flex items-center justify-center gap-2 text-[11px] text-gray-500">
            <button
              onClick={() => navigateTo('privacy-policy')}
              className="hover:text-blue-600 transition-colors"
            >
              Privacy Policy
            </button>
            <span>•</span>
            <button
              onClick={() => navigateTo('terms')}
              className="hover:text-blue-600 transition-colors"
            >
              Terms of Service
            </button>
          </div>

          {/* User / Authentication Status Footer */}
          <div className="p-4 border-t border-gray-100 bg-gray-50/50">
            {user ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-sm flex-shrink-0">
                    {user.email ? user.email.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div className="overflow-hidden">
                    <div className="text-[11px] text-gray-500 font-medium flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span>
                      Signed in
                    </div>
                    <div className="text-xs font-semibold text-gray-800 truncate" title={user.email}>
                      {user.email}
                    </div>
                  </div>
                </div>
                <button
                  onClick={signOut}
                  className="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-red-200/60 font-medium"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-[11px] text-gray-500 text-center">
                  Sign in to isolate data & connect Gmail
                </div>
                <button
                  onClick={openAuthModal}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  <LogIn className="w-4 h-4" />
                  Sign In / Register
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 max-w-6xl min-h-screen flex flex-col justify-between">
        <div>
          {renderContent()}
        </div>
        <footer className="mt-16 pt-6 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 gap-4">
          <p>© 2026 Email Spam Shield. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigateTo('privacy-policy')}
              className="hover:text-blue-600 transition-colors"
            >
              Privacy Policy
            </button>
            <span>•</span>
            <button
              onClick={() => navigateTo('terms')}
              className="hover:text-blue-600 transition-colors"
            >
              Terms of Service
            </button>
            <span>•</span>
            <a
              href="https://github.com/LokeshtheGreat/TechTrio-Month-2"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600 transition-colors"
            >
              GitHub
            </a>
          </div>
        </footer>
      </main>

      {/* Authentication Modal */}
      <AuthModal />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
