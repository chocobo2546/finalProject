import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Home from './Pages/Home.jsx'
import Predict from './Pages/Predict.jsx'
import ViewData from './Pages/ViewData.jsx'
import About from './Pages/About.jsx'
import { ScrapeProvider } from './ScrapeContext.jsx'

export default function App() {
  // ดึงค่า theme จาก localStorage ถ้าไม่มีให้เริ่มที่ 'dark'
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')

  // ทำงานทุกครั้งที่ theme มีการเปลี่ยนแปลง
  useEffect(() => {
    // กำหนด attribute ที่ <html> เพื่อให้ CSS Variables เปลี่ยนตาม
    document.documentElement.setAttribute('data-theme', theme);
    // บันทึกค่าลง Browser
    localStorage.setItem('theme', theme);
  }, [theme])

  // ฟังก์ชันสลับโหมดส่งให้ Navbar
  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'dark' ? 'light' : 'dark'));
  }

  return (
    <ScrapeProvider>
      <div className="bg-shell">
        <div className="grid-overlay" />
        {/* โยนค่า state และฟังก์ชันเข้าไปใน Navbar */}
        <Navbar theme={theme} toggleTheme={toggleTheme} />
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