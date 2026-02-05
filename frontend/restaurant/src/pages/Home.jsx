import { Flex, Image, Text, Icon } from "@chakra-ui/react"
import callAPI from "../utils/callAPI"
import { useEffect, useState } from "react"
import  placeholder from "../assets/img/placeholder.jpg"
import { Link, useOutletContext } from "react-router-dom";

export default function Home() {
  const [homeContent, setHomeContent ] = useState(null);
  const { homeSize } = useOutletContext();
  const bannerSize = {
    w: {
      base: "75vw",
      md: "50vw"
    },
    ratio: {
      base: 6/4,
      md: 6/2
    }
  }
  const bannerColor = "gray.700";


  // FIXME: improve callAPI if needed
  useEffect(() => {
    callAPI("homeContent").then(res => setHomeContent(res));
  }, [])

  return (
    <>
      <Flex px="6vw"  py="3vh" direction="column" align="center" gap="1vh" h={homeSize} flex="1" bg="yellow.100">
        <Text alignSelf="start" color={bannerColor} fontSize={{base: "32px", md: "48px"}} fontFamily="cursive">FEATURED</Text>
        { homeContent ? (
          <>
            <Image src={homeContent.path ? homeContent.path : placeholder} aspectRatio={bannerSize.ratio} w={bannerSize.w}/>
            <Text color={bannerColor} fontSize={{base: "16px", md: "24px"}} fontFamily="cursive"> {homeContent.description} </Text>
          </>
        ) : <Image src={placeholder} aspectRatio={bannerSize.ratio} w={bannerSize.w}/>}
        {homeContent ? (
        <Flex mt="auto">
          {homeContent.recommendedItems.map(item => {
            return (
              <Link to={`/${item.id}`}  key={item.id}><Image src={item.path ? item.path : placeholder}/></Link>
            )
          })}
        </Flex>
      ): <Text>Loading</Text>}
      </Flex>

      
    </>
  )
}
