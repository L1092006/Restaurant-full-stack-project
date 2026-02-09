import { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export default function AuthProvider({ children }) {
    // FIXME: call the backend to verify if we can still use cookies to log in silently, if not, set log out state.
    const defaultUser = {
        username: "Loc",
        email: "loc@gmail.com"
    };
    const [user, setUser] = useState(defaultUser);
    const [isAuthenticated, setAutheticated] = useState(true);

    //FIXME: implement the login and logout fucntion
    const login = async (username, password) => {
        setUser(defaultUser);
        setAutheticated(true);
    }
    const logout = async () => {
        setUser(null);
        setAutheticated(false);
    }

    return (
        <AuthContext.Provider value={{user, isAuthenticated, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}