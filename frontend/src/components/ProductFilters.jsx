import { Search } from "lucide-react";
import { categoryLabel } from "../utils/format";

export const DEFAULT_FILTERS = {
  q: "",
  category: "",
  min_price: "",
  max_price: "",
  min_rating: "",
  is_organic: "",
  sort: "relevance",
};

// Controlled form: the parent owns `filters`; this component only shows them and reports changes.
export default function ProductFilters({ filters, onChange, categories }) {
  const set = (name) => (event) => onChange({ ...filters, [name]: event.target.value });

  return (
    <form className="card space-y-4 p-4" onSubmit={(e) => e.preventDefault()} aria-label="Product filters">
      <div>
        <label htmlFor="f-q" className="mb-1 block text-sm font-semibold">Search</label>
        <div className="relative">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink/50" aria-hidden="true" />
          <input id="f-q" className="input pl-9" type="search" placeholder="honey, almonds, tea…" value={filters.q} onChange={set("q")} />
        </div>
      </div>

      <div>
        <label htmlFor="f-category" className="mb-1 block text-sm font-semibold">Category</label>
        <select id="f-category" className="input" value={filters.category} onChange={set("category")}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.category} value={c.category}>
              {categoryLabel(c.category)} ({c.product_count})
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="f-min" className="mb-1 block text-sm font-semibold">Min price ($)</label>
          <input id="f-min" className="input" type="number" min="0" step="0.5" inputMode="decimal" value={filters.min_price} onChange={set("min_price")} />
        </div>
        <div>
          <label htmlFor="f-max" className="mb-1 block text-sm font-semibold">Max price ($)</label>
          <input id="f-max" className="input" type="number" min="0" step="0.5" inputMode="decimal" value={filters.max_price} onChange={set("max_price")} />
        </div>
      </div>

      <div>
        <label htmlFor="f-rating" className="mb-1 block text-sm font-semibold">Minimum rating</label>
        <select id="f-rating" className="input" value={filters.min_rating} onChange={set("min_rating")}>
          <option value="">Any rating</option>
          <option value="3">3 stars and up</option>
          <option value="4">4 stars and up</option>
          <option value="4.5">4.5 stars and up</option>
        </select>
      </div>

      <div>
        <label htmlFor="f-organic" className="mb-1 block text-sm font-semibold">Organic</label>
        <select id="f-organic" className="input" value={filters.is_organic} onChange={set("is_organic")}>
          <option value="">Organic and non-organic</option>
          <option value="true">Organic only</option>
          <option value="false">Non-organic only</option>
        </select>
      </div>

      <div>
        <label htmlFor="f-sort" className="mb-1 block text-sm font-semibold">Sort by</label>
        <select id="f-sort" className="input" value={filters.sort} onChange={set("sort")}>
          <option value="relevance">Default order</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="rating_desc">Rating: high to low</option>
          <option value="rating_asc">Rating: low to high</option>
          <option value="name">Name</option>
        </select>
      </div>

      <button type="button" className="btn-secondary w-full" onClick={() => onChange(DEFAULT_FILTERS)}>
        Reset filters
      </button>
    </form>
  );
}
