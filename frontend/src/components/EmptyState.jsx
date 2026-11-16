export default function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="card flex flex-col items-center px-6 py-12 text-center">
      {Icon && <Icon size={36} className="mb-3 text-leaf" aria-hidden="true" />}
      <h2 className="text-xl font-bold">{title}</h2>
      {children && <p className="mt-1 max-w-md text-ink/70">{children}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
