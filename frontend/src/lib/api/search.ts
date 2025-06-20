import { ApiClient } from './client';
import { Image, ImageSearchRequest } from './types';

export class SearchApi extends ApiClient {
  constructor() {
    super('/api/v1/search');
  }

  async searchImages(request: ImageSearchRequest): Promise<{ images: Image[] }> {
    return await this.post('/images', request);
  }

  async searchVideos(request: ImageSearchRequest): Promise<{ videos: any[] }> {
    return await this.post('/videos', request);
  }
} 