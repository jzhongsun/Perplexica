import { ApiClient } from './client';
import { SuggestionsRequest } from './types';

export class SuggestionsApi extends ApiClient {
  constructor() {
    super('/api/v1');
  }

  async getSuggestions(request: SuggestionsRequest): Promise<{ suggestions: string[] }> {
    return await this.post('/suggestions', request);
  }
} 