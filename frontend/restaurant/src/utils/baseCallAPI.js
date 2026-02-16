import { toaster } from "../components/ui/toaster";
import { useNavigate } from "react-router-dom";

export default async function baseCallAPI(url, options={}, logout) {
    const config = {
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        ...options
    };

    // Call the api
    const res = await fetch(url, config)

    // If the call is successfully authenticated, return the res
    if(res.status != 401) {
        return res;
    }


    // Try to refresh the access token. If ok, call the original API again and return its res
    const backUrl = import.meta.env.VITE_BACKEND_URL
    const reRes = await fetch(`${backUrl}auth/refresh/`, config);
    if(reRes.ok) {
        return fetch(url, config);
    }


    // If can not refresh, log out and ask user to login again 
    if(logout()) {
        // Display a notification
        toaster.create({
            title: "Timeout.",
            description: "Please log in again",
            type: "info",
            closable: true
        })

        // Navigate to the login page
        const navigate = useNavigate();
        navigate("/login");
    }

    // If we can't even logout, tell the user to try again later
    toaster.create({
        title: "Error",
        description: "Something went wrong. Please try again later",
        type: "error",
        closable: true
    })

    return res;
}