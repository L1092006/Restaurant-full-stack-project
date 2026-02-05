import homeContent from "../assets/mockData/homeContent.json"

// FIXME: implement
export default async function callAPI(path) {
    if(path == "homeContent") return homeContent;
}