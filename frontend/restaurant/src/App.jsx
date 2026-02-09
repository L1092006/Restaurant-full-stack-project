import { useMemo, memo } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Menu from './pages/Menu'
import Implementing from './pages/Implementing'

function App() {
  return (
      <Routes>
        <Route element={<Layout/>}>
          <Route path="/" element={<Home/>}/>
          <Route path="/login" element={<Login/>}/>
          <Route path="/menu" element={<Menu/>}/>
          {/* FIXME: Implement the pages for the below routes */}
          <Route path="/cart" element={<Implementing/>}/>
          <Route path="/account" element={<Implementing/>}/>
          <Route path="/about" element={<Implementing/>}/>
          <Route path="/menu:id" element={<Implementing/>}/>
          <Route path="/contact" element={<Implementing/>}/>
        </Route>
      </Routes>
  );
}

export default App
