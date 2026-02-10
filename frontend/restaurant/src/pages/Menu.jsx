import { useOutletContext } from "react-router-dom";
import { Tabs, Text, Card } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import callAPI from "../utils/callAPI";

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
                        
                    </Tabs.Content>
                )
            })}

        </Tabs.Root>
    )
}