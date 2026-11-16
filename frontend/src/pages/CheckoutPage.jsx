import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShoppingCart } from "lucide-react";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import Spinner from "../components/Spinner";
import { useCart } from "../context/CartContext";
import { useCartSummary } from "../hooks/useCartSummary";
import { createOrder } from "../services/api";
import { formatPrice, newId } from "../utils/format";

export default function CheckoutPage() {
  const { items, clear } = useCart();
  const { summary, loading, error, reload } = useCartSummary(items);
  const navigate = useNavigate();
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // One idempotency key per cart contents. If the request is retried (double click, network blip),
  // the server sees the same key and returns the first order instead of creating a second one.
  const signature = JSON.stringify(items);
  const keyRef = useRef({ signature: null, key: null });
  if (keyRef.current.signature !== signature) keyRef.current = { signature, key: newId() };

  if (items.length === 0 && !submitting) {
    return (
      <EmptyState
        icon={ShoppingCart}
        title="Nothing to check out"
        action={<Link to="/catalog" className="btn-primary">Browse the catalog</Link>}
      >
        Your basket is empty.
      </EmptyState>
    );
  }

  async function placeOrder() {
    if (!summary || !confirmed || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const order = await createOrder({
        items,
        confirmed: true,
        confirmed_total: summary.total,
        idempotency_key: keyRef.current.key,
      });
      clear();
      navigate(`/orders/${order.id}`, { replace: true, state: { justPlaced: true } });
    } catch (err) {
      setSubmitError(err);
      setSubmitting(false);
      if (err.code === "total_mismatch") {
        setConfirmed(false);
        reload();
      }
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-3xl font-bold">Review your order</h1>
      <p className="text-ink/70">Check the items and total, then confirm. This is a demonstration: no payment is taken.</p>

      {error && (
        <div className="mt-4">
          <Notice type="error" title="Could not check your basket" action={<button type="button" className="btn-secondary" onClick={reload}>Try again</button>}>
            {error.message}
          </Notice>
        </div>
      )}
      {loading && !summary && <Spinner label="Checking prices…" />}

      {summary && (
        <div className="card mt-5 p-5">
          <ul className="divide-y divide-mist">
            {summary.items.map((line) => (
              <li key={line.product_id} className="flex justify-between gap-3 py-2">
                <span>{line.quantity} × {line.name} <span className="text-sm text-ink/60">({formatPrice(line.unit_price)} each)</span></span>
                <span className="font-semibold">{formatPrice(line.line_total)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 flex justify-between border-t border-mist pt-3 text-lg font-bold">
            <span>Total</span>
            <span>{formatPrice(summary.total)}</span>
          </p>

          <label className="mt-5 flex cursor-pointer items-start gap-3 rounded-lg bg-honey-soft p-3 text-sm">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 accent-leaf"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            <span>I have reviewed this order and want to place it. I understand this is a demo and nothing is paid for or shipped.</span>
          </label>

          {submitError && (
            <div className="mt-4">
              <Notice type="error" title="The order was not placed">{submitError.message}</Notice>
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-2">
            <button type="button" className="btn-primary" onClick={placeOrder} disabled={!confirmed || submitting || loading}>
              {submitting ? "Placing order…" : `Place demo order (${formatPrice(summary.total)})`}
            </button>
            <Link to="/cart" className="btn-secondary">Back to basket</Link>
          </div>
        </div>
      )}
    </div>
  );
}
