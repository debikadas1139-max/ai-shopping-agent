import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

// The cart stores only { product_id, quantity }. Names, prices and totals always come from the server.
const STORAGE_KEY = "larder.cart.v1";
const MAX_QUANTITY = 99;

const CartContext = createContext(null);

function clamp(quantity) {
  return Math.max(1, Math.min(MAX_QUANTITY, Math.floor(Number(quantity) || 1)));
}

function loadCart() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((i) => Number.isInteger(i.product_id) && i.product_id > 0)
      .map((i) => ({ product_id: i.product_id, quantity: clamp(i.quantity) }))
      .slice(0, 50);
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(loadCart);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // Storage can be blocked (private mode). The cart then just lasts until the page is closed.
    }
  }, [items]);

  const addItem = useCallback((productId, quantity = 1) => {
    setItems((current) => {
      const existing = current.find((i) => i.product_id === productId);
      if (existing) {
        return current.map((i) =>
          i.product_id === productId ? { ...i, quantity: clamp(i.quantity + quantity) } : i
        );
      }
      return [...current, { product_id: productId, quantity: clamp(quantity) }];
    });
  }, []);

  const setQuantity = useCallback((productId, quantity) => {
    setItems((current) =>
      current.map((i) => (i.product_id === productId ? { ...i, quantity: clamp(quantity) } : i))
    );
  }, []);

  const removeItem = useCallback((productId) => {
    setItems((current) => current.filter((i) => i.product_id !== productId));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  const value = useMemo(
    () => ({
      items,
      count: items.reduce((sum, i) => sum + i.quantity, 0),
      addItem,
      setQuantity,
      removeItem,
      clear,
    }),
    [items, addItem, setQuantity, removeItem, clear]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) throw new Error("useCart must be used inside <CartProvider>");
  return context;
}
