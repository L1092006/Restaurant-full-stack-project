import { createContext, useContext, useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useAuth } from "./AuthContext";

const CartContext = createContext();

export default function CartProvider({ children }) {
    const { callAPI, isAuthenticated } = useAuth();

    // Init the number to 0 in case the use is not authenticated
    const [ cartNumber, setCartNumber ] = useState(0);
    const [ cartItems, setCartItems ] = useState([]);

    // Get all the items of the user's cart. Do nothing if the load fails
    const loadCart = useCallback(async () => {
            let res = null;
            try {
                res = await callAPI("/carts/", {auth: true});
                if(!res.ok) return;
                const data = await res.json();
                setCartItems(data);
            }
            catch (e) {
                console.log(e.message);
            }
        }, [callAPI]);



    // Add addAmount items to the cart. addNumber can be negative which means subtract some items. Return nothing, raise error if there are problems:
    //  Error with messages for not enough items (but still add the item to the cart and then reload the menu items), non-ok response or existing call. Normal TypeError for failed fetch call
    const addItemRef = useRef(new Set());
    const addItem = useCallback(async (menuitem_id, addAmount) => {
        // Define the messages for different errors
        const errorMessages = {
            // Not enough items
            notEnough: 'Not enough',
            // res.ok is false
            notOk: 'Not Ok',
            // There is another addItem call
            existingCall: 'Existing call'
        }
        
        if (addItemRef.current.has(menuitem_id)) throw Error(errorMessages.existingCall);
        addItemRef.current.add(menuitem_id);
        try {
            // Use this var to check if the adding proccess is done
            let done = false;

            // This is the res to return 
            let res = null;
            // Search the current cart items to check if that item is already in the cart
            for(let i = 0; i < cartItems.length; i++) {
                const item = cartItems[i];
                if(item.menuitem.id !== menuitem_id) continue;
                try {
                    // If there is an item with the similar menuitem_id, make a patch request to update the quantity
                    res = await callAPI(`/carts/${item.id}/`, {options: {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ quantity: item.quantity + addAmount })
                    }, auth: true});
                            
                    if(!res.ok) throw new Error(errorMessages.notOk);
                    const updatedItem = await res.json();
                            
                    done = true;
                    // Check if the current quantity exceed the stock
                    if(updatedItem.quantity > updatedItem.menuitem.stock) throw new Error(errorMessages.notEnough);
                    
                }
                catch(e) {
                    throw e;
                }
            }

            // Return if we already added the item or if addAmount is <=0 since we don't need to create new item in this case
            if(done || addAmount < 1) return;

            try {
                // If the item is not in the cart, create a new cart item
                res = await callAPI("/carts/", {options: {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            menuitem_id: menuitem_id,
                            quantity: addAmount
                        })
                    }, auth: true});

                if(!res.ok) throw Error(errorMessages.notOk);
                const newItem = await res.json();

                // Check if the current quantity exceed the stock
                if(newItem.quantity > newItem.menuitem.stock) throw new Error(errorMessages.notEnough);

            }
            catch (e) {
                throw e;
                console.log(e.message);
            }

            
            return;
        }
        finally {
            // Update the cart item in cartItems
            await loadCart();
            addItemRef.current.delete(menuitem_id);
        }
    }, [loadCart, cartItems, callAPI])

    // If the user is authenticated, get the cart items data from the backend.
    useEffect(() => {
        if(isAuthenticated) loadCart();
        else {
            setCartItems([]);
        }
    }, [isAuthenticated, loadCart])

    // Auto update cartNumber when cartItems change
    useEffect(() => {
        let num = 0;
        for(const item of cartItems) {
            num += item.quantity;
        }
        setCartNumber(num);
    }, [cartItems]);

    const value = useMemo(() => ({ cartNumber, setCartNumber, cartItems, setCartItems, loadCart, addItem }), [cartNumber, cartItems, loadCart, addItem]);

    return (
        <CartContext.Provider value={value}>
            {children}
        </CartContext.Provider>
    )
}

export function useCart() {
    return useContext(CartContext);
}