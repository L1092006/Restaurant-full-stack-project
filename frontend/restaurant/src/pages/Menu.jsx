import { useOutletContext, Link } from "react-router-dom";
import { Tabs, Text, Card, Image, Grid, Heading } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useAuth } from '../contexts/AuthContext';
import  placeholder from "../assets/img/placeholder.jpg";

export default function Menu() {
    // Get the size of the page
    const { mainSize } = useOutletContext();

    const [ categories, setCategories ] = useState(null);
    const [ itemsInCat, setItemsInCat ] = useState(null);

    // Get the callAPI function
    const { callAPI } = useAuth();

    // FIXME: Improve if needed
    useEffect(() => {
        async function getContent() {
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
        };
        getContent();
    }, [])

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