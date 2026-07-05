import { Box, Button, ButtonGroup, Steps, Flex, Field, Input, Card, Text, Image, Spacer } from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { useOutletContext, Link } from "react-router-dom";
import { toaster } from "../components/ui/toaster";
import { IoMdAdd, IoMdRemove } from "react-icons/io";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import  { useForm } from "react-hook-form";
import { useCart } from "../contexts/CartContext";
import { useAuth } from "../contexts/AuthContext";
import  placeholder from "../assets/img/placeholder.jpg";

// Define the schema for the form
const schema = z.object({
    // Contact info
    first_name: z.string().min(1, "This can not be empty"),
    last_name: z.string().min(1, "This can not be empty"),
    email: z.string().email("Invalid email"),
    phone_number: z.string().regex(/^\d{10}$/, "Enter a valid phone number"),

    // Delivery info
    address: z.string().min(1, "Enter a valid address"),
    optional_details: z.string().optional(),
    city: z.string().min(1, "Enter a valid city"),
    state: z.string().min(1, "Enter a valid state"),
    postal_code: z.string().regex(/^\d{5,9}$/, "Enter a valid state")
})

export default function Checkout() {
  // Visual and layout variables
  const { mainSize } = useOutletContext();
  const style = {
      fontFamily: "cursive",
      fontSize: {
        base: "1rem",
        lg: "1rem"
        },
      color: "gray.700",
    //   The height of card of each item
      cardH: {base: "6rem", lg: "6rem"},
      cardW: {lg: "50vw"},

      gap: "1.5rem",
      formW: {base: "70vw", lg: "50vw"},
      //   The gap between label and its input
      labelB: "0.1rem",
      //   The mx of the box containing form and step component
      mx: {base: "5vw", lg: "10vw"}
  }

// Logic variables
  const { cartItems, loadCart, addItem } = useCart();


  //   Helper functions to calculate the total price of all items 
  const get_total_price = (tax) => {
    let sum = 0;
    for (const item of cartItems) {
        if(tax) sum += item.total_price_after_tax;
        else sum += item.total_price;
    }

    return sum
  }

  // Load cart 
  useEffect(() => loadCart, []);
  
  const { callAPI } = useAuth();

  // Form Hook
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm({ resolver: zodResolver(schema), mode: 'onChange' });

  const mySubmitHandler = async (data) => {
    let res = null;
    try {
        res = await callAPI(
            '/orders/', {options: {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }, auth: true}
        );
        if(!res.ok) throw new Error('callAPI successfully but res is not true');
    }
    catch (e) {
        console.log(e.message);
    }

  }
  // FIXME: check if eveything is correct. Add minus button and display warning if validCart is false
  return (
    <Box fontSize={style.fontSize} fontFamily="cursive" minH={mainSize} color={style.color}>
        <Box my="1vh" mx={style.mx}>
            <form onSubmit={handleSubmit(mySubmitHandler)}>
                <Steps.Root defaultStep={0} count={3} colorPalette="teal" variant="subtle" color={style.color}>
                    <Steps.List>
                        <Steps.Item key={0} index={0} title={"Contact Infomation"}>
                            <Steps.Trigger>
                                <Steps.Indicator />
                                <Steps.Title color={style.color}>{"Contact Infomation"}</Steps.Title>
                            </Steps.Trigger>
                            <Steps.Separator />
                        </Steps.Item>
                        <Steps.Item key={1} index={1} title={"Delivery"}>
                            <Steps.Trigger>
                                <Steps.Indicator />
                                <Steps.Title color={style.color}>{"Delivery"}</Steps.Title>
                            </Steps.Trigger>
                            <Steps.Separator />
                        </Steps.Item>
                        <Steps.Item key={2} index={2} title={"Payment & Confirmation"}>
                            <Steps.Trigger>
                                <Steps.Indicator />
                                <Steps.Title color={style.color}>{"Payment & Confirmation"}</Steps.Title>
                            </Steps.Trigger>
                            <Steps.Separator />
                        </Steps.Item>
                    </Steps.List>
                    
                    {/* Contact Infomation */}
                    <Steps.Content key={0} index={0}>
                        <Flex direction="column" gap={style.gap} w={style.formW} mx="auto">
                            <Field.Root invalid={!!errors.first_name} required>
                                <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                    First Name
                                    <Field.RequiredIndicator/>
                                </Field.Label>
                                <Input {...register("first_name")} size="xl" fontSize="1.3rem" bg="white"/>
                                <Field.ErrorText>{errors.first_name?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root  invalid={!!errors.last_name} required>
                                <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                    Last Name
                                    <Field.RequiredIndicator/>
                                </Field.Label>
                                <Input {...register("last_name")} size="xl" fontSize="1.3rem" bg="white"/>
                                <Field.ErrorText>{errors.lastName?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root  invalid={!!errors.email} required>
                                <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                    Email
                                    <Field.RequiredIndicator/>
                                </Field.Label>
                                <Input {...register("email")} size="xl" fontSize="1.3rem" bg="white"/>
                                <Field.ErrorText>{errors.email?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root  invalid={!!errors.phone_number} required>
                                <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                    Phone Number
                                    <Field.RequiredIndicator/>
                                </Field.Label>
                                <Input {...register("phone_number")} size="xl" fontSize="1.3rem" bg="white"/>
                                <Field.ErrorText>{errors.phone_number?.message}</Field.ErrorText>
                            </Field.Root>
                            <ButtonGroup size="sm" alignSelf="flex-end">
                                <Steps.PrevTrigger asChild>
                                <Button>Prev</Button>
                                </Steps.PrevTrigger>
                                <Steps.NextTrigger asChild>
                                <Button>Next</Button>
                                </Steps.NextTrigger>
                            </ButtonGroup>
                        </Flex>
                    </Steps.Content>

                    {/* Address */}
                    <Steps.Content key={1} index={1}>
                        <Flex direction="column" gap={style.gap} w={style.formW} mx="auto">
                            <Field.Root invalid={!!errors.address} required>
                                    <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                        Address
                                        <Field.RequiredIndicator/>
                                    </Field.Label>
                                    <Input {...register("address")} size="xl" fontSize="1.3rem" bg="white"/>
                                    <Field.ErrorText>{errors.address?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root invalid={!!errors.optional_details}>
                                    <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                        Add APT, Suite, Unit,...
                                    </Field.Label>
                                    <Input {...register("optional_detailse")} size="xl" fontSize="1.3rem" bg="white"/>
                                    <Field.ErrorText>{errors.optional_details?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root invalid={!!errors.city} required>
                                    <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                        City
                                        <Field.RequiredIndicator/>
                                    </Field.Label>
                                    <Input {...register("city")} size="xl" fontSize="1.3rem" bg="white"/>
                                    <Field.ErrorText>{errors.city?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root invalid={!!errors.state} required>
                                    <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                        State
                                        <Field.RequiredIndicator/>
                                    </Field.Label>
                                    <Input {...register("state")} size="xl" fontSize="1.3rem" bg="white"/>
                                    <Field.ErrorText>{errors.state?.message}</Field.ErrorText>
                            </Field.Root>

                            <Field.Root invalid={!!errors.postal_code} required>
                                    <Field.Label fontSize={style.fontSize} mb={style.labelB}>
                                        Postal Code
                                        <Field.RequiredIndicator/>
                                    </Field.Label>
                                    <Input {...register("postal_code")} size="xl" fontSize="1.3rem" bg="white"/>
                                    <Field.ErrorText>{errors.postal_code?.message}</Field.ErrorText>
                            </Field.Root>
                            <ButtonGroup size="sm"  alignSelf="flex-end">
                                <Steps.PrevTrigger asChild>
                                <Button>Prev</Button>
                                </Steps.PrevTrigger>
                                <Steps.NextTrigger asChild>
                                <Button>Next</Button>
                                </Steps.NextTrigger>
                            </ButtonGroup>
                        </Flex>
                    </Steps.Content>

                     
                    <Steps.Content key={2} index={2}>
                        <Flex direction="column" gap={style.gap} mx="auto">
                            {cartItems.map((item) => (
                                <Link to={`/menu/${item.menuitem.id}`} key={item.id}>
                                    <Card.Root flexDirection="row"  color={style.color} colorPalette="white" _hover={{shadow: "lg"}} maxH={style.cardH} maxW={"50rem"} overflow={"hidden"}> 
                                        <Image src={item.menuitem.path ? item.menuitem.path : placeholder} aspectRatio={6/4} h={style.cardH} fit={"fill"}/>
                                        <Card.Body bg="whitesmoke" fontSize="1rem" gap="1" m={"0"}>
                                            <Box>
                                                <Card.Title>{item.menuitem.title}</Card.Title>
                                                <Text ml="1.2rem">Quantity: {item.quantity}</Text>
                                            </Box>
                                        </Card.Body>
                                    </Card.Root>
                                </Link>
                            ))}

                            <Box w="full"  textAlign='left' color={style.color} fontSize="1.5rem">
                                {/* Price section */}
                                <Text>
                                    Total price: ${get_total_price(false).toFixed(2)}
                                    <br/>
                                    Total price after tax: ${get_total_price(true).toFixed(2)}
                                </Text>
                            </Box>

                            <ButtonGroup size="sm"  alignSelf="flex-end">
                                <Steps.PrevTrigger asChild>
                                <Button>Prev</Button>
                                </Steps.PrevTrigger>
                                <Button type="submit"  bg="green.800" color="white" h="3rem" w="8rem" _hover={{bg: "green.600"}} fontSize={style.fontSize}>Place Order</Button>
                            </ButtonGroup>
                        </Flex>
                    </Steps.Content>

                    <Steps.CompletedContent>Done!</Steps.CompletedContent>

                    {/* <ButtonGroup size="sm">
                        <Steps.PrevTrigger asChild>
                        <Button>Prev</Button>
                        </Steps.PrevTrigger>
                        <Steps.NextTrigger asChild>
                        <Button>Next</Button>
                        </Steps.NextTrigger>
                    </ButtonGroup> */}
                </Steps.Root>          
            </form>
             
        </Box>
    </Box>
    
  );
  
}
