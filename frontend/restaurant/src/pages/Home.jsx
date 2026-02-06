import { Flex, Image, Text, Card } from "@chakra-ui/react"
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
    }
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
      ratio: 1,
      w: {
        base: "50vw",
        md: "20vw",
        xl: "15vw",
        "2xl": "12vw"
      }
    }
  };


  // FIXME: improve callAPI if needed
  useEffect(() => {
    callAPI("homeContent").then(res => setHomeContent(res));
  }, [])

  return (
    <>
      <Flex px="6vw"  py="3vh" direction="column" align="center" gap="1vh" minH={homeSize} bg="yellow.100" >
        <Text alignSelf="start" color={bannerColor} fontSize={{base: "32px", md: "48px"}} fontFamily="cursive">FEATURED</Text>
        { homeContent ? (
          <>
            <Image src={homeContent.path ? homeContent.path : placeholder} w={bannerSize.w} borderRadius="3%" aspectRatio={bannerSize.ratio}/>
            <Text color={bannerColor} fontSize={{base: "16px", md: "24px"}} fontFamily="cursive"> {homeContent.description} </Text>
          </>
        ) : <Image src={placeholder} aspectRatio={bannerSize.ratio} w={bannerSize.w} flex="1" borderRadius="3%"/>}

        {homeContent ? (
        <Flex flex="1 0 0" align="center" gap={itemsConfig.gap} direction={itemsConfig.direction}>
          {homeContent.recommendedItems.map(item => {
            return (
              <Link to={`/${item.id}`}  key={item.id}>
               
                  <Image src={item.path ? item.path : placeholder} w={itemsConfig.size.w} alt={`An image of ${item.name}`}/>
                
              </Link>
            )
          })}
        </Flex>
      ): <Text>Loading</Text>}
      </Flex>

      
    </>
  )
}
