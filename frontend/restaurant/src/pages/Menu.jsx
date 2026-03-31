import { useOutletContext, Link } from "react-router-dom";
import { Tabs, Text, Card, Image, Grid, Heading, IconButton } from "@chakra-ui/react";
import { useEffect, useState, useCallback } from "react";
import { IoMdAdd } from "react-icons/io";
import { toaster } from "../components/ui/toaster";
import { useAuth } from '../contexts/AuthContext';
import { useCart } from "../contexts/CartContext";
import  placeholder from "../assets/img/placeholder.jpg";

export default function Menu() {
    // Get the size of the page
    const { mainSize } = useOutletContext();

    const [ categories, setCategories ] = useState(null);
    const [ itemsInCat, setItemsInCat ] = useState(null);

    // Get the callAPI function
    const { callAPI } = useAuth();

    // FIXME: Improve if needed
    // Helper function to get all items and categories
    const getContent = useCallback(async () => {
            let cats = null;
            let allItems = null;
            try {
                const catRes = await callAPI("/categories/");
                const itemRes = await callAPI("/items/");

                // If res is not ok, throw an error and return in the catch
                if(!catRes.ok || !itemRes.ok) throw new Error('callAPI successfully but res is not ok');

                cats = await catRes.json();
                allItems = await itemRes.json();
            }
            catch (e) {
                console.log(e.message);
                return;
            }


            
            const tempItems = new Map();
            for(let cat of cats) {
                tempItems.set(cat.id, [])
            }
            for(let item of allItems) {
                tempItems.get(item.category.id).push(item);
            }
            setCategories(cats)
            setItemsInCat(tempItems);
        }, [callAPI]);

    // Get the content when the component is mounted
    useEffect(() => {
        getContent();
    }, [getContent]);


    // Get the addItem function from CartContext
    const { addItem } = useCart();

    // Handler for the add item button
    const addHandler = async (e, item) => {
        e.preventDefault();
        try {
            await addItem(item.id);
        }
        catch (error) {
            // If the stock of an item needs to be updated, reload the content
            if (error.message === 'Not enough') {
                getContent();
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

    const tabStyle = {
        fontFamily: "cursive",
        fontSize: "1rem",
        color: "gray.700"
    }

    if(!categories || !itemsInCat) {
        return <Text color={tabStyle.color} fontFamily={tabStyle.fontFamily}>Loading</Text>
    }

    return (
        <Tabs.Root defaultValue={categories[0].id} fitted minH={mainSize} colorPalette="green" fontFamily={tabStyle.fontFamily} color={tabStyle.color}>
            <Tabs.List bg="gray.300" >
                {categories.map(cat => {
                    return (
                        <Tabs.Trigger value={cat.id} key={cat.id} color={tabStyle.color}>{cat.title}</Tabs.Trigger>
                    )
                })}
            </Tabs.List>

            {categories.map(cat => {
                return (
                    <Tabs.Content value={cat.id} key={cat.id} >
                        <Grid templateColumns="repeat(auto-fit, 20rem)"  justifyContent="center" gap="2rem" px="4vw" pt="1rem" pb="2rem">
                            {itemsInCat.get(cat.id).map(item => (
                                <Link to={`/menu/${item.id}`} key={item.id}>
                                    <Card.Root  color={tabStyle.color} colorPalette="white" _hover={{shadow: "lg"}}> 
                                        <Image src={item.path ? item.path : placeholder} aspectRatio={6/4}/>
                                        <Card.Body bg="whitesmoke">
                                            <Heading as="h3" mb="0.5rem">{item.title}</Heading>
                                            <Text>{item.description}</Text>
                                            <IconButton onClick={(e) => addHandler(e, item)} variant="solid" size="xs" ml="auto" backgroundColor="green.800" _hover={{backgroundColor: "green.700"}}>
                                                <IoMdAdd/>
                                            </IconButton>
                                        </Card.Body>
                                    </Card.Root>
                                </Link>
                            ))}
                        </Grid>
                    </Tabs.Content>
                )
            })}

        </Tabs.Root>
    )
}