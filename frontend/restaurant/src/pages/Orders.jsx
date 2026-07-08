import { useState, useEffect } from "react";
import { useOutletContext, Link  } from "react-router-dom";
import { Box, Text, Card, VStack, Heading, CardDescription } from "@chakra-ui/react";
import { useAuth } from "../contexts/AuthContext";



export default function Orders() {
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

    const  { callAPI } = useAuth();

    const [ orders, setOrders ] = useState([]);
    // Function to get all user orders
    const getOrders = async () => {
        try {
            const res = await callAPI(
                `/orders/`, {auth: true}
            );
            if(!res.ok) throw new Error(`callAPI successfully but res code is ${res.status}`);

            const body = await res.json();
            body.reverse();

            for (let i = 0; i < body.length; i++) {
                body[i].datetime = body[i].datetime.split("T")[0];
            }
            setOrders(body);

        }
        catch (e) {
            console.log(e.message);
        }
    }

    useEffect(() => {
        getOrders();
    }, []);

    return (
        <Box fontSize={style.fontSize} fontFamily="cursive" minH={mainSize} color={style.color}>
            <Box my={"2vh"} mx={"2vw"} textAlign="left">
                <Heading size="4xl" fontFamily="cursive" mb="2vh">Orders</Heading>
                <VStack alignItems="center" gap="1.5vh">
                {
                    orders.map(o => (
                        <Link to={`/account/orders/${o.id}`} key={o.id}>
                            <Card.Root flexDirection="row" variant="elevated" color={style.color} _hover={{shadow: "lg"}} size={"md"} w="80vw"> 
                                <Card.Body bg="whitesmoke" fontSize="1rem">
                                    <CardDescription color={style.color}>
                                        <Card.Title  style={{ display: "inline-block" }} minW="1vw" mr="2vw">Order</Card.Title> Placed on {o.datetime}
                                    </CardDescription>
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