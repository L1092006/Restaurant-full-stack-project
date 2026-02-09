import { useOutletContext } from "react-router-dom";
import { Tabs, Text } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import callAPI from "../utils/callAPI";

export default function Menu() {
    const { mainSize } = useOutletContext();

    const [ categories, setCategories ] = useState(null);

    useEffect(() => {
        callAPI("categories").then(res => setCategories(res));
    })

    const tabStyle = {
        fontFamily: "cursive",
        fontSize: "1rem",
        color: "white.900"
    }

    return (
        <Tabs.Root orientation="vertical" minH={mainSize} fontFamily={tabStyle.fontFamily} color={tabStyle.color}>
            <Tabs.List bg="gray.500">
                {categories ? categories.map(cat => {
                    return (
                        <Tabs.Trigger value={cat.id} key={cat.id} color="whiteAlpha.950">{cat.name}</Tabs.Trigger>
                    )
                }) : <Text>Loading</Text>}
            </Tabs.List>
        </Tabs.Root>
    )
}