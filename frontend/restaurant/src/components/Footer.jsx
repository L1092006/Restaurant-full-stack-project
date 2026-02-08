import { Flex, Text } from "@chakra-ui/react"

export default function Footer({footerSize}) {
    return (
        <Flex bg="green.700" h={footerSize} justify="flex-start">
            <Text fontFamily="cursive" mt="1vh" ml="1vw">This is Footer</Text>
        </Flex>
    )
}