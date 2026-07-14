import { Box, VStack, HStack, Spacer, Text, Card, Image, Heading, IconButton, Button } from "@chakra-ui/react";
import { useState, useEffect, useCallback } from "react";
import { useOutletContext, useParams, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { toaster } from "../components/ui/toaster";
import  placeholder from "../assets/img/placeholder.jpg";

export default function SingleOrder() {
  // Visual and layout variables
  const { mainSize } = useOutletContext();
  const style = {
      fontFamily: "cursive",
      fontSize: {
        base: "0.5rem",
        lg: "1rem"
        },
      color: "gray.700",
      h: {base: "6rem", lg: "9rem"}
  }
  //   Get the id parameter from the url
  const { id } = useParams();

  const { callAPI } = useAuth();
  const [ order, setOrder ] = useState({});
   const [ orderItems, setOrderItems ] = useState([]);
//   Get order and its items
  const getItems = useCallback(async () => {
    try {
        const res = await callAPI(
            `/orders/${id}/`, {auth: true}
        );
        if(!res.ok) throw new Error(`callAPI successfully but res code is ${res.status}`);

        const body = await res.json();
        setOrderItems(body.orderitem_set);
        setOrder(body);

    }
    catch (e) {
        console.log(e.message);
    }
  }, [callAPI])

  useEffect(() => {
    getItems();
  },[])

//   Calculate the total price
  const get_total_price = (tax) => {
    let sum = 0;
    for (const item of orderItems) {
        if(tax) sum += item.total_price_after_tax;
        else sum += item.total_price;
    }

    return sum;
  }

//   Send a patch request to cancel
  const cancel = async () => {
    try {
        const res = await callAPI(`/orders/${id}/`, {
            options: {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ status: 'canceled' })
                }, 
            auth: true
        });

        if(!res.ok) throw new Error(`callAPI successfully but res code is ${res.status}`);
        await getItems();
    }
    catch (e) {
        console.log(e.message);
    }
  }

  // FIXME: check if eveything is correct. Add minus button and display warning if validCart is false
  return (
    <Box fontSize={style.fontSize} fontFamily="cursive"  color={style.color}>
        <VStack w="90vw" mx="auto" my="2vh" gap='2vh' alignItems="center" minH={mainSize}>
        <Heading size="4xl" alignSelf={"flex-start"}>Status: {order && order.status} </Heading>
        {
            orderItems.map(item => (
            <Link to={`/menu/${item.menuitem.id}`} key={item.id}>
                <Card.Root flexDirection="row"  color={style.color} colorPalette="white" _hover={{shadow: "lg"}} h={style.h} maxW={"50rem"} overflow={"hidden"}> 
                    <Image src={item.menuitem.path ? item.menuitem.path : placeholder} aspectRatio={{base: 1/1, lg: 6/4}}/>
                    <Card.Body bg="whitesmoke" fontSize="1rem">
                        <Heading as="h3" mb="0.5rem">{item.menuitem.title}</Heading>
                        <Text mb="auto" overflow="hidden">{item.menuitem.description}</Text>
                        <HStack fontSize='1.2rem'>
                            <Spacer/>
                            <Text ml="1.2rem">Quantity: {item.quantity}</Text>
                            <Text mr="1.2rem">{`Price: $${item.total_price}`}</Text>
                        </HStack>
                    </Card.Body>
                </Card.Root>
            </Link>
            ))
        }
        <Spacer/>
        <HStack w="full" textAlign='left' color={style.color} fontSize="1.5rem">
            {/* Price section */}
            <Text>
                Total price: ${get_total_price(false).toFixed(2)}
                <br/>
                Total price after tax: ${get_total_price(true).toFixed(2)}
            </Text>
            <Spacer/>

             <Button size={{base: "sm", md: "lg", lg: "2xl"}} _hover={{backgroundColor: "red.700"}} bg='green.800' color='white' onClick={cancel} disabled={!order.status || order.status == "canceled"}>
                    Cancel
            </Button>
        </HStack>
        </VStack>
    </Box>
    
  );
  
}
