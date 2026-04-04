import React, { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiGet, apiPost } from '../api.js'

export default function Predict() {
  const [searchParams] = useSearchParams()
  const brand = searchParams.get('brand') || ''

  // ===== Regularization buttons (0/1/2 selections) =====
  const [regL1, setRegL1] = useState(false)
  const [regL2, setRegL2] = useState(false)

  // Fix elastic alpha to 0.5 (no UI)
  const elasticAlpha = 0.5

  // If alpha is empty -> auto tune (do not show alpha in UI)
  const [alpha, setAlpha] = useState('')
  const [epochs] = useState(50000)

  // ===== Inputs =====
  const [year, setYear] = useState(2018)
  const [gear, setGear] = useState('อัตโนมัติ')
  const [mile, setMile] = useState(100000)

  const [busy, setBusy] = useState(false)
  const [predResult, setPredResult] = useState(null)
  const [error, setError] = useState('')
  
  // State สำหรับเก็บค่า R^2
  const [r2Score, setR2Score] = useState(null)

  // Map button states -> reg value used by backend
  const reg = useMemo(() => {
    if (!regL1 && !regL2) return 'none'
    if (regL1 && regL2) return 'elasticnet'
    if (regL1) return 'lasso'
    return 'ridge'
  }, [regL1, regL2])

  const penaltyLabel = useMemo(() => {
    if (!regL1 && !regL2) return 'no penalty'
    if (regL1 && regL2) return 'L1 + L2'
    if (regL1) return 'L1'
    return 'L2'
  }, [regL1, regL2])

  // ===== Car image from project folder (NO file import) =====
  const carImageSrc = useMemo(() => {
    const safeBrand = (brand || '').trim()
    if (!safeBrand) return '/car-images/default.jpg'
    return `/car-images/${safeBrand}.jpg`
  }, [brand])

  const YEAR_MIN = 2000
  const YEAR_MAX = new Date().getFullYear()

  // percent for positioning bubble above slider thumb
  const yearPercent = useMemo(() => {
    const denom = YEAR_MAX - YEAR_MIN
    if (denom <= 0) return 0
    const p = (year - YEAR_MIN) / denom
    return Math.min(1, Math.max(0, p))
  }, [year, YEAR_MIN, YEAR_MAX])

  const predPriceText = useMemo(() => {
    if (!predResult?.y_pred?.length) return '0'
    const raw = predResult.y_pred[0]
    const num = typeof raw === 'number' ? raw : Number(String(raw).replace(/,/g, ''))
    if (!Number.isFinite(num)) return String(raw)
    return num.toLocaleString('th-TH')
  }, [predResult])

  async function tuneAlphaIfNeeded(lam) {
    if (alpha !== '') return Number(alpha)
    const res = await apiGet(`/tune/alpha?reg=${reg}&lam=${lam}`)
    setAlpha(String(res.alpha))
    return res.alpha
  }

  async function handlePredictAll() {
    setBusy(true)
    setError('')
    setPredResult(null)
    setR2Score(null)

    try {
      const lam = 10
      const a = await tuneAlphaIfNeeded(lam)

      // รับค่า Model ที่เพิ่ง Train เสร็จ (เพื่อดึงค่า r2)
      const trainRes = await apiPost('/model/train', {
        reg,
        alpha: a,
        lambda: lam,
        elastic_alpha: elasticAlpha,
        epochs,
        standardize: true,
        center_y: true,
        brand
      })
      
      if (trainRes && trainRes.r2 !== undefined) {
        setR2Score(trainRes.r2)
      }

      const res = await apiPost('/model/predict', {
        items: [{ year, gear, mile }]
      })
      setPredResult(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="dashboard-container predict-dashboard">
        {/* LEFT: controls */}
        <div className="form-section">
          <div className="app-header">
            <h2>
              PRE<span>DICT</span>
            </h2>
            <p>High-Precision Car Valuation System</p>
          </div>

          {/* ===== Year slider + bubble on thumb ===== */}
          <div className="input-group">
            <label>Year</label>
            <div className="range-wrap">
              <div
                className="range-bubble"
                style={{ left: `calc(${(yearPercent * 100).toFixed(4)}% )` }}
                aria-hidden="true"
              >
                {year}
              </div>

              <input
                className="year-slider"
                type="range"
                min={YEAR_MIN}
                max={YEAR_MAX}
                step="1"
                value={year}
                onChange={(e) => setYear(+e.target.value)}
              />

              <div className="range-minmax muted">
                <span>{YEAR_MIN}</span>
                <span>{YEAR_MAX}</span>
              </div>
            </div>
          </div>

          {/* ===== Gear toggle (single choice) ===== */}
          <div className="input-group">
            <label>Transmission (ระบบเกียร์)</label>
            <div className="toggle-group">
              <button
                type="button"
                className={`toggle-btn ${gear === 'อัตโนมัติ' ? 'active' : ''}`}
                aria-pressed={gear === 'อัตโนมัติ'}
                onClick={() => setGear('อัตโนมัติ')}
              >
                อัตโนมัติ
              </button>

              <button
                type="button"
                className={`toggle-btn ${gear === 'ธรรมดา' ? 'active' : ''}`}
                aria-pressed={gear === 'ธรรมดา'}
                onClick={() => setGear('ธรรมดา')}
              >
                ธรรมดา
              </button>
            </div>
          </div>

          {/* ===== Mileage ===== */}
          <div className="input-group">
            <label>Mileage (เลขไมล์สะสม)</label>
            <input type="number" value={mile} onChange={(e) => setMile(+e.target.value)} />
          </div>

          {/* ===== Regularization toggles (multi-choice) ===== */}
          <div className="input-group">
            <label>Regularization (Penalty)</label>
            <div className="toggle-group">
              <button
                type="button"
                className={`toggle-btn ${regL1 ? 'active' : ''}`}
                aria-pressed={regL1}
                onClick={() => setRegL1((v) => !v)}
                title="L1 penalty"
              >
                L1
              </button>

              <button
                type="button"
                className={`toggle-btn ${regL2 ? 'active' : ''}`}
                aria-pressed={regL2}
                onClick={() => setRegL2((v) => !v)}
                title="L2 penalty"
              >
                L2
              </button>

              <span className="badge" style={{ alignSelf: 'center' }}>
                <i className="fas fa-sliders" style={{ marginRight: 8, color: '#ff3333' }} />
                {penaltyLabel}
              </span>
            </div>
          </div>

          <button className="btn-predict" onClick={handlePredictAll} disabled={busy}>
            {busy ? 'PROCESSING...' : 'Predict'}
          </button>

          {error && (
            <div className="card error-card muted">
              <div style={{ fontWeight: 900, marginBottom: 6 }}>
                <i className="fas fa-triangle-exclamation" style={{ marginRight: 8, color: '#ff8a8a' }} />
                Error
              </div>
              {error}
            </div>
          )}
        </div>

        {/* RIGHT: results (match car.zip) */}
        <div className="visual-section">
          <img
            src={carImageSrc}
            className={`car-image-bg ${predResult ? 'active' : ''}`}
            alt="Car Background"
            onError={(e) => {
              e.currentTarget.src = '/car-images/img.jfif'
            }}
          />

          <div className="visual-overlay" />

          {/* Welcome center */}
          <div className="welcome-msg" style={{ opacity: predResult ? 0 : 1 }}>
            <i className="fas fa-gauge-high" />
            <h3>AI VALUATION</h3>
            <p className="welcome-sub">READY TO ANALYZE</p>
          </div>

          {/* Top-right HUD */}
          <div className={`result-hud ${predResult ? 'active' : ''}`}>
            {/* <span className="price-label">ESTIMATED PRICE (ราคาประเมิน)</span> */}
            <div className="price-value">
              <span>{predPriceText}</span>
              <span className="price-currency">฿</span>
            </div>
            {/* <p className="hud-note">*Based on trained model output</p> */}
          </div>
          
          {/* Bottom-right HUD สำหรับแสดงค่า R^2 */}
          <div className={`metrics-hud ${predResult ? 'active' : ''}`}>
            <div className="metric-box">
              <span className="metric-label">R²</span>
              <span className="metric-value">
                {r2Score !== null ? (r2Score * 100).toFixed(2) + '%' : '--'}
              </span>
            </div>
          </div>

          {/* Loader overlay inside result area (car.zip style) */}
          <div className="loader-overlay" style={{ display: busy ? 'flex' : 'none' }}>
            <div className="spinner" />
            <p className="loader-text">PROCESSING...</p>
          </div>
        </div>
      </div>
    </>
  )
}