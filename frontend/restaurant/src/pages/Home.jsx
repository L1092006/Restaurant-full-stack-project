import { Flex, Image, Text, Card, Heading, Box } from "@chakra-ui/react";
import callAPI from "../utils/callAPI";
import { useEffect, useState } from "react";
import  placeholder from "../assets/img/placeholder.jpg";
import { Link, useOutletContext } from "react-router-dom";

export default function Home() {
  const [homeContent, setHomeContent ] = useState(null);
  const { mainSize } = useOutletContext();
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
  const textColor = "gray.700";

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

  const defaultFont = "cursive";


  // FIXME: improve callAPI if needed
  useEffect(() => {
    callAPI("homeContent").then(res => setHomeContent(res));
  }, [])

  return (
    <>
      <Flex px="6vw"  py="3vh" direction="column" align="center" gap="1vh" minH={mainSize} fontFamily={defaultFont} color={textColor}>
        <Heading as="h1" alignSelf="start" color={textColor} fontFamily={defaultFont} fontSize="3xl">FEATURED</Heading>
        { homeContent ? (
          <>
            <Image src={homeContent.path ? homeContent.path : placeholder} w={bannerSize.w} borderRadius="3%" aspectRatio={bannerSize.ratio}/>
            <Text fontSize={{base: "16px", md: "24px"}}> {homeContent.description} </Text>
          </>
        ) : <Image src={placeholder} aspectRatio={bannerSize.ratio} w={bannerSize.w} flex="1" borderRadius="3%"/>}

          <Flex flex="1 0 0" alignSelf="stretch" align="center" >
            <Box flex="1">
              <Heading as={"h1"} fontFamily={defaultFont} textAlign="left" mb="2vh" color={textColor} fontSize="3xl">Trending this week:</Heading>
              {homeContent ? (
              <Flex align="center" justify="space-around" gap="2rem"  direction={itemsConfig.direction} >
                {homeContent.recommendedItems.map(item => {
                  return (
                    <Link to={`/menu/${item.id}`}  key={item.id}>
                      <Card.Root  _hover={itemsConfig.hover}>
                          <Image  src={item.path ? item.path : placeholder} alt={`An image of ${item.name}`}  aspectRatio={itemsConfig.size.ratio} />
                        <Card.Body bg="whitesmoke">
                          <Text color={textColor}>{item.description}</Text>
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
