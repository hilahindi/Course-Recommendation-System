import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState("Connecting to server...")

  useEffect(() => {
    axios.get('http://localhost:8000/api/test')
      .then(response => setMessage(response.data.message))
      .catch(error => setMessage("Connection failed: " + error.message))
  }, [])

  return (
    <div style={{ textAlign: 'center', marginTop: '50px' }}>
      <h1>Course Recommendation System</h1>
      <p style={{ color: 'blue' }}>{message}</p>
    </div>
  )
}

export default App