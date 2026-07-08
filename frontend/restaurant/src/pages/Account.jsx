import { useOutletContext, Link  } from "react-router-dom";
import { Box, Text, Card, VStack, Heading } from "@chakra-ui/react";

export default function Account() {
    // Visual and layout variables
    const { mainSize } = useOutletContext();
    const style = {
        fontFamily: "cursive",
        fontSize: {
        base: "0.5rem",
        lg: "1rem"
        },
        color: "gray.700",
        h: {base: "8rem", lg: "12rem"}
    }

    // The list of all related links
    const links = [
        {
            link: '/account/orders',
            title: "Order",
            description: "View your orders"
        }
    ]

    return (
        <Box fontSize={style.fontSize} fontFamily="cursive" minH={mainSize} color={style.color}>
            <Box my={"2vh"} mx={"2vw"} textAlign="left">
                <Heading size="4xl" fontFamily="cursive" mb="2vh">Account</Heading>
                <VStack alignItems="center">
                {
                    links.map(l => (
                        <Link to={l.link}>
                            <Card.Root flexDirection="row" variant="elevated" color={style.color} _hover={{shadow: "lg"}} size={"md"} w="80vw"> 
                                
                                <Card.Body bg="whitesmoke" fontSize="1rem">
                                    <Card.Title>{l.title}</Card.Title>
                                    {l.description}
                                </Card.Body>
                            </Card.Root>
                        </Link>
                    ))
                }
                
            </VStack>
            </Box>
            
        </Box>
    )
}