import { Minus, Plus } from "lucide-react";

export default function QuantityStepper({ value, onChange, min = 1, max = 99, label = "Quantity" }) {
  return (
    <div className="inline-flex items-center rounded-lg border border-mist bg-white" role="group" aria-label={label}>
      <button
        type="button"
        className="rounded-l-lg p-2 hover:bg-leaf-soft disabled:opacity-40"
        onClick={() => onChange(value - 1)}
        disabled={value <= min}
        aria-label="Decrease quantity"
      >
        <Minus size={16} aria-hidden="true" />
      </button>
      <span className="min-w-[2.5rem] text-center text-sm font-semibold" aria-live="polite">
        {value}
      </span>
      <button
        type="button"
        className="rounded-r-lg p-2 hover:bg-leaf-soft disabled:opacity-40"
        onClick={() => onChange(value + 1)}
        disabled={value >= max}
        aria-label="Increase quantity"
      >
        <Plus size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
