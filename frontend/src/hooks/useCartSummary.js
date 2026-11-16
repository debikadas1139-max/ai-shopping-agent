import { validateCart } from "../services/api";
import { useFetch } from "./useFetch";

// Asks the server for real prices and totals for the cart (never calculated from browser data).
export function useCartSummary(items) {
  const key = JSON.stringify(items);
  const result = useFetch(() => (items.length ? validateCart(items) : Promise.resolve(null)), [key]);
  return { summary: result.data, loading: result.loading, error: result.error, reload: result.reload };
}
