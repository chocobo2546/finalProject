import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Home from './Pages/Home.jsx'
import Predict from './Pages/Predict.jsx'
import ViewData from './Pages/ViewData.jsx'
import About from './Pages/About.jsx'
import { ScrapeProvider } from './ScrapeContext.jsx'

export default function App() {
  return (
    <ScrapeProvider>
      <div className="bg-shell">
        <div className="grid-overlay" />
        <Navbar />
        <main className="main">
          <div className="container">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/predict" element={<Predict />} />
              <Route path="/view-data" element={<ViewData />} />
              <Route path="/about" element={<About />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </ScrapeProvider>
  )
}
