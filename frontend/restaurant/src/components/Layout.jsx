import { Outlet } from "react-router-dom"
import Header from "./Header";
import Navbar from "./Navbar";

export default function Layout() {
    const links = [
        {
            path: "/about",
            description: "About us"
        },
        {
            path: "/menu",
            description: "Menu"
        },
        {
            path: "/contact",
            description: "Contact us"
        }
    ]
    return (
        <>
            <Header/>
            <Navbar links={links}/>
            <Outlet/>
            {/* <Footer/> */}
        </>
    );
}