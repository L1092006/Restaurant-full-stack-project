import { useState, useEffect } from "react";
import { useOutletContext, useParams  } from "react-router-dom";
import { Box, VStack, HStack, Image, Button, Text, Heading, Spacer } from "@chakra-ui/react";
import { toaster } from "../components/ui/toaster";
import { useAuth } from '../contexts/AuthContext';
import { useCart } from "../contexts/CartContext";
import  placeholder from "../assets/img/placeholder.jpg";

export default function SingleMenuItem() {
    // Visual and layout variables
    const style = {
        fontFamily: "cursive",
        fontSize: {
            base: "1rem",
            lg: "1.5rem"
            },
        color: "gray.700",
        h: {base: "8rem", lg: "12rem"}
    }
     // Get the size of the page
    const { mainSize } = useOutletContext();
    const { callAPI } = useAuth();
    const { id } = useParams();
    const { addItem } = useCart();

    const [ details, setDetails ] = useState({});

    useEffect(() => {
        const load = async () => {
            const response = await callAPI(`/items/${id}/`);
            if(!response.ok) throw new Error(`Response not ok, response: ${response}`);
            const data = await response.json();
            setDetails(data);
        }

        load();
    }, [callAPI]);


    // Handler for the add item button
    const addHandler = async (e) => {
        e.preventDefault();
        try {
            await addItem(details.id, 1);
        }
        catch (error) {
            // Log the error
            if (error.message === 'Not enough') {
                console.log(e);
            }
            // If there is another addItem call, tell the user to wait
            else if (error.message === 'Existing call') {
                toaster.create({
                    title: 'The web is busy.',
                    description: 'Please wait for a few seconds',
                    type: 'loading',
                    closable: true
                });
            }
        }
    }
    return (
        <Box  fontFamily={style.fontFamily} color={style.color}>
            <VStack mx="6vw" fontSize={style.fontSize} alignItems="flex-start" minH="auto" minH={mainSize}>
                <Image src={details.path ? item.path : placeholder} my="2vh" mx="auto" aspectRatio={6/3} maxH="30vh" borderRadius="2%"/>
                <HStack>
                    <Heading fontFamily={style.fontFamily} color={style.color} fontSize="2.5rem">{details.title}</Heading>
                    <Text color="red">{details.featured ? "Hot" : null}</Text>
                </HStack>
                <Text mb="1vh" mt="0.5vh">{`Stock: ${details.stock}`}</Text>
                <Text mb="2vh">{details.description}</Text>
                <Spacer/>
                <HStack my="3vh" fontSize="2rem" alignSelf="flex-end">
                    <Text mr="1.2rem">{`Price: $${details.price}`}</Text>
                    <Spacer/>
                    <Button onClick={(e) => addHandler(e)} variant="solid" size="2xl" ml="auto" color="white" backgroundColor="green.800" _hover={{backgroundColor: "green.700"}} fontSize="2rem">
                        Add to cart
                    </Button>
                </HStack>

            </VStack>
        </Box>
    )
}