import React from 'react'
import { Box, Flex, Text, Spacer, Avatar, Button, IconButton, Badge } from '@chakra-ui/react'
import { Link } from 'react-router-dom'
import { FaShoppingCart } from "react-icons/fa";
import { useAuth } from '../contexts/AuthContext';

export default function Header() {
  const { user, isAuthenticated, login, logout } = useAuth();

  //FIXME: complete them
  const logoutHandler = () => logout();
  const loginHandler = () => login();

  
  return (
    <div>
    <Flex bg="green.800" height="5vh" alignItems="center" fontFamily="cursive" gap="1%" px="1%">
        <Link to="/">
          <Text textStyle="3xl" color="white">The Restaurant</Text>
        </Link>

        <Spacer/>

        <Link to="/cart">
          <Button aria-label='Cart' variant="ghost" colorPalette="white" px="0.5em" _hover={{backgroundColor: "green.700"}}>
            <FaShoppingCart/>
            {/* FIXME: get the number of items in cart from context */}
            <Badge color="white" backgroundColor="green.700" borderRadius="full" variant="subtle">1</Badge>
          </Button>     
        </Link>

        { isAuthenticated ? <>
          <Link to="/account">
            <Avatar.Root>
              <Avatar.Fallback name={user.username}/>
            </Avatar.Root>
          </Link>
          <Button onClick={logoutHandler} variant="outline" borderColor="green.700" _hover={{backgroundColor: "green.700"}}>
            Logout
          </Button>
        </>
        : <Button onClick={loginHandler} variant="outline" borderColor="green.700" _hover={{backgroundColor: "green.700"}}>Login / Signup</Button> }
    </Flex>
    </div>
  )
}
