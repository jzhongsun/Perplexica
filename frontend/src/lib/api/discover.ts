import { ApiClient } from './client';
import { Article } from './types';

export class DiscoverApi extends ApiClient {
  constructor() {
    super('/api/v1');
  }

  async getArticles(preview: boolean = false): Promise<{ blogs: Article[] }> {
    const url = preview ? '/discover?mode=preview' : '/discover';
    return await this.get(url);
  }
} 