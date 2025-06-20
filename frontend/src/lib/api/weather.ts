import { ApiClient } from './client';
import { WeatherData, WeatherRequest } from './types';

export class WeatherApi extends ApiClient {
  constructor() {
    super('/api/v1');
  }

  async getWeather(request: WeatherRequest): Promise<WeatherData> {
    return await this.post('/weather', request);
  }
} 