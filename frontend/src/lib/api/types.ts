import { UIMessage } from '@ai-sdk/react';

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: UIMessage[];
  files: Array<{
    name: string;
    fileId: string;
  }>;
  focusMode: string;
  optimizationMode: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatModel {
  provider: string;
  model: string;
  customOpenAIKey?: string;
  customOpenAIBaseURL?: string;
}

export interface Image {
  img_src: string;
  title: string;
  source_url: string;
}

export interface WeatherData {
  temperature: number;
  condition: string;
  humidity: number;
  windSpeed: number;
  icon: string;
  location: string;
}

export interface Article {
  id: string;
  title: string;
  thumbnail: string;
  url: string;
  source: string;
  publishedAt: string;
}

export interface SettingsType {
  automaticImageSearch: boolean;
  automaticVideoSearch: boolean;
  systemInstructions: string;
  [key: string]: any;
}

// Request Types
export interface WeatherRequest {
  lat: number;
  lng: number;
}

export interface ImageSearchRequest {
  query: string;
  chatHistory: UIMessage[];
  chatModel: ChatModel;
}

export interface SuggestionsRequest {
  chatHistory: UIMessage[];
  chatModel: ChatModel;
} 