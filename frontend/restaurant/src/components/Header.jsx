import React from 'react'
import { Box, Flex, Text, Spacer, Avatar, Button, IconButton, Badge } from '@chakra-ui/react'
import { Link } from 'react-router-dom'
import { FaShoppingCart } from "react-icons/fa";

export default function Header() {
  return (
    <div>
    <Flex bg="green.800" height="5vh" alignItems="center" fontFamily="cursive" gap={2} px="1em">
        <Link to="/">
          <Text textStyle="3xl" color="white">The Restaurant</Text>
        </Link>
        <Spacer/>
        <Link to="/cart">
          <IconButton aria-label='Cart' variant="ghost" colorPalette="white" px="0.5em">
            <FaShoppingCart/>
            <Badge color="white" backgroundColor="green.700" borderRadius="full" variant="subtle">1</Badge>
          </IconButton>     
        </Link>
    </Flex>
    </div>
  )
}
