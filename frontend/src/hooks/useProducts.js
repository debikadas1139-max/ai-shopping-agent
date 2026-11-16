import { getProducts } from "../services/api";
import { useDebounced } from "./useDebounced";
import { useFetch } from "./useFetch";

// Loads products for the given filters (waits briefly while the user is still typing).
export function useProducts(filters, enabled = true) {
  const debounced = useDebounced(filters, 250);
  const key = JSON.stringify(debounced);
  const result = useFetch(
    () => (enabled ? getProducts({ ...debounced, limit: 100 }) : Promise.resolve({ items: [], total: 0 })),
    [key, enabled]
  );
  return {
    items: result.data ? result.data.items : [],
    total: result.data ? result.data.total : 0,
    loading: result.loading,
    error: result.error,
    reload: result.reload,
  };
}
