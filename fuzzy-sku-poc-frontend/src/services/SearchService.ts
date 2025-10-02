import { AuthService } from './AuthService';
import config from '../config';

export interface SearchResult {
  _id: string;
  _source: {
    syohin_code: string;
    syohin_name_1: string;
    syohin_name_2?: string;
    syohin_name_3?: string;
    [key: string]: any;
  };
  _score: number;
}

export interface SearchResponse {
  hits: {
    total: {
      value: number;
      relation: string;
    };
    hits: SearchResult[];
  };
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

      // Get access token
      const accessToken = this.authService.getAccessToken();
      if (!accessToken) {
        throw new Error('No valid access token');
      }

      // Construct the search URL
      const searchUrl = new URL('/search/sku', this.baseUrl);
      searchUrl.searchParams.append('q', query);
      searchUrl.searchParams.append('size', size.toString());

      // Make the API request
      const response = await fetch(searchUrl.toString(), {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${accessToken}`,
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
