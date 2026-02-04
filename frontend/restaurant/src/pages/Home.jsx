import { Flex, Image, Text, Icon } from "@chakra-ui/react"
import callAPI from "../utils/callAPI"
import { useEffect, useState } from "react"
import { LuLoader } from "react-icons/lu";
import  placeholder from "../assets/img/placeholder.jpg"

export default function Home() {
  const [featuredBanner, setFeaturedBanner ] = useState(null);
  const bannerSize = {
    h: "35vh",
    w: "75vw"
  }
  const bannerColor = "gray.700";

  useEffect(() => {
    callAPI("featuredBanner").then(res => setFeaturedBanner(res));
  }, [])

  return (
    <Flex mx="6vw"  my="3vh" direction="column" align="center" gap="1vh">
      <Text alignSelf="start" color={bannerColor} fontSize="5vh" fontFamily="cursive">FEATURED</Text>
      { featuredBanner ? (
        <>
          {featuredBanner.path ? <Image src={featuredBanner.path} h={bannerSize.h} w={bannerSize.w}/> : <Image src={placeholder} h={bannerSize.h} w={bannerSize.w}/>}
          <Text color={bannerColor} fontSize="2vh" fontFamily="cursive"> {featuredBanner.description} </Text>
        </>
      ) : <Icon as={LuLoader} color="gray.400" h={bannerSize.h} w={bannerSize.w}/>}
    </Flex>
  )
}
