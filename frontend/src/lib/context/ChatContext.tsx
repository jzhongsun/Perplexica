'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { Chat } from '../api/types';

export interface ChatData {
  message: string;
  focusMode: string;
  optimizationMode: string;
  fileIds: string[];
  files: Array<{ fileName: string; fileExtension: string; fileId: string }>;
}

interface ChatContextType {
  chatData: Record<string, ChatData>;
  setChatData: (chatId: string, data: ChatData) => void;

  chats: Record<string, Chat>;
  setChat: (chatId: string, chat: Chat) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [chatData, setChatDataState] = useState<Record<string, ChatData>>({});
  const [chats, setChatState] = useState<Record<string, Chat>>({});
  
  const setChatData = (chatId: string, data: ChatData) => {
    setChatDataState(prev => ({
      ...prev,
      [chatId]: data
    }));
  };

  const setChat = (chatId: string, chat: Chat) => {
    setChatState(prev => ({
      ...prev,
      [chatId]: chat
    }));
  };

  return (
    <ChatContext.Provider value={{ chatData, setChatData, chats, setChat }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
} 