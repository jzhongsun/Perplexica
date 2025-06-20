import { ApiClient } from './client';
import { User } from './types';

export class AuthApi extends ApiClient {
  constructor() {
    super('/api/v1/auth');
  }

  async getMe(): Promise<User | null> {
    try {
      return await this.get<User>('/me');
    } catch (error) {
      return null;
    }
  }

  async login(email: string, password: string): Promise<User> {
    return await this.post<User>('/login', { email, password });
  }

  async logout(): Promise<void> {
    await this.post('/logout');
  }

  async updateAvatar(formData: FormData): Promise<{ avatar: string }> {
    return await this.post('/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async register(data: {
    email: string;
    password: string;
    name: string;
  }): Promise<User> {
    return await this.post<User>('/register', data);
  }

  async resetPassword(email: string): Promise<void> {
    await this.post('/reset-password', { email });
  }

  async verifyEmail(token: string): Promise<void> {
    await this.post('/verify-email', { token });
  }
} 