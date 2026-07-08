import { Box, VStack, HStack, Spacer, Text, Card, Image, Heading, IconButton, Button } from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { useOutletContext, Link, useNavigate } from "react-router-dom";
import { toaster } from "../components/ui/toaster";
import { IoMdAdd, IoMdRemove } from "react-icons/io";
import { useCart } from "../contexts/CartContext";
import  placeholder from "../assets/img/placeholder.jpg";

export default function Cart() {
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

// Logic variables
  const { cartItems, loadCart, addItem } = useCart();
  
  const navigate = useNavigate();
  // Used to check if there is any item whose quantity exceed stock. False if there is
  const [ validCart, setValidCart ] = useState(true);

  // List of all invalid items
  const [ invalidItems, setInvalidItems ] = useState([]);

  // Handler for the add item button. Take the menuitem and the number to add to the cartitem quantity
  const addHandler = async (e, item, addNumber) => {
      e.preventDefault();
      try {
          await addItem(item.id, addNumber);
      }
      catch (error) {
          // If the stock of an item needs to be updated, set the validCart to false if needed
          if (error.message === 'Not enough') {
              setValidCart(false);
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

  //   Helper functions to calculate the total price of all items 
  const get_total_price = (tax) => {
    let sum = 0;
    for (const item of cartItems) {
        if(tax) sum += item.total_price_after_tax;
        else sum += item.total_price;
    }

    return sum
  }

  // Load cart and initialize validCart. Set it to false if needed.
  useEffect(() => {loadCart()}, []);
  useEffect(() => {
    setValidCart(true);
    const invalidItems = [];
    for(const item of cartItems) {
        if(item.quantity > item.menuitem.stock) {
            setValidCart(false);
            invalidItems.push(item);
        }
    }

    setInvalidItems(invalidItems);
    
  },[cartItems])

  // FIXME: check if eveything is correct. Add minus button and display warning if validCart is false
  return (
    <Box fontSize={style.fontSize} fontFamily="cursive">
        <VStack w="90vw" mx="auto" my="2vh" gap='2vh' alignItems="center" minH={mainSize}>
        {
            cartItems.map(item => (
            <Link to={`/menu/${item.menuitem.id}`} key={item.id}>
                <Card.Root flexDirection="row"  color={style.color} colorPalette="white" _hover={{shadow: "lg"}} h={style.h}> 
                    <Image src={item.menuitem.path ? item.menuitem.path : placeholder} aspectRatio={{base: 1/1, lg: 6/4}}/>
                    <Card.Body bg="whitesmoke" fontSize="1rem">
                        <Heading as="h3" mb="0.5rem">{item.menuitem.title}</Heading>
                        <Text mb="auto" overflow="hidden">{item.menuitem.description}</Text>
                        <HStack fontSize='1.2rem'>
                            <Spacer/>
                            <Text mr="1.2rem">{`Price: $${item.total_price}`}</Text>
                            <IconButton onClick={(e) => addHandler(e, item.menuitem, -1)} variant="solid" size="xs" ml="auto" color="white" backgroundColor="green.800" _hover={{backgroundColor: "green.700"}}>
                            <IoMdRemove/>
                            </IconButton>
                            <IconButton onClick={(e) => addHandler(e, item.menuitem, 1)} variant="solid" size="xs" ml="auto" color="white" backgroundColor="green.800" _hover={{backgroundColor: "green.700"}}>
                            <IoMdAdd/>
                            </IconButton>
                            <Text ml="1.2rem">{item.quantity}</Text>
                        </HStack>
                        {(item.quantity > item.menuitem.stock) ? <Text color="red.500">Warning: Low stock. There are currently only {item.menuitem.stock} items in stock.</Text> : ''}
                    
                    </Card.Body>
                </Card.Root>
            </Link>
            ))
        }
        <Spacer/>
        <Box w="full"  textAlign='left' color={style.color} fontSize="1.5rem">
            {/* Price section */}
            <Text>
                Total price: ${get_total_price(false).toFixed(2)}
                <br/>
                Total price after tax: ${get_total_price(true).toFixed(2)}
            </Text>
            <Box my='1vh'>
                {invalidItems.map((item) => (
                    <Text fontSize="1rem" color="red.500">There are not enough {item.menuitem.title} in stock. Please change the quantity to checkout.</Text>
                ))}
            </Box>

            {/* <Link to="/checkout" bg='red' ml="10rem">
                <Button link _hover={{backgroundColor: "green.700"}} bg='green.800' color='white' disabled={!validCart}>
                 Checkout
                </Button>     
            </Link> */}
            <Box textAlign="right">
                <Button onClick={() => {navigate("/checkout")}} size={{base: "sm", md: "lg", lg: "2xl"}}  _hover={{backgroundColor: "green.700"}} bg='green.800' color='white' disabled={!validCart}>
                    Checkout
                </Button>
            </Box>
             
        </Box>
        </VStack>
    </Box>
    
  );
  
}

// To do: 
//        Add Total Price and Warning section. Block check out if invalid. Enclose all in a responsive flex. Resize the card