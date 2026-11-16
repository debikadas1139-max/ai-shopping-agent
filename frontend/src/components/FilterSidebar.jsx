import React from 'react';
import { Search, SlidersHorizontal, Camera } from 'lucide-react';

export const FilterSidebar = ({
  search, setSearch,
  category, setCategory,
  maxPrice, setMaxPrice,
  minRating, setMinRating,
  isOrganic, setIsOrganic,
  sortBy, setSortBy,
  onOpenImageSearch
}) => {
  const categories = [
    { label: 'All Categories', value: '' },
    { label: 'Honey', value: 'honey' },
    { label: 'Oils', value: 'oil' },
    { label: 'Nuts & Seeds', value: 'nuts' },
    { label: 'Grains & Cereals', value: 'grains' },
    { label: 'Tea & Coffee', value: 'tea' },
    { label: 'Snacks', value: 'snacks' },
    { label: 'Dairy Alternatives', value: 'dairy-alt' }
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 font-semibold text-gray-900">
          <SlidersHorizontal className="w-5 h-5 text-indigo-600" />
          <span>Filters & Search</span>
        </div>
        <button
          onClick={onOpenImageSearch}
          className="flex items-center space-x-1 text-xs bg-violet-50 text-violet-700 hover:bg-violet-100 px-3 py-1.5 rounded-lg font-medium transition-colors"
        >
          <Camera className="w-3.5 h-3.5" />
          <span>Shop by Image</span>
        </button>
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Search</label>
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search groceries..."
            className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Category</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full py-2 px-3 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {categories.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </div>

      <div>
        <div className="flex justify-between text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
          <span>Max Price</span>
          <span className="text-indigo-600">${maxPrice}</span>
        </div>
        <input
          type="range"
          min="3"
          max="35"
          step="1"
          value={maxPrice}
          onChange={(e) => setMaxPrice(Number(e.target.value))}
          className="w-full accent-indigo-600 cursor-pointer"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Minimum Rating</label>
        <select
          value={minRating}
          onChange={(e) => setMinRating(e.target.value)}
          className="w-full py-2 px-3 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">Any Rating</option>
          <option value="4.5">4.5+ Stars</option>
          <option value="4.0">4.0+ Stars</option>
          <option value="3.5">3.5+ Stars</option>
        </select>
      </div>

      <div>
        <label className="flex items-center space-x-2 cursor-pointer pt-2">
          <input
            type="checkbox"
            checked={isOrganic}
            onChange={(e) => setIsOrganic(e.target.checked)}
            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
          />
          <span className="text-sm font-medium text-gray-700">Organic Only</span>
        </label>
      </div>

      <div>
        <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">Sort By</label>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="w-full py-2 px-3 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="rating_desc">Highest Rated</option>
        </select>
      </div>
    </div>
  );
};
