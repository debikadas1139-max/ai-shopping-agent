import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Leaf, ShoppingCart } from "lucide-react";
import RatingStars from "./RatingStars";
import { useCart } from "../context/CartContext";
import { categoryLabel, formatPrice } from "../utils/format";

// One product. Used in the catalog, in chat answers and in image-search results.
//   compact          : smaller card for chat (hides the description)
//   compareSelected  : (optional) true/false -> shows a "Compare" checkbox
//   onToggleCompare  : (optional) called when that checkbox changes
export default function ProductCard({ product, compact = false, compareSelected, onToggleCompare }) {
  const { addItem } = useCart();
  const [justAdded, setJustAdded] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  function handleAdd() {
    addItem(product.id, 1);
    setJustAdded(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setJustAdded(false), 1800);
  }

  return (
    <article className="card flex h-full flex-col p-4">
      <div className="flex items-start justify-between gap-2">
        <span className="rounded-full bg-paper px-2.5 py-0.5 text-xs font-semibold text-ink/70">
          {categoryLabel(product.category)}
        </span>
        {product.is_organic && (
          <span className="inline-flex items-center gap-1 rounded-full bg-leaf-soft px-2.5 py-0.5 text-xs font-semibold text-leaf-deep">
            <Leaf size={12} aria-hidden="true" /> Organic
          </span>
        )}
      </div>

      <h3 className="mt-3 text-lg font-bold leading-snug">
        <Link to={`/products/${product.id}`} className="hover:underline">
          {product.name}
        </Link>
      </h3>

      {!compact && <p className="mt-1 line-clamp-2 text-sm text-ink/70">{product.description}</p>}
      {product.reason && <p className="mt-1 text-sm text-ink/70">{product.reason}</p>}
      {product.matched_on && (
        <p className="mt-1 text-xs text-ink/60">Approximate match on “{product.matched_on}”</p>
      )}

      <div className="mt-3">
        <RatingStars rating={product.average_rating} count={product.review_count} />
      </div>

      <div className="mt-auto flex items-center justify-between gap-3 pt-4">
        <span className="shelf-label">{formatPrice(product.price)}</span>
        <button
          type="button"
          onClick={handleAdd}
          className={justAdded ? "btn-secondary" : "btn-primary"}
          aria-label={`Add ${product.name} to basket`}
        >
          {justAdded ? <Check size={16} aria-hidden="true" /> : <ShoppingCart size={16} aria-hidden="true" />}
          {justAdded ? "Added" : "Add"}
        </button>
      </div>
      <span className="sr-only" aria-live="polite">
        {justAdded ? `${product.name} added to basket` : ""}
      </span>

      {onToggleCompare && (
        <label className="mt-3 flex cursor-pointer items-center gap-2 border-t border-mist pt-3 text-sm">
          <input
            type="checkbox"
            checked={!!compareSelected}
            onChange={() => onToggleCompare(product.id)}
            className="h-4 w-4 accent-leaf"
          />
          Compare
        </label>
      )}
    </article>
  );
}
