import { AuthService } from './AuthService';
import config from '../config';

export interface SearchResult {
  id: string;
  sku_name: string;
  hinban: string;
  colorcd: string;
  colornm: string;
  sizecd: string;
  sizename: string;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  max_score: number;
  results: SearchResult[];
  took: number;
  timed_out: boolean;
}

export class SearchService {
  private authService: AuthService;
  private baseUrl: string;

  constructor(authService: AuthService) {
    this.authService = authService;
    this.baseUrl = config.API_BASE_URL;
  }

  public async searchSKU(
    query: string,
    size: number = 15,
  ): Promise<SearchResponse | null> {
    try {
      // Check if user is authenticated
      if (!this.authService.isAuthorized()) {
        throw new Error('User not authenticated');
      }

      // Get ID token for API Gateway authorization
      const idToken = this.authService.getIdToken();
      if (!idToken) {
        throw new Error('No valid ID token');
      }

      // Construct the search URL
      const searchUrl = `${this.baseUrl}/search/sku?q=${encodeURIComponent(
        query,
      )}&size=${size}`;

      console.log('Search URL:', searchUrl); // Debug log

      // Make the API request
      const response = await fetch(searchUrl, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token might be expired, try to refresh
          await this.authService.logout();
          throw new Error('Authentication failed. Please login again.');
        }
        throw new Error(
          `Search failed: ${response.status} ${response.statusText}`,
        );
      }

      const data: SearchResponse = await response.json();
      console.log('Search response:', data); // Debug log
      return data;
    } catch (error) {
      console.error('Search error:', error);
      throw error;
    }
  }

  public async searchSKUWithRetry(
    query: string,
    size: number = 15,
    maxRetries: number = 1,
  ): Promise<SearchResponse | null> {
    let retries = 0;

    while (retries <= maxRetries) {
      try {
        return await this.searchSKU(query, size);
      } catch (error) {
        if (retries === maxRetries) {
          throw error;
        }

        // If it's an auth error, don't retry
        if (
          error instanceof Error &&
          error.message.includes('Authentication failed')
        ) {
          throw error;
        }

        retries++;
        // Wait a bit before retrying
        await new Promise((resolve) => setTimeout(resolve, 1000 * retries));
      }
    }

    return null;
  }
}
