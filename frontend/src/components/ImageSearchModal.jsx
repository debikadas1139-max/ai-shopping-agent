import React, { useState } from 'react';
import { X, Upload, Camera, Loader2, Sparkles } from 'lucide-react';
import { searchByImage } from '../services/api';
import { ProductCard } from './ProductCard';

export const ImageSearchModal = ({ isOpen, onClose }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResults([]);
      setError('');
    }
  };

  const handleUploadAndSearch = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError('');
    try {
      const data = await searchByImage(selectedFile);
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Image search failed. Please verify Groq vision model configuration.');
    } finally {
      setLoading(false);
    }
  };

  const resetModal = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResults([]);
    setError('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={resetModal} />

      <div className="min-h-screen px-4 text-center flex items-center justify-center">
        <div className="inline-block w-full max-w-3xl bg-white rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all my-8 relative z-10">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
            <div className="flex items-center space-x-2 font-semibold text-gray-900 text-lg">
              <Camera className="w-5 h-5 text-indigo-600" />
              <span>Shop by Product Image</span>
            </div>
            <button onClick={resetModal} className="text-gray-400 hover:text-gray-600 p-1">
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {!previewUrl ? (
              <label className="border-2 border-dashed border-gray-300 hover:border-indigo-500 rounded-2xl p-12 flex flex-col items-center justify-center cursor-pointer bg-gray-50 hover:bg-indigo-50/30 transition-colors">
                <Upload className="w-12 h-12 text-indigo-600 mb-3" />
                <span className="font-semibold text-gray-800">Upload a product image</span>
                <span className="text-xs text-gray-500 mt-1">Supports JPG, JPEG, PNG, WebP</span>
                <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
              </label>
            ) : (
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row items-center gap-6 bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <img src={previewUrl} alt="Preview" className="w-32 h-32 object-cover rounded-xl shadow-sm" />
                  <div className="flex-1 space-y-2 text-center sm:text-left">
                    <h4 className="font-semibold text-gray-900">{selectedFile.name}</h4>
                    <p className="text-xs text-gray-500">Ready to analyze using Groq Vision model and find approximate matches in our database.</p>
                    <div className="flex space-x-2 pt-2 justify-center sm:justify-start">
                      <button
                        onClick={handleUploadAndSearch}
                        disabled={loading}
                        className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors flex items-center space-x-2 shadow-sm"
                      >
                        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                        <span>{loading ? 'Analyzing Image...' : 'Find Similar Products'}</span>
                      </button>
                      <button
                        onClick={() => { setSelectedFile(null); setPreviewUrl(null); setResults([]); }}
                        className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors"
                      >
                        Change Image
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm">{error}</div>
            )}

            {results.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-900 flex items-center space-x-1 text-sm">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span>Matching Approximate Products</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto pr-1">
                  {results.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
