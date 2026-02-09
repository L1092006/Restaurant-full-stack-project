import { Outlet } from "react-router-dom";
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

    const size = {
        header: "5vh",
        navbar: "3vh",
        footer: "7vh"
    }
    return (
        <Flex minH="100vh" direction="column">
            <Header headerSize={size.header}/>
            <Navbar links={links}/>
            <Box flex="1">
                <Outlet context={{mainSize: "85vh"}}/>
            </Box>
            <Footer footerSize={size.footer}/>
        </Flex>
    );
}