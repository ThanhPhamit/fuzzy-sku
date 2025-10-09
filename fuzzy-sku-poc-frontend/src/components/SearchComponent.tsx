import React, { useState, useCallback } from 'react';
import {
  SearchService,
  SearchResult,
  SearchResponse,
} from '../services/SearchService';

interface SearchComponentProps {
  searchService: SearchService;
}

const SearchComponent: React.FC<SearchComponentProps> = ({ searchService }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const searchSize = 20; // Fixed to 20 results

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!query.trim()) {
        setError('Please enter a search query');
        return;
      }

      setLoading(true);
      setError(null);
      setSearchPerformed(false);

      try {
        const response: SearchResponse | null =
          await searchService.searchSKUWithRetry(query.trim(), searchSize);

        if (response && response.results) {
          setResults(response.results);
          setTotalResults(response.total_hits);
          setSearchPerformed(true);
        } else {
          setResults([]);
          setTotalResults(0);
          setError('No results found');
        }
      } catch (error) {
        console.error('Search failed:', error);
        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError('Search failed. Please try again.');
        }
        setResults([]);
        setTotalResults(0);
      } finally {
        setLoading(false);
      }
    },
    [query, searchSize, searchService],
  );

  const handleClear = () => {
    setQuery('');
    setResults([]);
    setError(null);
    setSearchPerformed(false);
    setTotalResults(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Search Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8 border border-primary/10">
          <form onSubmit={handleSearch} className="space-y-6">
            {/* Search Input */}
            <div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter aitehinmei"
                disabled={loading}
                className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:border-primary focus:ring-4 focus:ring-primary/20 transition-all duration-200 outline-none placeholder-gray-400"
              />
            </div>

            {/* Controls Row */}
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search Button */}
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="flex-1 sm:flex-initial px-8 py-3 bg-primary hover:bg-primary-600 disabled:bg-gray-300 text-white font-bold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 disabled:hover:scale-100 disabled:cursor-not-allowed text-lg"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Searching...
                  </span>
                ) : (
                  '🔍 Search'
                )}
              </button>

              {/* Clear Button */}
              {(query || results.length > 0) && (
                <button
                  type="button"
                  onClick={handleClear}
                  disabled={loading}
                  className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  🗑️ Clear
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-8 shadow-md">
            <div className="flex items-center">
              <span className="text-2xl mr-3">⚠️</span>
              <span className="font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Results Table */}
        {results.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gradient-to-r from-primary to-primary-400">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      #
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      Hinban
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      SKU Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      Color Code
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      Color Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      Size Code
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">
                      Size Name
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.map((result, index) => (
                    <tr
                      key={`${result.id || index}`}
                      className="hover:bg-gray-50 transition-colors duration-150"
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 font-medium">
                        {index + 1}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-mono font-semibold text-gray-900">
                        {result.hinban}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {result.sku_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {result.colorcd}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {result.colornm}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {result.sizecd}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {result.sizename}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* No Results */}
        {searchPerformed && results.length === 0 && !loading && !error && (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center border-2 border-dashed border-gray-300">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              No results found
            </h3>
            <p className="text-gray-600">
              Try adjusting your search terms or check the spelling.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchComponent;
