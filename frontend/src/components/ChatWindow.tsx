'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Document } from '@langchain/core/documents';
import Navbar from './Navbar';
import Chat from './Chat';
import EmptyChat from './EmptyChat';
import crypto from 'crypto';
import { toast } from 'sonner';
import { useSearchParams } from 'next/navigation';
import { getSuggestions } from '@/lib/actions';
import { Settings } from 'lucide-react';
import Link from 'next/link';
import NextError from 'next/error';
import { UIMessage } from 'ai';
import { TextUIPart } from 'ai';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useTranslation } from 'react-i18next';
import { useChatContext } from '@/lib/context/ChatContext';
import { ChatMessageMeta } from '@/lib/api/types';
import { api } from '@/lib/api';

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

const loadMessages = async (
  chatId: string,
  setMessages: (messages: UIMessage[]) => void,
  setIsMessagesLoaded: (loaded: boolean) => void,
  setChatHistory: (history: UIMessage[]) => void,
  setFocusMode: (mode: string) => void,
  setNotFound: (notFound: boolean) => void,
  setFiles: (files: File[]) => void,
  setFileIds: (fileIds: string[]) => void,
) => {
  try {
    const { chat } = await api.chat.getChat(chatId);
    console.log(chat);
    
    const messages = [] as UIMessage[];
    setMessages(messages);

    const history = messages as UIMessage[];
    console.debug(new Date(), 'app:messages_loaded');

    const files = chat.files.map((file: any) => {
      return {
        fileName: file.name,
        fileExtension: file.name.split('.').pop(),
        fileId: file.fileId,
      };
    });

    setFiles(files);
    setFileIds(files.map((file: File) => file.fileId));

    setChatHistory(history);
    setFocusMode(chat.focusMode);
    setIsMessagesLoaded(true);
  } catch (error: any) {
    if (error.response?.status === 404) {
      setNotFound(true);
    } else {
      console.error(error);
      toast.error(('chat.error.loadError'));
    }
    setIsMessagesLoaded(true);
  }
};

