import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useCart } from "../context/CartContext";
import { formatPrice } from "../utils/format";

// Shown when the assistant prepares an order. Nothing is bought here: the button only fills
// the basket and opens checkout, where the person must confirm.
export default function OrderProposalCard({ proposal }) {
  const { addItem } = useCart();
  const navigate = useNavigate();

  function reviewOrder() {
    proposal.items.forEach((line) => addItem(line.product_id, line.quantity));
    navigate("/checkout");
  }

  return (
    <div className="card border-honey/60 p-4">
      <h3 className="text-base font-bold">Order summary prepared by the assistant</h3>
      <ul className="mt-2 divide-y divide-mist text-sm">
        {proposal.items.map((line) => (
          <li key={line.product_id} className="flex justify-between gap-3 py-1.5">
            <span>
              {line.quantity} × {line.name}
            </span>
            <span className="font-semibold">{formatPrice(line.line_total)}</span>
          </li>
        ))}
      </ul>
      <p className="mt-2 flex justify-between border-t border-mist pt-2 font-bold">
        <span>Total</span>
        <span>{formatPrice(proposal.total)}</span>
      </p>
      <p className="mt-2 flex items-start gap-2 text-sm text-ink/70">
        <ShieldCheck size={16} className="mt-0.5 shrink-0 text-leaf" aria-hidden="true" />
        Nothing has been ordered yet. You confirm the order on the checkout page.
      </p>
      <button type="button" className="btn-primary mt-3" onClick={reviewOrder}>
        Add to basket and review order
      </button>
    </div>
  );
}
