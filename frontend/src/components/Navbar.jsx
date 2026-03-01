import React from 'react'
import { NavLink } from 'react-router-dom'
import { useScrape } from '../ScrapeContext.jsx'

export default function Navbar() {
  const { status, count, stopScraping } = useScrape()

  return (
    <nav className="top-nav">
      <div className="nav-title">
        <span className="mark">
          <i className="fas fa-bolt" />
        </span>
        <span>Car Price Prediction</span>
      </div>

      <div className="nav-badges">
        <span className="pill">
          <i className="fas fa-signal" />
          scrape: {status}
        </span>

        {status === 'scraping' && (
          <span className="pill">
            <i className="fas fa-list-ol" />
            rows: {count}
          </span>
        )}

        {status === 'scraping' && (
          <button className="small btn-secondary" style={{ width: 'auto' }} onClick={stopScraping}>
            Stop
          </button>
        )}
      </div>

      <div className="nav-spacer" />

      <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <i className="fas fa-home" /> Home
      </NavLink>

      <NavLink to="/predict" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <i className="fas fa-gauge-high" /> Predict
      </NavLink>

      <NavLink to="/view-data" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <i className="fas fa-table" /> View Data
      </NavLink>

      <NavLink to="/about" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <i className="fas fa-info-circle" /> About
      </NavLink>
    </nav>
  )
}
