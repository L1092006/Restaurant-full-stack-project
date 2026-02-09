import homeContent from "../assets/mockData/homeContent.json"
import menuContent from "../assets/mockData/menuContent.json"

// FIXME: implement
export default async function callAPI(path,  method="GET", args={}) {
    if(path === "homeContent") return homeContent;
    else if(path === "login") return {message: "Successfully!"};
    else if(path === "categories") return menuContent.categories;
}