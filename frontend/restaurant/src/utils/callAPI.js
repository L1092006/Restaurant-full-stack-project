import homeContent from "../assets/mockData/homeContent.json"

// FIXME: implement
export default async function callAPI(path,  method="GET", args={}) {
    if(path === "homeContent") return homeContent;
    else if(path === "login") return {message: "Successfully!"}
}