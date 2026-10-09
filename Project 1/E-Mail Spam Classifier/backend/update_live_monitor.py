import os

with open('../frontend/src/components/LiveMonitor.jsx', 'r') as f:
    content = f.read()

# Add states
if "const [monitoring, setMonitoring] = useState(false);" not in content:
    content = content.replace("const [selectedEmail, setSelectedEmail] = useState(null);", 
        "const [selectedEmail, setSelectedEmail] = useState(null);\n  const [monitoring, setMonitoring] = useState(false);")

# Add polling useEffect
polling_effect = """
  useEffect(() => {
    let interval;
    if (monitoring) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get('http://localhost:5000/api/gmail/latest');
          if (res.data.emails) {
            setEmails(res.data.emails);
          }
          if (res.data.monitoring !== undefined) {
            setMonitoring(res.data.monitoring);
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
"""
if "let interval;" not in content:
    content = content.replace("useEffect(() => {\n    checkStatus();\n  }, []);", 
        "useEffect(() => {\n    checkStatus();\n  }, []);\n" + polling_effect)

# Add watch handlers
watch_handlers = """
  const handleStartWatch = async () => {
    try {
      await axios.post('http://localhost:5000/api/gmail/watch');
      setMonitoring(true);
    } catch(err) {
      setError('Failed to start monitoring');
    }
  };

  const handleStopWatch = async () => {
    try {
      await axios.post('http://localhost:5000/api/gmail/stop-watch');
      setMonitoring(false);
    } catch(err) {
      setError('Failed to stop monitoring');
    }
  };
"""
if "const handleStartWatch" not in content:
    content = content.replace("const handleSync = async () => {", watch_handlers + "\n  const handleSync = async () => {")

# Add buttons
buttons = """
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
"""

# Replace the old sync button wrapper
old_button = """        <button 
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing emails...' : 'Sync Now'}
        </button>"""

if "Start Monitoring" not in content:
    content = content.replace(old_button, buttons)

with open('../frontend/src/components/LiveMonitor.jsx', 'w') as f:
    f.write(content)
print("Updated LiveMonitor.jsx")
