import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    fetch('/api/test')
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => setMessage('Error connecting to backend'))
  }, [])

  return (
    <>
      <h1>Video Detector Annotation Agent</h1>
      <div className="card">
        <p>Message from backend: {message}</p>
      </div>
    </>
  )
}

export default App