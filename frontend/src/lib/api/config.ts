import { ApiClient } from './client';
import { SettingsType } from './types';

export class ConfigApi extends ApiClient {
  constructor() {
    super('/api/v1');
  }

  async getConfig(): Promise<SettingsType> {
    return await this.get('/config');
  }

  async updateConfig(config: SettingsType): Promise<SettingsType> {
    return await this.post('/config', config);
  }
} 