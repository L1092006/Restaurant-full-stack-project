import { Outlet } from "react-router-dom"
import { Box, Flex } from "@chakra-ui/react";
import Header from "./Header";
import Navbar from "./Navbar";
import Footer from "./Footer";

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
        <Flex bg="red" minH="100vh" direction="column">
            <Header/>
            <Navbar links={links}/>
            <Box flex="1">
                <Outlet/>
            </Box>
            <Footer/>
        </Flex>
    );
}