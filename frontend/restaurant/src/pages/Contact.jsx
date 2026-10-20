import { useState, useEffect } from "react";
import { useOutletContext  } from "react-router-dom";
import { Box, VStack, HStack, Image, Button, Text, Heading, Spacer } from "@chakra-ui/react";

export default function Contact() {
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
                <Heading mt="2vh" fontSize="3rem" fontFamily={style.fontFamily}>Contact us:</Heading>
                <Text ml="5vw" mt="3vh" fontSize={style.fontSize}>{"Email: email@gmail.com"}</Text>
                <Text ml="5vw"  fontSize={style.fontSize}>{"Phone number: 111-111-1111"}</Text>
                <Text ml="5vw"  fontSize={style.fontSize}>{"Address: Street, City, US"}</Text>
            </VStack>
        </Box>
    )
}