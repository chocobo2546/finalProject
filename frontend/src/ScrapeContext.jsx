import React, { createContext, useContext, useMemo, useRef, useState } from 'react'
import { apiDelete, openSSE } from './api.js'

const ScrapeContext = createContext(null)

export function ScrapeProvider({ children }) {
  const esRef = useRef(null)

  const [status, setStatus] = useState('idle') // idle | scraping | error
  const [error, setError] = useState('')
  const [lastItem, setLastItem] = useState(null)
  const [count, setCount] = useState(0)
  const [baseUrl, setBaseUrl] = useState('')

  function stopScraping() {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }
    setStatus('idle')
  }

  async function startScraping({ clearDb = true, baseUrl: url = '' } = {}) {
    setError('')
    setLastItem(null)
    setCount(0)
    setBaseUrl(url)

    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }

    if (clearDb) {
      await apiDelete('/cars')
    }

    setStatus('scraping')

    const qs = url ? `?base_url=${encodeURIComponent(url)}` : ''
    const es = openSSE(`/cars/stream${qs}`)
    esRef.current = es

    es.onmessage = (ev) => {
      try {
        const obj = JSON.parse(ev.data)
        if (obj && obj.error) {
          setError(String(obj.error))
          setStatus('error')
          return
        }
        setLastItem(obj)
        setCount((c) => c + 1)
      } catch {
        // ignore
      }
    }

    es.onerror = () => {
      setError('SSE disconnected. Check backend/CORS.')
      setStatus('error')
      stopScraping()
    }
  }

  const value = useMemo(
    () => ({
      status,
      error,
      lastItem,
      count,
      baseUrl,
      startScraping,
      stopScraping
    }),
    [status, error, lastItem, count, baseUrl]
  )

  return <ScrapeContext.Provider value={value}>{children}</ScrapeContext.Provider>
}

export function useScrape() {
  const ctx = useContext(ScrapeContext)
  if (!ctx) throw new Error('useScrape must be used within ScrapeProvider')
  return ctx
}
