import { useOutletContext, Link } from "react-router-dom";
import { Tabs, Text, Card, Image, Grid, Heading } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import callAPI from "../utils/callAPI";
import  placeholder from "../assets/img/placeholder.jpg";

export default function Menu() {
    const { mainSize } = useOutletContext();

    const [ categories, setCategories ] = useState(null);
    const [ itemsInCat, setItemsInCat ] = useState(null);

    

    // FIXME: Improve if needed
    useEffect(() => {
        async function getContent() {
            const cats = await callAPI("categories");
            const allItems = await callAPI("items");
            const tempItems = new Map();
            for(let cat of cats) {
                tempItems.set(cat.id, [])
            }
            for(let item of allItems) {
                tempItems.get(item.category).push(item);
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
                        <Tabs.Trigger value={cat.id} key={cat.id} color={tabStyle.color}>{cat.name}</Tabs.Trigger>
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