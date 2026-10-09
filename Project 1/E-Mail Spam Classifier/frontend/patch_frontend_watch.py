import re

with open('src/components/LiveMonitor.jsx', 'r') as f:
    content = f.read()

# Replace handleStartWatch
start_watch_old = """
  const handleStartWatch = async () => {
    try {
      const res = await axios.post('http://localhost:5000/api/gmail/watch');
      setMonitoring(true);
      if (res.data.expiration) {
        setExpiration(res.data.expiration);
      }
      setRenewalStatus('active');
    } catch(err) {
      setError('Failed to start monitoring');
    }
  };
"""

start_watch_new = """
  const [watchLoading, setWatchLoading] = useState(false);

  const handleStartWatch = async () => {
    if (watchLoading) return;
    setWatchLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/api/gmail/watch');
      setMonitoring(true);
      if (res.data.expiration) {
        setExpiration(res.data.expiration);
      }
      setRenewalStatus('active');
    } catch(err) {
      setError(err.response?.data?.error || 'Failed to start monitoring');
    } finally {
      setWatchLoading(false);
    }
  };
"""

if "const [watchLoading" not in content:
    content = content.replace(start_watch_old.strip('\n'), start_watch_new.strip('\n'))
    
# Replace the start monitoring button
btn_old = """
            {monitoring ? (
              <button 
                onClick={handleStopWatch}
                className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg font-medium hover:bg-red-100 transition-colors"
              >
                <BellOff className="w-4 h-4" />
                Stop Monitoring
              </button>
            ) : (
              <button 
                onClick={handleStartWatch}
                className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg font-medium hover:bg-blue-100 transition-colors"
              >
                <BellRing className="w-4 h-4" />
                Start Monitoring
              </button>
            )}
"""

btn_new = """
            {monitoring ? (
              <button 
                onClick={handleStopWatch}
                className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg font-medium hover:bg-red-100 transition-colors"
              >
                <BellOff className="w-4 h-4" />
                Stop Monitoring
              </button>
            ) : (
              <button 
                onClick={handleStartWatch}
                disabled={watchLoading}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${watchLoading ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-blue-50 text-blue-600 hover:bg-blue-100'}`}
              >
                <BellRing className={`w-4 h-4 ${watchLoading ? 'animate-pulse' : ''}`} />
                {watchLoading ? 'Starting...' : 'Start Monitoring'}
              </button>
            )}
"""
content = content.replace(btn_old.strip('\n'), btn_new.strip('\n'))

with open('src/components/LiveMonitor.jsx', 'w') as f:
    f.write(content)
