import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useScrape } from '../ScrapeContext.jsx'

const CAR_OPTIONS = [
  { value: 'https://chobrod.com/car-honda-civic/p', label: 'Honda Civic' },
  { value: 'https://chobrod.com/car-toyota-hilux-revo/p', label: 'Toyota Hilux Revo' }
]

export default function Home() {
  const navigate = useNavigate()
  const { startScraping } = useScrape()
  const [baseUrl, setBaseUrl] = useState(CAR_OPTIONS[0].value)

  async function handleScrapping() {
    await startScraping({ clearDb: true, baseUrl })
    navigate(`/predict?base_url=${encodeURIComponent(baseUrl)}`)
  }

  return (
    <div className="hero">
      <div className="hero-card">
        <h1 style={{ marginBottom: 6 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
            <span className="badge" style={{ background: 'rgba(225,6,0,.14)', borderColor: 'rgba(225,6,0,.45)' }}>
              <i className="fas fa-car" style={{ marginRight: 8, color: '#ff3333' }} />
              Redline UI
            </span>
            Home
          </span>
        </h1>

        {/* <div className="hero-sub">
          เลือกรุ่นรถเพื่อเริ่ม <b>Scrapping</b> (SSE) — โค้ดฝั่ง API/การรับส่งยังคงเหมือนเดิมจากไฟล์
          <b> frontend.zip</b>
        </div> */}

        <div className="hero-actions">
          <div>
            <label>Car model</label>
            <select value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}>
              {CAR_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>

            {/* <div className="muted" style={{ marginTop: 8 }}>
              ระบบจะล้างข้อมูลเดิม (DELETE /cars) แล้วเริ่ม stream (SSE /cars/stream?base_url=...)
            </div> */}
          </div>

          <button onClick={handleScrapping}>
            Scrapping <i className="fas fa-arrow-right" style={{ marginLeft: 10 }} />
          </button>
        </div>
      </div>
    </div>
  )
}
