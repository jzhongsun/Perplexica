import { ApiClient } from './client';
import { Chat, ChatMessageMeta, ChatRequest } from './types';
import { UIMessage } from 'ai';

export class ChatApi extends ApiClient {
  constructor() {
    super('/api/v1');
  }

  async getChats(): Promise<{ chats: Chat[] }> {
    return await this.get('/chats');
  }

  async getChat(chatId: string): Promise<{ chat: Chat }> {
    return await this.get(`/chats/${chatId}`);
  }

  async deleteChat(chatId: string): Promise<void> {
    await this.delete(`/chats/${chatId}`);
  }

  async createChat(chat: Partial<ChatRequest>): Promise<{ chat: Chat }> {
    return await this.post('/chats', chat);
  }

  async updateChat(chatId: string, chat: Partial<Chat>): Promise<Chat> {
    return await this.put(`/chats/${chatId}`, chat);
  }

  async fetchMessagesOfChat(chatId: string): Promise<{ messages: UIMessage<ChatMessageMeta>[] }> {
    return await this.get(`/chats/${chatId}/messages`);
  }
} 