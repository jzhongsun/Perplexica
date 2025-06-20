'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface ChatData {
  message: string;
  focusMode: string;
  optimizationMode: string;
  fileIds: string[];
  files: Array<{ fileName: string; fileExtension: string; fileId: string }>;
}

interface ChatContextType {
  chatData: Record<string, ChatData>;
  setChatData: (chatId: string, data: ChatData) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [chatData, setChatDataState] = useState<Record<string, ChatData>>({});

  const setChatData = (chatId: string, data: ChatData) => {
    setChatDataState(prev => ({
      ...prev,
      [chatId]: data
    }));
  };

  return (
    <ChatContext.Provider value={{ chatData, setChatData }}>
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