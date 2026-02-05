import { Box } from "@chakra-ui/react"

export default function Footer({footerSize}) {
    return (
        <Box bg="green.700" mt="auto" h={footerSize}>
            This is Footer
        </Box>
    )
}