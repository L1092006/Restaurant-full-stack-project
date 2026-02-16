import { createContext, useContext, useState } from "react";
import baseCallAPI from "../utils/baseCallAPI";

const AuthContext = createContext();
const backUrl = import.meta.env.VITE_BACKEND_URL

export default function AuthProvider({ children }) {
    // FIXME: call the backend to verify if we can still use cookies to log in silently, if not, set log out state.
    
    const [user, setUser] = useState(null);
    const [isAuthenticated, setAutheticated] = useState(false);

    // Return true if success, false otherwise
    const login = async (username, password) => {
        const res = await fetch(`${backUrl}auth/login/`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({username, password})
        });

        if(!res.ok) return false;
        const data = await res.json();

        setUser({username, email: data.email});
        setAutheticated(true);
        return true
    }
    // Return true if success, false otherwise
    const logout = async () => {
        const res = await fetch(`${backUrl}auth/logout/`, {
            method: "POST",
            credentials: "include",
        })

        if(res.ok) {
            setUser(null);
            setAutheticated(false);
            return true;
        }
        return false;
        
    }

    // Wrapper function which auto provides logout to baseCallAPI
    const callAPI = (url, options={}) => baseCallAPI(url, options, logout);

    return (
        <AuthContext.Provider value={{user, isAuthenticated, login, logout, callAPI }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}