import { Link } from "react-router-dom";
import RatingStars from "./RatingStars";
import { categoryLabel, formatPrice } from "../utils/format";

// Side-by-side comparison. `comparison` has the shape returned by POST /api/compare.
export default function ComparisonTable({ comparison }) {
  const { products, highlights } = comparison;

  function badges(product) {
    const list = [];
    if (product.id === highlights.cheapest_id) list.push("Lowest price");
    if (product.id === highlights.highest_rated_id) list.push("Highest rated");
    return list;
  }

  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[32rem] text-left text-sm">
        <caption className="sr-only">Product comparison</caption>
        <thead>
          <tr className="border-b border-mist">
            <th scope="col" className="p-3">
              <span className="sr-only">Attribute</span>
            </th>
            {products.map((p) => (
              <th scope="col" key={p.id} className="p-3 align-top font-display text-base">
                <Link to={`/products/${p.id}`} className="hover:underline">
                  {p.name}
                </Link>
                <div className="mt-1 flex flex-wrap gap-1">
                  {badges(p).map((b) => (
                    <span key={b} className="rounded-full bg-honey-soft px-2 py-0.5 text-xs font-semibold text-honey-deep">
                      {b}
                    </span>
                  ))}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="[&_th]:font-semibold [&_tr]:border-b [&_tr]:border-mist">
          <tr>
            <th scope="row" className="p-3">Price</th>
            {products.map((p) => (
              <td key={p.id} className="p-3">
                <span className="shelf-label">{formatPrice(p.price)}</span>
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row" className="p-3">Rating</th>
            {products.map((p) => (
              <td key={p.id} className="p-3">
                <RatingStars rating={p.average_rating} count={p.review_count} />
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row" className="p-3">Category</th>
            {products.map((p) => (
              <td key={p.id} className="p-3">{categoryLabel(p.category)}</td>
            ))}
          </tr>
          <tr>
            <th scope="row" className="p-3">Organic</th>
            {products.map((p) => (
              <td key={p.id} className="p-3">{p.is_organic ? "Yes" : "No"}</td>
            ))}
          </tr>
          <tr>
            <th scope="row" className="p-3">Description</th>
            {products.map((p) => (
              <td key={p.id} className="p-3 text-ink/70">{p.description}</td>
            ))}
          </tr>
        </tbody>
      </table>
      <p className="border-t border-mist p-3 text-sm text-ink/70">
        Price gap between the cheapest and the most expensive: {formatPrice(highlights.price_difference)}.
      </p>
    </div>
  );
}
