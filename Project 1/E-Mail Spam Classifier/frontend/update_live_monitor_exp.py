import re

with open('src/components/LiveMonitor.jsx', 'r') as f:
    content = f.read()

# 1. Add states
state_addition = """
  const [expiration, setExpiration] = useState(null);
  const [renewalStatus, setRenewalStatus] = useState('active');
  const [serverTime, setServerTime] = useState(null);
"""
if "const [expiration, setExpiration] = useState(null);" not in content:
    content = content.replace("const [monitoring, setMonitoring] = useState(false);", "const [monitoring, setMonitoring] = useState(false);\n" + state_addition)

# 2. Update polling
polling_replacement = """
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
"""
content = re.sub(r'          if \(res\.data\.monitoring !== undefined\) \{\n            setMonitoring\(res\.data\.monitoring\);\n          \}', polling_replacement.strip('\n'), content)

# 3. Handle manual renew
renew_handler = """
  const handleRenewWatch = async () => {
    try {
      const res = await axios.post('http://localhost:5000/api/gmail/renew-watch');
      setExpiration(res.data.expiration);
      setRenewalStatus('active');
    } catch(err) {
      setError('Failed to renew monitoring');
    }
  };
"""
if "const handleRenewWatch" not in content:
    content = content.replace("const handleStopWatch = async () => {", renew_handler + "\n  const handleStopWatch = async () => {")

# 4. Watch status component
status_component = """
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
"""
if "const renderWatchStatus" not in content:
    content = content.replace("return (", status_component + "\n  return (")

# 5. Render it in the header
header_replacement = """
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
"""
content = re.sub(r'        <div>\n          <h2 className="text-2xl font-bold text-gray-900">Live Monitor</h2>\n          <p className="text-gray-500 flex items-center gap-2">\n            Connected to: <span className="font-semibold">\{userEmail\}</span>\n            <button onClick=\{handleDisconnect\} className="text-sm text-red-500 hover:underline ml-2">\n              \[ Disconnect \]\n            </button>\n          </p>\n        </div>', header_replacement.strip('\n'), content)

with open('src/components/LiveMonitor.jsx', 'w') as f:
    f.write(content)
