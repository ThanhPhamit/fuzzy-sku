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
  const [maxScore, setMaxScore] = useState(0);
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
          setMaxScore(response.max_score);
          setSearchPerformed(true);
        } else {
          setResults([]);
          setTotalResults(0);
          setMaxScore(0);
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
        setMaxScore(0);
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
    setMaxScore(0);
  };

  const renderHighlightedText = (
    text: string,
    highlights?: string[],
  ): JSX.Element => {
    // If we have highlight data from API, use it
    if (highlights && highlights.length > 0) {
      const highlightedHtml = highlights[0]; // Use first highlight
      return (
        <span
          dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          className="highlighted-text"
        />
      );
    }

    // Fallback: no highlights, just return plain text
    return <span>{text}</span>;
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
                placeholder="Enter SKU name in Japanese (e.g. メイジバランスソフト)"
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

        {/* Search Summary */}
        {searchPerformed && !loading && (
          <div className="bg-gradient-to-r from-primary to-primary-400 text-white p-4 rounded-xl mb-8 shadow-lg">
            <p className="text-center font-semibold text-lg">
              Found <span className="font-bold text-2xl">{totalResults}</span>{' '}
              result
              {totalResults !== 1 ? 's' : ''}
              {query && (
                <span>
                  {' '}
                  for "<span className="font-bold">{query}</span>"
                </span>
              )}
            </p>
          </div>
        )}

        {/* Results Grid */}
        {results.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((result, index) => (
              <div
                key={`${result.id || index}`}
                className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-100 hover:scale-105 hover:border-primary/30"
              >
                {/* Card Header */}
                <div className="bg-gradient-to-r from-primary to-primary-400 p-4 flex justify-between items-center">
                  <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full">
                    <span className="text-white font-bold text-sm">
                      Score: {result.score.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-white/80 text-xs font-mono">
                    #{index + 1}
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-6 space-y-4">
                  <div className="space-y-2">
                    <div className="text-primary text-xs font-bold uppercase tracking-wider">
                      SKU Name
                    </div>
                    <div className="text-gray-900 font-semibold text-lg leading-relaxed">
                      {renderHighlightedText(
                        result.sku_name,
                        result.highlights?.sku_name,
                      )}
                    </div>
                  </div>

                  {/* Score Badge */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <div className="text-gray-500 text-xs">Relevance Score</div>
                    <div className="flex items-center">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary to-primary-400 transition-all duration-300"
                          style={{
                            width: `${Math.min(
                              maxScore > 0
                                ? (result.score / maxScore) * 100
                                : 0,
                              100,
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="ml-2 text-primary font-bold text-sm">
                        {result.score.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Optional: Image Placeholder */}
                {/* <div className="px-6 pb-6">
                  <div className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl h-32 flex items-center justify-center">
                    <span className="text-gray-400 text-4xl">📦</span>
                  </div>
                </div> */}
              </div>
            ))}
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
