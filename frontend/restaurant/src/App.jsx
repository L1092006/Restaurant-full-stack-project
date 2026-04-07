import { useMemo, memo } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Routes, Route } from 'react-router-dom'
import { Toaster } from "./components/ui/toaster"
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Menu from './pages/Menu'
import Signup from './pages/Signup'
import Implementing from './pages/Implementing'
import Cart from './pages/Cart'

function App() {
  return (
    <>
      <Toaster/>
      <Routes>
        <Route element={<Layout/>}>
          <Route path="/" element={<Home/>}/>
          <Route path="/login" element={<Login/>}/>
          <Route path="/menu" element={<Menu/>}/>
          <Route path='/signup' element={<Signup/>}/>
          <Route path="/cart" element={<Cart/>}/>
          {/* FIXME: Implement the pages for the below routes */}
          <Route path="/account" element={<Implementing/>}/>
          <Route path="/about" element={<Implementing/>}/>
          <Route path="/menu/:id" element={<Implementing/>}/>
          <Route path="/contact" element={<Implementing/>}/>
        </Route>
      </Routes>
    </>
  );
  
}

export default App
