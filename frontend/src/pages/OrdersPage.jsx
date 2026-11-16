import { Link } from "react-router-dom";
import { Receipt } from "lucide-react";
import EmptyState from "../components/EmptyState";
import Notice from "../components/Notice";
import Spinner from "../components/Spinner";
import { useFetch } from "../hooks/useFetch";
import { getOrders } from "../services/api";
import { formatDate, formatPrice } from "../utils/format";

export default function OrdersPage() {
  const { data: orders, loading, error, reload } = useFetch(() => getOrders(), []);

  if (loading) return <Spinner label="Loading orders…" />;
  if (error) {
    return (
      <Notice type="error" title="Could not load orders" action={<button type="button" className="btn-secondary" onClick={reload}>Try again</button>}>
        {error.message}
      </Notice>
    );
  }
  if (orders.length === 0) {
    return (
      <EmptyState icon={Receipt} title="No orders yet" action={<Link to="/catalog" className="btn-primary">Browse the catalog</Link>}>
        Orders you place in this demo store will show up here.
      </EmptyState>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">Order history</h1>
      <p className="text-ink/70">Demo orders stored in the local database. This demo has no user accounts, so all orders are listed.</p>
      <ul className="mt-5 space-y-3">
        {orders.map((order) => (
          <li key={order.id}>
            <Link to={`/orders/${order.id}`} className="card flex flex-wrap items-center justify-between gap-3 p-4 hover:bg-leaf-soft">
              <div>
                <p className="font-bold">Order #{order.id}</p>
                <p className="text-sm text-ink/70">
                  {formatDate(order.created_at)}, {order.item_count} {order.item_count === 1 ? "item" : "items"}
                </p>
                <p className="mt-1 text-sm text-ink/70">{order.items.map((i) => `${i.quantity} × ${i.product_name}`).join(", ")}</p>
              </div>
              <span className="shelf-label">{formatPrice(order.total_amount)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
