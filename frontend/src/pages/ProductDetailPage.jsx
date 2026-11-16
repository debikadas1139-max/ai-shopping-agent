import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Leaf, PackageSearch, ShoppingCart } from "lucide-react";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import QuantityStepper from "../components/QuantityStepper";
import RatingStars from "../components/RatingStars";
import Spinner from "../components/Spinner";
import { useCart } from "../context/CartContext";
import { useFetch } from "../hooks/useFetch";
import { getProduct, getReviews } from "../services/api";
import { categoryLabel, formatPrice } from "../utils/format";

export default function ProductDetailPage() {
  const { id } = useParams();
  const { addItem } = useCart();
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);

  const { data, loading, error, reload } = useFetch(
    async () => {
      const [product, reviews] = await Promise.all([getProduct(id), getReviews(id)]);
      return { product, reviews };
    },
    [id]
  );

  if (loading) return <Spinner label="Loading product…" />;

  if (error) {
    if (error.status === 404 || error.status === 422) {
      return (
        <EmptyState
          icon={PackageSearch}
          title="Product not found"
          action={<Link to="/catalog" className="btn-primary">Back to catalog</Link>}
        >
          This product does not exist in the store.
        </EmptyState>
      );
    }
    return (
      <Notice type="error" title="Could not load this product" action={<button type="button" className="btn-secondary" onClick={reload}>Try again</button>}>
        {error.message}
      </Notice>
    );
  }

  const { product, reviews } = data;

  function handleAdd() {
    addItem(product.id, quantity);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  }

  return (
    <div>
      <Link to="/catalog" className="inline-flex items-center gap-1 text-sm font-semibold text-leaf-deep hover:underline">
        <ArrowLeft size={16} aria-hidden="true" /> Back to catalog
      </Link>

      <div className="card mt-4 p-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-paper px-2.5 py-0.5 text-xs font-semibold text-ink/70">{categoryLabel(product.category)}</span>
          {product.is_organic && (
            <span className="inline-flex items-center gap-1 rounded-full bg-leaf-soft px-2.5 py-0.5 text-xs font-semibold text-leaf-deep">
              <Leaf size={12} aria-hidden="true" /> Organic
            </span>
          )}
        </div>
        <h1 className="mt-3 text-3xl font-bold">{product.name}</h1>
        <p className="mt-2 max-w-2xl text-ink/80">{product.description}</p>
        <div className="mt-3">
          <RatingStars rating={product.average_rating} count={product.review_count} />
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-4">
          <span className="shelf-label text-2xl">{formatPrice(product.price)}</span>
          <QuantityStepper value={quantity} onChange={(q) => setQuantity(Math.max(1, Math.min(99, q)))} />
          <button type="button" className="btn-primary" onClick={handleAdd}>
            <ShoppingCart size={16} aria-hidden="true" /> {added ? "Added to basket" : "Add to basket"}
          </button>
        </div>
        <p className="mt-3 text-sm text-ink/60">Demo store: availability is not tracked and nothing ships.</p>
      </div>

      <section className="mt-8" aria-labelledby="reviews-heading">
        <h2 id="reviews-heading" className="text-xl font-bold">
          Customer reviews ({reviews.length})
        </h2>
        <p className="text-sm text-ink/60">These reviews are fictional sample data.</p>
        {reviews.length === 0 ? (
          <p className="mt-3 text-ink/70">No reviews yet.</p>
        ) : (
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {reviews.map((r) => (
              <li key={r.id} className="card p-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold">{r.reviewer_name || "Anonymous"}</span>
                  <RatingStars rating={r.rating} count={1} showNumber />
                </div>
                <p className="mt-1 text-sm text-ink/80">{r.review_text}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
