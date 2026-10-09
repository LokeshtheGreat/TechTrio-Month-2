import re
with open('frontend/src/components/LiveMonitor.jsx', 'r') as f:
    content = f.read()

# Find the definition of renderWatchStatus
pattern = r'\s*const renderWatchStatus = \(\) => \{[\s\S]+?  \};\n'
clean_content = re.sub(pattern, '', content)

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

  return (
    <div className="space-y-6">
"""

clean_content = clean_content.replace('  return (\n    <div className="space-y-6">\n      <div className="flex justify-between items-end">', status_component + '      <div className="flex justify-between items-end">')

with open('frontend/src/components/LiveMonitor.jsx', 'w') as f:
    f.write(clean_content)
