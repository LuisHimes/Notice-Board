import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/health')
      .then(response => setMessage(response.data.status))
      .catch(error => setMessage('Backend unavailable'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: '50px', textAlign: 'center' }}>
      <h1>React Frontend</h1>
      <p>Backend Status: {loading ? 'Loading...' : message}</p>
    </div>
  );
}

export default App;
