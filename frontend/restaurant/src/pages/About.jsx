import { useState, useEffect } from "react";
import { useOutletContext  } from "react-router-dom";
import { Box, VStack, HStack, Image, Button, Text, Heading, Spacer } from "@chakra-ui/react";

export default function About() {
    // Visual and layout variables
    const style = {
        fontFamily: "cursive",
        fontSize: "1.5rem",
        color: "gray.700",
        h: {base: "8rem", lg: "12rem"}
    }
     // Get the size of the page
    const { mainSize } = useOutletContext();

    return (
        <Box  fontFamily={style.fontFamily} color={style.color} minH={mainSize}>
            <VStack mx="2vw" w="80vw" alignItems="flex-start">
                <Heading mt="2vh" fontSize="3rem" fontFamily={style.fontFamily}>About us:</Heading>
                <Text ml="5vw" mt="3vh" fontSize={style.fontSize}>{"This is a website for a restaurant."}</Text>
            </VStack>
        </Box>
    )
}