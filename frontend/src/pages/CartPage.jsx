import { Link, useNavigate } from "react-router-dom";
import { ShoppingCart, Trash2 } from "lucide-react";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import QuantityStepper from "../components/QuantityStepper";
import Spinner from "../components/Spinner";
import { useCart } from "../context/CartContext";
import { useCartSummary } from "../hooks/useCartSummary";
import { formatPrice } from "../utils/format";

export default function CartPage() {
  const { items, setQuantity, removeItem, clear } = useCart();
  const { summary, loading, error, reload } = useCartSummary(items);
  const navigate = useNavigate();

  if (items.length === 0) {
    return (
      <EmptyState
        icon={ShoppingCart}
        title="Your basket is empty"
        action={<Link to="/catalog" className="btn-primary">Browse the catalog</Link>}
      >
        Add products from the catalog or ask the assistant to find something.
      </EmptyState>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Your basket</h1>
      <p className="text-ink/70">Prices and totals are checked by the server.</p>

      {error && (
        <div className="mt-4">
          <Notice
            type="error"
            title="Could not check your basket"
            action={
              <div className="flex gap-2">
                <button type="button" className="btn-secondary" onClick={reload}>Try again</button>
                {error.status === 404 && <button type="button" className="btn-secondary" onClick={clear}>Empty basket</button>}
              </div>
            }
          >
            {error.message}
          </Notice>
        </div>
      )}

      {loading && !summary && <Spinner label="Checking prices…" />}

      {summary && (
        <div className="mt-5 grid gap-6 lg:grid-cols-[1fr_20rem]">
          <ul className="card divide-y divide-mist">
            {summary.items.map((line) => (
              <li key={line.product_id} className="flex flex-wrap items-center gap-4 p-4">
                <div className="min-w-0 flex-1">
                  <Link to={`/products/${line.product_id}`} className="font-bold hover:underline">{line.name}</Link>
                  <p className="text-sm text-ink/70">{formatPrice(line.unit_price)} each</p>
                </div>
                <QuantityStepper
                  value={line.quantity}
                  onChange={(q) => setQuantity(line.product_id, q)}
                  label={`Quantity of ${line.name}`}
                />
                <span className="w-20 text-right font-bold">{formatPrice(line.line_total)}</span>
                <button type="button" className="btn-danger" onClick={() => removeItem(line.product_id)} aria-label={`Remove ${line.name}`}>
                  <Trash2 size={16} aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>

          <aside className="card h-fit p-4">
            <h2 className="text-lg font-bold">Summary</h2>
            <dl className="mt-3 space-y-1 text-sm">
              <div className="flex justify-between"><dt>Items</dt><dd>{summary.item_count}</dd></div>
              <div className="flex justify-between"><dt>Subtotal</dt><dd>{formatPrice(summary.total)}</dd></div>
              <div className="flex justify-between text-ink/60"><dt>Shipping and tax</dt><dd>Not applicable (demo)</dd></div>
              <div className="flex justify-between border-t border-mist pt-2 text-base font-bold"><dt>Total</dt><dd>{formatPrice(summary.total)}</dd></div>
            </dl>
            <button type="button" className="btn-primary mt-4 w-full" onClick={() => navigate("/checkout")} disabled={loading}>
              Go to checkout
            </button>
            <button type="button" className="btn-secondary mt-2 w-full" onClick={clear}>Empty basket</button>
          </aside>
        </div>
      )}
    </div>
  );
}
