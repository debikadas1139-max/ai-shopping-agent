import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

const STYLES = {
  error: { box: "border-berry/40 bg-berry-soft text-ink", icon: AlertTriangle, iconClass: "text-berry" },
  info: { box: "border-honey/50 bg-honey-soft text-ink", icon: Info, iconClass: "text-honey-deep" },
  success: { box: "border-leaf/40 bg-leaf-soft text-ink", icon: CheckCircle2, iconClass: "text-leaf" },
};

// A coloured message box. `action` can be a button, for example "Try again".
export default function Notice({ type = "info", title, children, action }) {
  const style = STYLES[type];
  const Icon = style.icon;
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border p-3 text-sm ${style.box}`}
      role={type === "error" ? "alert" : "status"}
    >
      <Icon size={18} className={`mt-0.5 shrink-0 ${style.iconClass}`} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        {title && <p className="font-semibold">{title}</p>}
        <div>{children}</div>
      </div>
      {action}
    </div>
  );
}
