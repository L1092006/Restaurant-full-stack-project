import featuredBanner from "../assets/mockData/featuredBanner.json"

// FIXME: implement
export default async function callAPI(path) {
    if(path == "featuredBanner") return featuredBanner;
}