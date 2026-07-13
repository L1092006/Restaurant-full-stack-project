import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import {BrowserRouter} from "react-router-dom"
import { Provider } from "./components/ui/provider"
import AuthProvider from './contexts/AuthContext.jsx'
import CartProvider from './contexts/CartContext.jsx'
import ChatbotProvider from './contexts/ChatbotContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Provider>
      <BrowserRouter>
        <AuthProvider>
          <CartProvider>
             <ChatbotProvider>
                <App/>
             </ChatbotProvider>
          </CartProvider>
        </AuthProvider>
      </BrowserRouter>
    </Provider>
  </StrictMode>,
)
