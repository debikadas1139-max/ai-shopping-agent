import React, { useState } from 'react';
import { X, Trash2, Plus, Minus, ShoppingBag, CheckCircle2 } from 'lucide-react';
import { useCart } from '../context/CartContext';

export const CartDrawer = () => {
  const {
    cartItems,
    cartDetails,
    isCartOpen,
    setIsCartOpen,
    updateQuantity,
    removeFromCart,
    clearCart,
    checkoutCart,
    loading
  } = useCart();

  const [confirmedOrder, setConfirmedOrder] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isCartOpen) return null;

  const handleCheckout = async () => {
    setErrorMsg('');
    try {
      const order = await checkoutCart();
      setConfirmedOrder(order);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Checkout failed. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={() => setIsCartOpen(false)} />

      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-xl flex flex-col">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
            <div className="flex items-center space-x-2 font-semibold text-gray-900 text-lg">
              <ShoppingBag className="w-5 h-5 text-indigo-600" />
              <span>Your Shopping Cart</span>
            </div>
            <button onClick={() => setIsCartOpen(false)} className="text-gray-400 hover:text-gray-600 p-1">
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {confirmedOrder ? (
              <div className="text-center py-12 space-y-4">
                <CheckCircle2 className="w-16 h-16 text-emerald-600 mx-auto" />
                <h3 className="text-xl font-bold text-gray-900">Order Confirmed!</h3>
                <p className="text-sm text-gray-600">Order #{confirmedOrder.id} has been successfully placed.</p>
                <div className="bg-gray-50 p-4 rounded-xl text-left text-sm space-y-2 border border-gray-100">
                  <div className="flex justify-between font-semibold">
                    <span>Total Amount:</span>
                    <span className="text-indigo-600">${confirmedOrder.total_amount.toFixed(2)}</span>
                  </div>
                  <div className="text-xs text-gray-500">Status: {confirmedOrder.status}</div>
                </div>
                <button
                  onClick={() => { setConfirmedOrder(null); setIsCartOpen(false); }}
                  className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 transition-colors"
                >
                  Continue Shopping
                </button>
              </div>
            ) : cartItems.length === 0 ? (
              <div className="text-center py-16 space-y-3">
                <span className="text-4xl">🛒</span>
                <p className="text-gray-500 font-medium">Your cart is empty</p>
                <button
                  onClick={() => setIsCartOpen(false)}
                  className="text-indigo-600 font-semibold text-sm hover:underline"
                >
                  Browse Catalog
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {errorMsg && (
                  <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{errorMsg}</div>
                )}
                {cartDetails.items.map((item) => (
                  <div key={item.product_id} className="flex justify-between items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className="flex-1 pr-4">
                      <h4 className="font-semibold text-gray-900 text-sm">{item.name}</h4>
                      <p className="text-indigo-600 text-sm font-medium">${item.price.toFixed(2)} each</p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2 bg-white border border-gray-200 rounded-lg p-1">
                        <button
                          onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                          className="p-1 text-gray-500 hover:text-gray-900"
                        >
                          <Minus className="w-3.5 h-3.5" />
                        </button>
                        <span className="text-sm font-semibold w-6 text-center">{item.quantity}</span>
                        <button
                          onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                          className="p-1 text-gray-500 hover:text-gray-900"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <button
                        onClick={() => removeFromCart(item.product_id)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {!confirmedOrder && cartItems.length > 0 && (
            <div className="p-6 border-t border-gray-100 bg-gray-50 space-y-4">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal</span>
                  <span>${cartDetails.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-gray-900 font-bold text-lg pt-2 border-t border-gray-200">
                  <span>Total</span>
                  <span className="text-indigo-600">${cartDetails.total.toFixed(2)}</span>
                </div>
              </div>
              <button
                onClick={handleCheckout}
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-3 rounded-xl font-medium transition-colors shadow-sm flex items-center justify-center space-x-2"
              >
                <span>{loading ? 'Processing Order...' : 'Confirm & Checkout'}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
