import { Link, useLocation, useParams } from "react-router-dom";
import { CheckCircle2, Receipt } from "lucide-react";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import Spinner from "../components/Spinner";
import { useFetch } from "../hooks/useFetch";
import { getOrder } from "../services/api";
import { formatDate, formatPrice } from "../utils/format";

export default function OrderConfirmationPage() {
  const { id } = useParams();
  const location = useLocation();
  const justPlaced = Boolean(location.state && location.state.justPlaced);
  const { data: order, loading, error, reload } = useFetch(() => getOrder(id), [id]);

  if (loading) return <Spinner label="Loading order…" />;
  if (error) {
    if (error.status === 404 || error.status === 422) {
      return (
        <EmptyState icon={Receipt} title="Order not found" action={<Link to="/orders" className="btn-primary">See all orders</Link>}>
          There is no order with this number.
        </EmptyState>
      );
    }
    return (
      <Notice type="error" title="Could not load the order" action={<button type="button" className="btn-secondary" onClick={reload}>Try again</button>}>
        {error.message}
      </Notice>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      {justPlaced && (
        <div className="mb-5 flex items-center gap-3 text-leaf-deep">
          <CheckCircle2 size={32} aria-hidden="true" />
          <h1 className="text-3xl font-bold">Demo order placed</h1>
        </div>
      )}
      {!justPlaced && <h1 className="mb-5 text-3xl font-bold">Order #{order.id}</h1>}

      <Notice type="info">
        This is a demonstration order saved in the local database. No payment was taken and nothing will be shipped.
      </Notice>

      <div className="card mt-5 p-5">
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <div><dt className="text-ink/60">Order number</dt><dd className="font-bold">#{order.id}</dd></div>
          <div><dt className="text-ink/60">Placed</dt><dd className="font-bold">{formatDate(order.created_at)}</dd></div>
          <div><dt className="text-ink/60">Status</dt><dd className="font-bold capitalize">{order.status}</dd></div>
        </dl>
        <ul className="mt-4 divide-y divide-mist border-t border-mist">
          {order.items.map((item, index) => (
            <li key={`${item.product_id}-${index}`} className="flex justify-between gap-3 py-2">
              <span>{item.quantity} × {item.product_name} <span className="text-sm text-ink/60">({formatPrice(item.unit_price)} each)</span></span>
              <span className="font-semibold">{formatPrice(item.line_total)}</span>
            </li>
          ))}
        </ul>
        <p className="flex justify-between border-t border-mist pt-3 text-lg font-bold">
          <span>Total</span>
          <span>{formatPrice(order.total_amount)}</span>
        </p>
      </div>

      <div className="mt-5 flex gap-2">
        <Link to="/orders" className="btn-secondary">Order history</Link>
        <Link to="/catalog" className="btn-primary">Keep shopping</Link>
      </div>
    </div>
  );
}
