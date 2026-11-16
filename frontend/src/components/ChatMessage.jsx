import { AlertTriangle, Leaf, User } from "lucide-react";
import ProductCard from "./ProductCard";
import ComparisonTable from "./ComparisonTable";
import OrderProposalCard from "./OrderProposalCard";

export default function ChatMessage({ message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end gap-2">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-leaf px-4 py-2.5 text-white">
          <span className="sr-only">You: </span>
          {message.content}
        </p>
        <User size={18} className="mt-2 shrink-0 text-ink/40" aria-hidden="true" />
      </div>
    );
  }

  if (message.error) {
    return (
      <div className="flex gap-2">
        <AlertTriangle size={18} className="mt-2 shrink-0 text-berry" aria-hidden="true" />
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-sm border border-berry/40 bg-berry-soft px-4 py-2.5" role="alert">
          <span className="sr-only">Error: </span>
          {message.content}
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <Leaf size={18} className="mt-2 shrink-0 text-leaf" aria-hidden="true" />
      <div className="min-w-0 flex-1 space-y-3">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-sm border border-mist bg-white px-4 py-2.5">
          <span className="sr-only">Assistant: </span>
          {message.content}
        </p>
        {message.comparison && <ComparisonTable comparison={message.comparison} />}
        {message.products && message.products.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {message.products.map((product) => (
              <ProductCard key={product.id} product={product} compact />
            ))}
          </div>
        )}
        {message.orderProposal && <OrderProposalCard proposal={message.orderProposal} />}
      </div>
    </div>
  );
}
