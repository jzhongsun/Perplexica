import { AuthApi } from './auth';
import { ChatApi } from './chat';
import { ConfigApi } from './config';
import { DiscoverApi } from './discover';
import { WeatherApi } from './weather';
import { SearchApi } from './search';
import { SuggestionsApi } from './suggestions';

export * from './types';

export class Api {
  auth: AuthApi;
  chat: ChatApi;
  config: ConfigApi;
  discover: DiscoverApi;
  weather: WeatherApi;
  search: SearchApi;
  suggestions: SuggestionsApi;

  constructor() {
    this.auth = new AuthApi();
    this.chat = new ChatApi();
    this.config = new ConfigApi();
    this.discover = new DiscoverApi();
    this.weather = new WeatherApi();
    this.search = new SearchApi();
    this.suggestions = new SuggestionsApi();
  }
}

// Create a singleton instance
export const api = new Api();

// Export individual APIs for direct use
export {
  AuthApi,
  ChatApi,
  ConfigApi,
  DiscoverApi,
  WeatherApi,
  SearchApi,
  SuggestionsApi,
}; 