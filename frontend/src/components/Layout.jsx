import { Link, NavLink, Outlet } from "react-router-dom";
import { Leaf, ShoppingCart } from "lucide-react";
import { useCart } from "../context/CartContext";

const LINKS = [
  { to: "/", label: "Assistant", end: true },
  { to: "/catalog", label: "Catalog" },
  { to: "/image-search", label: "Image search" },
  { to: "/orders", label: "Orders" },
];

const linkClass = ({ isActive }) =>
  `whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors ${
    isActive ? "bg-leaf text-white" : "text-ink hover:bg-leaf-soft"
  }`;

export default function Layout() {
  const { count } = useCart();

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2"
      >
        Skip to content
      </a>

      <div className="bg-honey-soft px-4 py-1.5 text-center text-sm text-ink">
        Demo store. Products and reviews are sample data, no payment is taken and nothing ships.
      </div>

      <header className="sticky top-0 z-30 border-b border-mist bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-display text-xl font-bold">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-leaf text-white">
              <Leaf size={18} aria-hidden="true" />
            </span>
            Larder
          </Link>

          <nav aria-label="Main" className="order-3 -mx-1 flex w-full gap-1 overflow-x-auto px-1 sm:order-none sm:w-auto sm:flex-1">
            {LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
                {l.label}
              </NavLink>
            ))}
          </nav>

          <NavLink to="/cart" className="btn-secondary relative ml-auto sm:ml-0" aria-label={`Basket, ${count} items`}>
            <ShoppingCart size={18} aria-hidden="true" />
            Basket
            {count > 0 && (
              <span className="grid min-w-[1.4rem] place-items-center rounded-full bg-honey px-1.5 text-xs font-bold text-ink">
                {count}
              </span>
            )}
          </NavLink>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-mist px-4 py-4 text-center text-sm text-ink/60">
        Larder is a student demonstration project. All data is fictional.
      </footer>
    </div>
  );
}
