import { Loader2 } from "lucide-react";

export default function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-ink/70" role="status">
      <Loader2 className="animate-spin" size={20} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
