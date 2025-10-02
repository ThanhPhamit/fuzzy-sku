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
  const [searchSize, setSearchSize] = useState(15);

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

        if (response) {
          setResults(response.hits.hits);
          setTotalResults(response.hits.total.value);
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

  const highlightQuery = (text: string, searchQuery: string): JSX.Element => {
    if (!searchQuery.trim()) return <span>{text}</span>;

    const regex = new RegExp(
      `(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`,
      'gi',
    );
    const parts = text.split(regex);

    return (
      <span>
        {parts.map((part, index) =>
          regex.test(part) ? (
            <mark key={index} className="search-highlight">
              {part}
            </mark>
          ) : (
            <span key={index}>{part}</span>
          ),
        )}
      </span>
    );
  };

  return (
    <div className="search-container">
      <div className="search-header">
        <h1>🔍 Fuzzy SKU Search</h1>
        <p>Search for products using Japanese SKU names with fuzzy matching</p>
      </div>

      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter SKU name in Japanese (e.g., メイジバランスソフト)"
            disabled={loading}
            className="search-input"
          />
          <div className="search-controls">
            <select
              value={searchSize}
              onChange={(e) => setSearchSize(Number(e.target.value))}
              disabled={loading}
              className="size-select"
            >
              <option value={10}>10 results</option>
              <option value={15}>15 results</option>
              <option value={25}>25 results</option>
              <option value={50}>50 results</option>
            </select>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="btn-primary search-btn"
            >
              {loading ? '🔄 Searching...' : '🔍 Search'}
            </button>
            {(query || results.length > 0) && (
              <button
                type="button"
                onClick={handleClear}
                disabled={loading}
                className="btn-secondary clear-btn"
              >
                🗑️ Clear
              </button>
            )}
          </div>
        </div>
      </form>

      {error && <div className="error-message">⚠️ {error}</div>}

      {searchPerformed && !loading && (
        <div className="search-summary">
          <p>
            Found <strong>{totalResults}</strong> result
            {totalResults !== 1 ? 's' : ''}
            {query && (
              <span>
                {' '}
                for "<strong>{query}</strong>"
              </span>
            )}
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="search-results">
          <div className="results-grid">
            {results.map((result, index) => (
              <div key={`${result._id}-${index}`} className="result-card">
                <div className="result-header">
                  <div className="result-score">
                    Score: {result._score.toFixed(2)}
                  </div>
                  <div className="result-id">ID: {result._id}</div>
                </div>

                <div className="result-content">
                  <div className="result-field">
                    <strong>SKU Code:</strong>
                    <span className="result-value">
                      {highlightQuery(
                        result._source.syohin_code || 'N/A',
                        query,
                      )}
                    </span>
                  </div>

                  <div className="result-field">
                    <strong>Product Name 1:</strong>
                    <span className="result-value">
                      {highlightQuery(
                        result._source.syohin_name_1 || 'N/A',
                        query,
                      )}
                    </span>
                  </div>

                  {result._source.syohin_name_2 && (
                    <div className="result-field">
                      <strong>Product Name 2:</strong>
                      <span className="result-value">
                        {highlightQuery(result._source.syohin_name_2, query)}
                      </span>
                    </div>
                  )}

                  {result._source.syohin_name_3 && (
                    <div className="result-field">
                      <strong>Product Name 3:</strong>
                      <span className="result-value">
                        {highlightQuery(result._source.syohin_name_3, query)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {searchPerformed && results.length === 0 && !loading && !error && (
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h3>No results found</h3>
          <p>Try adjusting your search terms or check the spelling.</p>
        </div>
      )}
    </div>
  );
};

export default SearchComponent;
