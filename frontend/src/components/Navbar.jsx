import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShoppingCart, Bot, Package, Store } from 'lucide-react';
import { useCart } from '../context/CartContext';

export const Navbar = () => {
  const { cartItems, setIsCartOpen } = useCart();
  const location = useLocation();

  const totalItems = cartItems.reduce((acc, item) => acc + item.quantity, 0);

  const isActive = (path) => location.pathname === path ? 'text-indigo-600 font-semibold' : 'text-gray-600 hover:text-indigo-600';

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-40 border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🛒</span>
            <span className="font-bold text-xl bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
              AI ShopDemo
            </span>
          </div>

          <div className="hidden md:flex items-center space-x-8">
            <Link to="/" className={`flex items-center space-x-1 transition-colors ${isActive('/')}`}>
              <Store className="w-4 h-4" />
              <span>Catalog</span>
            </Link>
            <Link to="/chat" className={`flex items-center space-x-1 transition-colors ${isActive('/chat')}`}>
              <Bot className="w-4 h-4" />
              <span>AI Assistant</span>
            </Link>
            <Link to="/orders" className={`flex items-center space-x-1 transition-colors ${isActive('/orders')}`}>
              <Package className="w-4 h-4" />
              <span>My Orders</span>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsCartOpen(true)}
              className="relative p-2 text-gray-700 hover:text-indigo-600 transition-colors bg-gray-50 hover:bg-indigo-50 rounded-full"
              aria-label="Shopping Cart"
            >
              <ShoppingCart className="w-6 h-6" />
              {totalItems > 0 && (
                <span className="absolute -top-1 -right-1 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-sm">
                  {totalItems}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
      
      <div className="md:hidden flex justify-around bg-gray-50 py-2 border-t border-gray-100 text-sm">
        <Link to="/" className={isActive('/')}>Catalog</Link>
        <Link to="/chat" className={isActive('/chat')}>AI Assistant</Link>
        <Link to="/orders" className={isActive('/orders')}>Orders</Link>
      </div>
    </nav>
  );
};
