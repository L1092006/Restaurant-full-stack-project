import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'

function App() {
  return (
      <Routes>
        <Route element={<Layout/>}>
          <Route path="/" element={<Home/>}/>
        </Route>
      </Routes>
  );
}

export default App
