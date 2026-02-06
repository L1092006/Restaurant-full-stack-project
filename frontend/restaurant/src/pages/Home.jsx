import { Flex, Image, Text, Card, Heading, Box } from "@chakra-ui/react"
import callAPI from "../utils/callAPI"
import { useEffect, useState } from "react"
import  placeholder from "../assets/img/placeholder.jpg"
import { Link, useOutletContext } from "react-router-dom";

export default function Home() {
  const [homeContent, setHomeContent ] = useState(null);
  const { homeSize } = useOutletContext();
  const bannerSize = {
    ratio: {
      base: 6/4,
      md: 6/3,
      "2xl": 6/2
    },
    
    w: {
      base: "120vw",
      lg: "60vw"
    },
  };
  const bannerColor = "gray.700";

  const itemsConfig = {
    direction: {
      base: "column",
      md: "row"
    },

    gap: {
      base: "20px",
      md: "3vw"
    },

    size: {
      ratio: {
        base: 6/4,
        xl: 6/2
      },
      w: {
        base: "50vw",
        md: "20vw",
      }
    },

    hover: {
        shadow: "lg"
      }
  };


  // FIXME: improve callAPI if needed
  useEffect(() => {
    callAPI("homeContent").then(res => setHomeContent(res));
  }, [])

  return (
    <>
      <Flex px="6vw"  py="3vh" direction="column" align="center" gap="1vh" minH={homeSize} bg="yellow.100" >
        <Heading as="h1" alignSelf="start" color={bannerColor}  fontFamily="cursive">FEATURED</Heading>
        { homeContent ? (
          <>
            <Image src={homeContent.path ? homeContent.path : placeholder} w={bannerSize.w} borderRadius="3%" aspectRatio={bannerSize.ratio}/>
            <Text color={bannerColor} fontSize={{base: "16px", md: "24px"}} fontFamily="cursive"> {homeContent.description} </Text>
          </>
        ) : <Image src={placeholder} aspectRatio={bannerSize.ratio} w={bannerSize.w} flex="1" borderRadius="3%"/>}

          <Flex flex="1 0 0" alignSelf="stretch" align="center" >
            <Box flex="1">
              <Heading as={"h1"} fontFamily="cursive" textAlign="left" mb="2vh" color={bannerColor}>Trending this week:</Heading>
              {homeContent ? (
              <Flex align="center" justify="space-around" gap="1vh"  direction={itemsConfig.direction} >
                {homeContent.recommendedItems.map(item => {
                  return (
                    <Link to={`/${item.id}`}  key={item.id}>
                      <Card.Root w={itemsConfig.size.w} _hover={itemsConfig.hover}>
                          <Image  src={item.path ? item.path : placeholder} alt={`An image of ${item.name}`}  aspectRatio={itemsConfig.size.ratio} />
                        <Card.Body>
                          <Text>Lorem ipsum dolor sit amet consectetur adipisicing elit. Explicabo, eius doloribus voluptates pariatur ut laudantium.</Text>
                        </Card.Body>
                      </Card.Root>
                    </Link>
                  )
                })}
              </Flex>
              ): <Text>Loading</Text>}
          </Box>
        </Flex>
      </Flex>

      
    </>
  )
}
