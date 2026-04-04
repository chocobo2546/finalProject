import React from 'react'
import { NavLink } from 'react-router-dom'
import { useScrape } from '../ScrapeContext.jsx'

// รับ Props theme และ toggleTheme มาจาก App.jsx
export default function Navbar({ theme, toggleTheme }) {
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

      {/* ปุ่มสลับ Theme (Dark/Light) */}
      <button 
        onClick={toggleTheme} 
        className="nav-item theme-toggle-btn"
        title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
        style={{ 
          padding: '8px 12px', 
          marginLeft: '5px', 
          cursor: 'pointer',
          background: 'transparent',
          border: '1px solid var(--border)'
        }}
      >
        {theme === 'dark' ? (
          <><i className="fas fa-sun" style={{ color: '#ffb300', opacity: 1 }}></i></>
        ) : (
          <><i className="fas fa-moon" style={{ color: '#555', opacity: 1 }}></i></>
        )}
      </button>

    </nav>
  )
}