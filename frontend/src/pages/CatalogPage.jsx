import { useMemo, useState } from "react";
import { Scale, Search, SlidersHorizontal, X } from "lucide-react";
import ComparisonTable from "../components/ComparisonTable";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import ProductCard from "../components/ProductCard";
import ProductFilters, { DEFAULT_FILTERS } from "../components/ProductFilters";
import Spinner from "../components/Spinner";
import { useFetch } from "../hooks/useFetch";
import { useProducts } from "../hooks/useProducts";
import { compareProducts, getCategories } from "../services/api";

// Remove empty filter values before calling the API.
function cleanFilters(filters) {
  const cleaned = {};
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && !(key === "sort" && value === "relevance")) cleaned[key] = value;
  });
  return cleaned;
}

export default function CatalogPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [showFilters, setShowFilters] = useState(false);
  const [selected, setSelected] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState("");

  const categoriesResult = useFetch(() => getCategories(), []);
  const categories = categoriesResult.data || [];

  const priceRangeInvalid =
    filters.min_price !== "" && filters.max_price !== "" && Number(filters.min_price) > Number(filters.max_price);
  const apiFilters = useMemo(() => cleanFilters(filters), [filters]);
  const { items, total, loading, error, reload } = useProducts(apiFilters, !priceRangeInvalid);

  function toggleCompare(id) {
    setComparison(null);
    setCompareError("");
    setSelected((current) => {
      if (current.includes(id)) return current.filter((x) => x !== id);
      return current.length >= 4 ? current : [...current, id];
    });
  }

  async function runComparison() {
    setComparing(true);
    setCompareError("");
    try {
      setComparison(await compareProducts(selected));
    } catch (err) {
      setCompareError(err.message);
    } finally {
      setComparing(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">Catalog</h1>
          <p className="text-ink/70">Sample products with ratings calculated from sample reviews.</p>
        </div>
        <button type="button" className="btn-secondary lg:hidden" onClick={() => setShowFilters((s) => !s)} aria-expanded={showFilters}>
          <SlidersHorizontal size={16} aria-hidden="true" /> Filters
        </button>
      </div>

      <div className="mt-5 grid gap-6 lg:grid-cols-[17rem_1fr]">
        <aside className={`${showFilters ? "block" : "hidden"} lg:sticky lg:top-24 lg:block lg:self-start`}>
          <ProductFilters filters={filters} onChange={setFilters} categories={categories} />
        </aside>

        <section aria-label="Products">
          {priceRangeInvalid && (
            <div className="mb-4">
              <Notice type="info">The minimum price is higher than the maximum price. Adjust one of them to see products.</Notice>
            </div>
          )}

          {comparison && (
            <div className="mb-6">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-xl font-bold">Comparison</h2>
                <button type="button" className="btn-secondary" onClick={() => setComparison(null)}>
                  <X size={16} aria-hidden="true" /> Close comparison
                </button>
              </div>
              <ComparisonTable comparison={comparison} />
            </div>
          )}
          {compareError && (
            <div className="mb-4">
              <Notice type="error" title="Could not compare">{compareError}</Notice>
            </div>
          )}

          {error ? (
            <Notice
              type="error"
              title="Could not load products"
              action={<button type="button" className="btn-secondary" onClick={reload}>Try again</button>}
            >
              {error.message}
            </Notice>
          ) : loading ? (
            <Spinner label="Loading products…" />
          ) : items.length === 0 ? (
            !priceRangeInvalid && (
              <EmptyState
                icon={Search}
                title="No products match these filters"
                action={<button type="button" className="btn-primary" onClick={() => setFilters(DEFAULT_FILTERS)}>Reset filters</button>}
              >
                Try a lower minimum rating, a wider price range, or remove the organic filter.
              </EmptyState>
            )
          ) : (
            <>
              <p className="mb-3 text-sm text-ink/70" aria-live="polite">
                {total} {total === 1 ? "product" : "products"}
              </p>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {items.map((p) => (
                  <ProductCard key={p.id} product={p} compareSelected={selected.includes(p.id)} onToggleCompare={toggleCompare} />
                ))}
              </div>
            </>
          )}
        </section>
      </div>

      {selected.length > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-20 border-t border-mist bg-white/95 px-4 py-3 backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
            <p className="text-sm font-semibold">
              {selected.length} selected{selected.length < 2 ? ", choose at least 2 to compare" : ""}
              {selected.length === 4 ? " (maximum 4)" : ""}
            </p>
            <div className="flex gap-2">
              <button type="button" className="btn-secondary" onClick={() => { setSelected([]); setComparison(null); }}>
                Clear
              </button>
              <button type="button" className="btn-primary" onClick={runComparison} disabled={selected.length < 2 || comparing}>
                <Scale size={16} aria-hidden="true" /> {comparing ? "Comparing…" : "Compare"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
