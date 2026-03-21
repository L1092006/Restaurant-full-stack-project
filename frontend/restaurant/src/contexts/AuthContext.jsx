import { createContext, useContext, useState, useCallback, useRef, useMemo, useEffect, useEffectEvent } from "react";
import { toaster } from "../components/ui/toaster";
import { useNavigate } from "react-router-dom";

const AuthContext = createContext();
const backUrl = import.meta.env.VITE_BACKEND_URL

export default function AuthProvider({ children }) {
    
    
    const [user, setUser] = useState(null);
    const [isAuthenticated, setAuthenticated] = useState(false);
    const [accessToken, setAccessToken] = useState(null);
    const accessTokenRef = useRef(null);

    const navigate = useNavigate();

    // refreshPromiseRef to ensure one refresh call at a time
    const refreshPromiseRef = useRef(null);

    // set the useState and useRef of access token
    const setToken = useCallback(token => {
        accessTokenRef.current = token;
        setAccessToken(token);
    }, [])

    // Return true if success, false otherwise
    const login = useCallback(async (username, password) => {
        let res = null;
        try {
            res = await fetch(`${backUrl}/auth/login/`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({username, password})
            });
        }
        catch (e) {
            return {
                success: false,
                message: "Network error"
            }
        }


        if(!res.ok) return {
            success: false,
            message: "Invalid username or password"
        };
        const data = await res.json();

        setAuthenticated(true);
        setToken(data.access_token);
        setUser(data.user);
        console.log(data.user.username);
        return {
            success: true,
            message: "Success!"
        };
    }, [setToken]);

    // Return true if success, false otherwise
    const logout = useCallback(async () => {
        let res = null;
        try {
            res = await fetch(`${backUrl}/auth/logout/`, {
                method: "POST",
                credentials: "include",
            })
        }
        catch (e) {
            return {
                success: false,
                message: "Network error"
            }
        }

        if(res.ok) {
            setUser(null);
            setAuthenticated(false);
            setToken(null);
            return {
                success: true,
                message: "Success!"
            };
        }
        return {
                success: false,
                message: "Error"
            };
        
    }, [setToken]);

    // Refresh helper function, throw error if fails. Guarantee one refresh at a time
    const callRefresh = useCallback(async () => {
        // If a concurrent call happens while a previous refresh call is being processed, return the promise from the previous ongoing call
        if(refreshPromiseRef.current) return refreshPromiseRef.current;

        const p = (async () => {
            let res = null;
            try {
                res = await fetch(`${backUrl}/auth/refresh/`, {
                    method: "POST",
                    credentials: "include"
                });
            }
            catch (e) {
                throw new Error("Network error")
            }

            const data = await res.json();
            if(!res.ok) {
                throw new Error(data.message);
            }
            
            setToken(data.access_token);
            setAuthenticated(true);
            return data.access_token;
        })();

        refreshPromiseRef.current = p;

        try { return await p } finally { refreshPromiseRef.current = null; }   
    }, [setToken]);

    // call API function that call the backend with all the necessary headers. It auto sends credentials if auth is true
    // If the response is not ok and auth is true, try refreshing tokens and get a new response to return. If the refresh fails, notify the user and force to log out and login again.
    // If any fetch throw error, display network error and throw an Error.
    // If the res is not ok, notify user and return the original res.
    // SUMMARY: callAPI only handles the authentication (by refresh and force to login if fail) and fetch error (by raise error). 
    // if authentication handler fails or any other issues occur, notify user and return the res as it is
    const callAPI = useCallback(async (postUrl, { options = {}, auth = false } = {}) => {
        const url = `${backUrl}${postUrl}`;
        const config = {
            credentials: "include",
            ...options,
            headers: {
                ...((auth && accessTokenRef.current) ? {"Authorization": `Bearer ${accessTokenRef.current}`} : {}),
                ...(options.headers || {})
            }
        };

        let res = null;
        // Call the api
        try {
            res = await fetch(url, config);
        }
        catch (e) {
            // Display a notification
                toaster.create({
                    title: "Network error",
                    description: "Please try again or wait and try later",
                    type: "error",
                    closable: true
                });
                throw new Error("Network error");
        }
        

        // If the call is successful, return the res.
        if(res && res.ok) {
            return res;
        }

        // If res is not ok and authentication is required, try refresh the tokens
        if(auth) {
            // Try to refresh the access token. If ok, call the original API again and return its res
            try{
                const newAccessToken = await callRefresh();
                config.headers = { ...config.headers, "Authorization": `Bearer ${newAccessToken}` }
                try {
                    const newRes = await fetch(url, config);
                    if(newRes.ok) return newRes;
                }
                catch {
                    throw new Error("Network error");
                }
            }
            catch (e) {
                // If can not refresh, log out and ask user to login again 
                if(e.message === "Network error") {
                    // Display a notification
                    toaster.create({
                        title: e.message,
                        description: "Please try again or wait and try later",
                        type: "error",
                        closable: true
                    });
                    throw e;
                }
                else {
                    const resLogout = await logout();
                    if(resLogout.success) {
                        // Display a notification
                        toaster.create({
                            title: "Timeout.",
                            description: "Please log in again",
                            type: "info",
                            closable: true
                        })

                        // Navigate to the login page
                        
                        navigate("/login");
                        return null;
                    }
                }
            }
        }

        // If we still fails, tell the user to try again later
        toaster.create({
            title: "Error",
            description: "Something went wrong. Please try again later",
            type: "error",
            closable: true
        })

        return res;
    }, [callRefresh, logout, navigate])


    // Call the backend to verify if we can log in silently, if not, set log out state.
    useEffect(() => {
        const init = async () => {
            try {
                // Refresh tokens
                const newAccessToken = await callRefresh();
                // Fetch user info
                const res = await fetch(`${backUrl}/users/me/`, {
                    credentials: "include",
                    headers: {
                        "Authorization": `Bearer ${newAccessToken}`
                    }
                });
                
                if(res.ok) {
                    const user = await res.json();
                    setUser(user);
                    
                }
            }
            catch (e) {
                console.log(e.message);
                logout();
            }
        }
        init();
    },[])

    const value = useMemo(() => ({ user, isAuthenticated, login, logout, callAPI }), [ user, isAuthenticated, login, logout, callAPI ])
    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}