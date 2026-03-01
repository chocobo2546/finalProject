// frontend/src/pages/ViewData.jsx
import React, { useEffect, useMemo, useState } from 'react'
import { apiGet } from '../api.js'
import { useScrape } from '../ScrapeContext.jsx'

const MODEL_LABEL_BY_BASE_URL = {
  'https://chobrod.com/car-honda-civic/p': 'Honda Civic',
  'https://chobrod.com/car-toyota-hilux-revo/p': 'Toyota Hilux Revo'
}

export default function ViewData() {
  const { baseUrl } = useScrape()

  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // pagination
  const [page, setPage] = useState(1)
  const pageSize = 10

  const selectedModelLabel = useMemo(() => {
    const key = (baseUrl || '').trim()
    return MODEL_LABEL_BY_BASE_URL[key] || ''
  }, [baseUrl])

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(rows.length / pageSize))
  }, [rows.length])

  const pageRows = useMemo(() => {
    const start = (page - 1) * pageSize
    return rows.slice(start, start + pageSize)
  }, [rows, page])

  async function load() {
    setLoading(true)
    setError('')
    try {
      // IMPORTANT: keep API behavior same as original frontend.zip
      const res = await apiGet('/cars')
      const data = Array.isArray(res.data) ? res.data : []
      setRows(data)
      setPage(1)
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  function goFirst() {
    setPage(1)
  }

  function goLast() {
    setPage(totalPages)
  }

  function prevPage() {
    setPage((p) => Math.max(1, p - 1))
  }

  function nextPage() {
    setPage((p) => Math.min(totalPages, p + 1))
  }

  return (
    <>
      {loading && (
        <div className="loading-overlay">
          <div className="loader" />
        </div>
      )}

      <div className="card">
        <h1>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
            <span className="badge" style={{ background: 'rgba(225,6,0,.14)', borderColor: 'rgba(225,6,0,.45)' }}>
              <i className="fas fa-table" style={{ marginRight: 8, color: '#ff3333' }} />
              Data
            </span>
            View Data
          </span>
        </h1>

        <div className="top-actions">
          <button className="small btn-secondary" onClick={load} disabled={loading}>
            {loading ? 'Loading...' : 'Reload'}
          </button>

          <span className="badge">
            <i className="fas fa-list-ol" style={{ marginRight: 8, color: '#ff3333' }} />
            rows: {rows.length}
          </span>

          {selectedModelLabel ? (
            <span className="badge">
              <i className="fas fa-tag" style={{ marginRight: 8, color: '#ff3333' }} />
              {selectedModelLabel}
            </span>
          ) : null}
        </div>

        {error && (
          <div style={{ marginTop: 12 }} className="card">
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Error</div>
            <div className="muted">{error}</div>
          </div>
        )}

        <hr />

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Title</th>
                <th>Year</th>
                <th>Gear</th>
                <th>Mile</th>
                <th>Price</th>
                <th>URL</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((r, i) => {
                const rowTitle = selectedModelLabel
                return (
                  <tr key={`${r.url || ''}-${(page - 1) * pageSize + i}`}>
                    <td>{(page - 1) * pageSize + i + 1}</td>
                    <td title={rowTitle}>{rowTitle}</td>
                    <td>{r.year ?? '-'}</td>
                    <td>{r.gear ?? '-'}</td>
                    <td>{r.mile ?? '-'}</td>
                    <td>{r.price ?? '-'}</td>
                    <td>
                      {r.url ? (
                        <a href={r.url} target="_blank" rel="noreferrer">
                          open
                        </a>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                )
              })}

              {pageRows.length === 0 && (
                <tr>
                  <td colSpan={7} className="muted" style={{ padding: 14 }}>
                    No rows
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <hr />

        {/* pagination controls centered */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 10,
            flexWrap: 'wrap'
          }}
        >
          <button className="small btn-secondary" onClick={goFirst} disabled={page <= 1}>
            First
          </button>

          <button className="small btn-secondary" onClick={prevPage} disabled={page <= 1}>
            Prev
          </button>

          <span className="badge">
            Page {page} / {totalPages}
          </span>

          <button className="small btn-secondary" onClick={nextPage} disabled={page >= totalPages}>
            Next
          </button>

          <button className="small btn-secondary" onClick={goLast} disabled={page >= totalPages}>
            Last
          </button>
        </div>
      </div>
    </>
  )
}