const ChatWindow = ({ id }: { id?: string }) => {
  const { t } = useTranslation();
  const { chatData } = useChatContext();
  
  const [chatId, setChatId] = useState<string | undefined>(id);
  const [newChatCreated, setNewChatCreated] = useState(false);

  // Get initial data from context if available
  const initialChatData = chatId ? chatData[chatId] : undefined;
  const initialMessage = initialChatData?.message;
  const initialFocusMode = initialChatData?.focusMode;
  const initialOptimizationMode = initialChatData?.optimizationMode;
  const initialFileIds = initialChatData?.fileIds || [];
  const initialFiles = initialChatData?.files || [];

  const [files, setFiles] = useState<File[]>(initialFiles);
  const [fileIds, setFileIds] = useState<string[]>(initialFileIds);
  const [focusMode, setFocusMode] = useState(initialFocusMode || 'webSearch');
  const [optimizationMode, setOptimizationMode] = useState(initialOptimizationMode || 'speed');

  const [isConfigReady, setIsConfigReady] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const transport = new DefaultChatTransport({
    api: 'http://localhost:8000/api/v1/chat-stream'
  });

  const chatHelper = useChat<UIMessage<ChatMessageMeta>>({
    id: chatId!,
    transport: transport,
    experimental_throttle: 100
  });

  useEffect(() => {
    checkConfig(
      setIsConfigReady,
      setHasError,
      t
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [loading, setLoading] = useState(false);

  // const [chatHistory, setChatHistory] = useState<UIMessage[]>([]);
  // const [messages, setMessages] = useState<UIMessage[]>([]);

  const [isMessagesLoaded, setIsMessagesLoaded] = useState(false);

  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (
      chatId &&
      !newChatCreated &&
      !isMessagesLoaded &&
      chatHelper.messages.length === 0
    ) {
      loadMessages(
        chatId,
        (messages) => {
          // setMessages(messages as UIMessage[]);
          chatHelper.setMessages(messages as UIMessage<ChatMessageMeta>[]);
        },
        setIsMessagesLoaded,
        (history) => {
          // setChatHistory(history as UIMessage[]);
          // chatHelper.setMessages(history as UIMessage[]);
        },
        setFocusMode,
        setNotFound,
        setFiles,
        setFileIds,
      );
    } else if (!chatId) {
      setNewChatCreated(true);
      setIsMessagesLoaded(true);
      setChatId(crypto.randomBytes(20).toString('hex'));
      setChatId(chatHelper.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const messagesRef = useRef<UIMessage<ChatMessageMeta>[]>([]);

  useEffect(() => {
    messagesRef.current = chatHelper.messages;
  }, [chatHelper]);

  useEffect(() => {
    if (isMessagesLoaded && isConfigReady) {
      setIsReady(true);
      console.debug(new Date(), 'app:ready');
    } else {
      setIsReady(false);
    }
  }, [isMessagesLoaded, isConfigReady]);

  const sendMessage = async (message: string, messageId?: string) => {
    if (loading) return;
    if (!isConfigReady) {
      toast.error('Cannot send message before the configuration is ready');
      return;
    }

    setLoading(true);

    let sources: Document[] | undefined = undefined;
    let recievedMessage = '';
    let added = false;

    messageId = messageId ?? crypto.randomBytes(7).toString('hex');

    // setMessages((prevMessages) => [
    //   ...prevMessages,
    //   {
    //     id: messageId,
    //     role: 'user',
    //     parts: [
    //       {
    //         type: 'text',
    //         text: message,
    //       },
    //     ],
    //   }
    // ]);

    // const messageHandler = async (data: any) => {
    //   if (data.type === 'error') {
    //     toast.error(data.data);
    //     setLoading(false);
    //     return;
    //   }

    //   if (data.type === 'sources') {
    //     sources = data.data;
    //     if (!added) {
    //       setMessages((prevMessages) => [
    //         ...prevMessages,
    //         {
    //           content: '',
    //           messageId: data.messageId,
    //           chatId: chatId!,
    //           role: 'assistant',
    //           sources: sources,
    //           createdAt: new Date(),
    //         },
    //       ]);
    //       added = true;
    //     }
    //     setMessageAppeared(true);
    //   }

    //   if (data.type === 'message') {
    //     if (!added) {
    //       setMessages((prevMessages) => [
    //         ...prevMessages,
    //         {
    //           content: data.data,
    //           messageId: data.messageId,
    //           chatId: chatId!,
    //           role: 'assistant',
    //           sources: sources,
    //           createdAt: new Date(),
    //         },
    //       ]);
    //       added = true;
    //     }

    //     setMessages((prev) =>
    //       prev.map((message) => {
    //         if (message.messageId === data.messageId) {
    //           return { ...message, content: message.content + data.data };
    //         }

    //         return message;
    //       }),
    //     );

    //     recievedMessage += data.data;
    //     setMessageAppeared(true);
    //   }

    //   if (data.type === 'messageEnd') {
    //     setChatHistory((prevHistory) => [
    //       ...prevHistory,
    //       ['human', message],
    //       ['assistant', recievedMessage],
    //     ]);

    //     setLoading(false);

    //     const lastMsg = messagesRef.current[messagesRef.current.length - 1];

    //     const autoImageSearch = localStorage.getItem('autoImageSearch');
    //     const autoVideoSearch = localStorage.getItem('autoVideoSearch');

    //     if (autoImageSearch === 'true') {
    //       document
    //         .getElementById(`search-images-${lastMsg.messageId}`)
    //         ?.click();
    //     }

    //     if (autoVideoSearch === 'true') {
    //       document
    //         .getElementById(`search-videos-${lastMsg.messageId}`)
    //         ?.click();
    //     }

    //     if (
    //       lastMsg.role === 'assistant' &&
    //       lastMsg.sources &&
    //       lastMsg.sources.length > 0 &&
    //       !lastMsg.suggestions
    //     ) {
    //       const suggestions = await getSuggestions(messagesRef.current);
    //       setMessages((prev) =>
    //         prev.map((msg) => {
    //           if (msg.messageId === lastMsg.messageId) {
    //             return { ...msg, suggestions: suggestions };
    //           }
    //           return msg;
    //         }),
    //       );
    //     }
    //   }
    // };

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
          optimization_mode: optimizationMode,
          focus_mode: focusMode,
          // system_instructions: localStorage.getItem('systemInstructions'),
        }
      }
    });
  };
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

  useEffect(() => {
    if (chatId && initialMessage && chatHelper.messages.length === 0) {
      // Send initial message if available
      sendMessage(initialMessage);
    }
  }, [chatId, initialMessage]);

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
          {/* {chatHelper.messages.length === 0 ? (
            <EmptyChat />
          ) : (
            <Chat
              messages={chatHelper.messages}
              loading={loading}
              onRewrite={rewrite}
            />
          )} */}
        </>
      )}
    </div>
  );
};

export default ChatWindow;

