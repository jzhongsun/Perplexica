'use client';

import { useEffect, useRef, useState } from 'react';
import Chat from './Chat';
import { toast } from 'sonner';
import { Settings } from 'lucide-react';
import Link from 'next/link';
import NextError from 'next/error';
import { UIMessage } from 'ai';
import { TextUIPart } from 'ai';
import { useChat, UseChatHelpers } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useTranslation } from 'react-i18next';
import { Chat as ChatType, ChatMessageMeta } from '@/lib/api/types';
import { api } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

export type Message = {
  messageId: string;
  chatId: string;
  createdAt: Date;
  content: string;
  role: 'user' | 'assistant';
  suggestions?: string[];
  sources?: Document[];
};

export interface File {
  fileName: string;
  fileExtension: string;
  fileId: string;
}

const checkConfig = async (
  setIsConfigReady: (ready: boolean) => void,
  setHasError: (hasError: boolean) => void,
  t: (key: string) => string,
) => {
  try {
    const autoImageSearch = localStorage.getItem('autoImageSearch');
    const autoVideoSearch = localStorage.getItem('autoVideoSearch');

    if (!autoImageSearch) {
      localStorage.setItem('autoImageSearch', 'true');
    }

    if (!autoVideoSearch) {
      localStorage.setItem('autoVideoSearch', 'false');
    }

    setIsConfigReady(true);
  } catch (err) {
    console.error(t('chat.error.configError'), err);
    setIsConfigReady(false);
    setHasError(true);
    toast.error(t('chat.error.configError'));
  }
};

const ChatWindow = ({ chat, initialMessage }: {
  chat: ChatType,
  initialMessage: string | null,
}) => {
  const { t } = useTranslation();
  const [isConfigReady, setIsConfigReady] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isMessagesLoaded, setIsMessagesLoaded] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [fileIds, setFileIds] = useState<string[]>([]);

  const transport = new DefaultChatTransport({
    api: 'http://localhost:8000/api/v1/chat-stream'
  });

  // Move useChat to top level - this is the fix for the Rules of Hooks violation
  const chatHelper = useChat<UIMessage<ChatMessageMeta>>({
    id: chat.id,
    transport: transport,
    experimental_throttle: 50
  });

  const sendMessage = async (message: string, messageId?: string) => {
    if (loading) return;
    if (!isConfigReady) {
      toast.error('Cannot send message before the configuration is ready');
      return;
    }

    setLoading(true);
    messageId = messageId ?? uuidv4();
    await chatHelper.sendMessage({
      id: messageId,
      role: 'user',
      parts: [
        {
          type: 'text',
          text: message,
        },
      ],
    }, {
      body: {
        options: {
          optimizationMode: chat?.optimizationMode,
          focusMode: chat?.focusMode,
        }
      }
    });
    setLoading(false);
  };

  // Handle config initialization
  useEffect(() => {
    if (!isConfigReady && !hasError) {
      checkConfig(setIsConfigReady, setHasError, t);
    }
  }, []);

  // Handle chat initialization
  useEffect(() => {
    const initializeChat = async () => {
      console.log("initializeChat", chat);

      if (!chat || loading || !isConfigReady) {
        return;
      }

      try {
        setLoading(true);

        // Convert API files to File type
        const newFiles = chat?.files.map(apiFile => ({
          fileName: apiFile.name || '',
          fileExtension: (apiFile.name || '').split('.').pop() || '',
          fileId: apiFile.fileId || '',
        }));

        setFiles(newFiles ?? []);
        setFileIds(newFiles?.map(file => file.fileId) ?? []);

        const fetchedMessages = await api.chat.fetchMessagesOfChat(chat.id);
        chatHelper.setMessages(fetchedMessages.messages);
        console.log("fetchedMessages", chat.id, fetchedMessages, chatHelper.messages);
        setIsMessagesLoaded(true);

        if (initialMessage) {
          sendMessage(initialMessage);
        }
      } catch (error) {
        console.error('Error initializing chat:', error);
        toast.error(t('chat.error.initError'));
        setHasError(true);
      } finally {
        setLoading(false);
      }
    };

    if (chat && isConfigReady) {
      initializeChat();
    }
  }, [chat, isConfigReady]);

  // Update ready state
  useEffect(() => {
    if (isMessagesLoaded && isConfigReady) {
      setIsReady(true);
      console.debug(new Date(), 'app:ready');
    } else {
      setIsReady(false);
    }
  }, [isMessagesLoaded, isConfigReady]);

  const rewrite = (messageId: string) => {
    const index = chatHelper.messages.findIndex((msg) => msg.id === messageId);
    if (index === -1) return;
    const message = chatHelper.messages[index - 1];
    chatHelper.setMessages((prev) => {
      return [...prev.slice(0, chatHelper.messages.length > 2 ? index - 1 : 0)];
    });
    chatHelper.setMessages((prev) => {
      return [...prev.slice(0, chatHelper.messages.length > 2 ? index - 1 : 0)];
    });
    sendMessage((message.parts[0] as TextUIPart)?.text, message.id);
  };

  if (hasError) {
    return (
      <div className="relative">
        <div className="absolute w-full flex flex-row items-center justify-end mr-5 mt-5">
          <Link href="/settings">
            <Settings className="cursor-pointer lg:hidden" />
          </Link>
        </div>
        <div className="flex flex-col items-center justify-center min-h-screen">
          <p className="dark:text-white/70 text-black/70 text-sm">
            Failed to connect to the server. Please try again later.
          </p>
        </div>
      </div>
    );
  }

  return notFound ? (
    <NextError statusCode={404} />
  ) : (
    <div className="flex flex-col h-screen pb-28 md:pb-0">
      {!isReady ? (
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-black dark:border-white" />
        </div>
      ) : (
        <>
          {chatHelper.messages.length === 0 ? (
            <div>Empty Chat</div>
          ) : (
            <Chat
              chat={chatHelper}
              messages={chatHelper.messages}
              loading={loading}
              sendMessage={sendMessage}
              setFiles={setFiles}
              setFileIds={setFileIds}
              files={files}
              fileIds={fileIds}
              messageAppeared={false}
              rewrite={rewrite}
            />
          )}
        </>
      )}
    </div>
  );
};

export default ChatWindow;

