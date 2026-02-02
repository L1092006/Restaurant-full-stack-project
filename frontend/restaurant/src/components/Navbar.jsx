import { Link, Flex, Text } from "@chakra-ui/react"
import { Link as RouterLink } from "react-router-dom"

export default function Navbar({ links }) {
    return (
        <Flex alignItems="center" justifyContent="space-around" h="3vh" bg="green.800">
            {links.map(link => <Link as={RouterLink} color="white" _hover={{ color: "green.500"}} to={link.path}>{link.description}</Link>)}
        </Flex>
    )
}