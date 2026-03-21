import { createContext, useContext, useEffect, useState, useMemo, useCallback } from "react";
import { useAuth } from "./AuthContext";

const CartContext = createContext();

export default function CartProvider({ children }) {
    const { callAPI, isAuthenticated } = useAuth();

    // Init the number to 0 in case the use is not authenticated
    const [ cartNumber, setCartNumber ] = useState(0);
    const [ cartItems, setCartItems ] = useState(null);

    // Get all the items of the user's cart
    const loadCart = useCallback(async () => {
            let res = null;
            try {
                res = await callAPI('/carts/', {auth: true});
                if(!res.ok) return;
                const data = await res.json();
                setCartItems(data);
                setCartNumber(data.length);
            }
            catch (e) {
                console.log(e.message);
            }
        }, [setCartItems, setCartNumber]);
    // If the user is authenticated, get the cart items data from the backend.
    useEffect(() => {
        if(isAuthenticated) loadCart();
        else {
            setCartItems(null);
            setCartNumber(0);
        }
    }, [isAuthenticated, callAPI])

    const value = useMemo(() => ({ cartNumber, setCartNumber, cartItems, setCartItems }), [cartNumber, setCartNumber, cartItems, setCartItems]);

    return (
        <CartContext.Provider value={value}>
            {children}
        </CartContext.Provider>
    )
}

export function useCart() {
    return useContext(CartContext);
}