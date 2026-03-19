import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { getHealth } from '../api/client'

function Home() {
  const [status, setStatus] = useState('loading')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function checkHealth() {
      try {
        const result = await getHealth()
        setData(result)
        setStatus('success')
      } catch (err) {
        setError(err.message)
        setStatus('error')
      }
    }

    checkHealth()
  }, [])

  return (
    <div style={{ padding: '20px' }}>
      <h1>NEWSRADAR</h1>
      <h2>Estado del backend</h2>

      {status === 'loading' && <p>Cargando...</p>}

      {status === 'success' && (
        <>
          <p style={{ color: 'green' }}>Backend OK</p>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </>
      )}

      {status === 'error' && (
        <>
          <p style={{ color: 'red' }}>Error de conexión</p>
          <p>{error}</p>
        </>
      )}
    </div>
  )
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  )
}