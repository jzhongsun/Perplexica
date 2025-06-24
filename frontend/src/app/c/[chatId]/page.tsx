'use client';

import { MessageSquare, Clock, Zap, ScanEye } from 'lucide-react';
import ChatWindow from '@/components/ChatWindow';
import TopNav from '@/components/TopNav';
import DeleteChat from '@/components/DeleteChat';
import { api } from '@/lib/api';
import { useEffect, useState, useRef } from 'react';
import { use } from 'react';
import { useChatContext } from '@/lib/context/ChatContext';
import { formatTimeDifference } from '@/lib/utils';
import { Chat } from '@/lib/api/types';

const Page = ({ params }: { params: Promise<{ chatId: string }> }) => {
  const { chatId } = use(params);
  const { chatData } = useChatContext();
  const [chat, setChat] = useState<Chat | null>(null);
  const [initialMessage, setInitialMessage] = useState<string | null>(null);

  const [newChatCreated, setNewChatCreated] = useState(false);
  const [error, setError] = useState(false);
  const [title, setTitle] = useState('');
  const [timeAgo, setTimeAgo] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  
  // 使用 ref 来跟踪已经初始化的 chatId
  const initializedChatId = useRef<string | null>(null);
  const isInitializingRef = useRef(false);

  useEffect(() => {
    const createOrFetchChat = async () => {
      // 如果这个 chatId 已经初始化过，或者正在初始化中，直接返回
      if (initializedChatId.current === chatId || isInitializingRef.current) {
        // 如果聊天已存在，更新标题和时间
        if (chat) {
          setTitle(chat?.title ?? '');
          if (chat?.createdAt) {
            const newTimeAgo = formatTimeDifference(
              new Date(),
              new Date(chat?.createdAt)
            );
            setTimeAgo(newTimeAgo);
          }
        }
        return;
      }

      console.log("createOrFetchChat - initializing", chatId);
      isInitializingRef.current = true;
      setIsLoading(true);
      
      try {
        if (chatData[chatId] && !newChatCreated) {
          // create chat
          const data = chatData[chatId];
          console.log("createOrFetchChat - creating chat", chatId, data);
          const {chat: createdChat} = await api.chat.createChat({
            chatId: chatId,
            title: data.message,
            messages: [],
            options: {
              focusMode: data.focusMode,
              optimizationMode: data.optimizationMode,
            }
          });
          setInitialMessage(data.message);
          setChat(createdChat);
          setNewChatCreated(true);
          setTitle(createdChat.title ?? "New chat");
          initializedChatId.current = chatId;
        } else {
          // fetch existing chat
          const { chat: fetchedChat } = await api.chat.getChat(chatId);
          setChat(fetchedChat);
          if (fetchedChat.title) {
            setTitle(fetchedChat.title);
          }
          initializedChatId.current = chatId;
        }
        
        // Set initial time ago
        if (chat?.createdAt) {
          const newTimeAgo = formatTimeDifference(
            new Date(),
            new Date(chat?.createdAt)
          );
          setTimeAgo(newTimeAgo);
        }
      } catch (e) {
        setError(true);
        console.error('Error fetching chat:', e);
      } finally {
        isInitializingRef.current = false;
        setIsLoading(false);
      }
    };

    createOrFetchChat();
  }, [chatId, chatData, newChatCreated, chat]);

  useEffect(() => {
    // Update time ago every 20 seconds
    const intervalId = setInterval(() => {
      if (chat?.createdAt) {
        const newTimeAgo = formatTimeDifference(
          new Date(),
          new Date(chat?.createdAt)
        );
        setTimeAgo(newTimeAgo);
      }
    }, 20_000);

    return () => clearInterval(intervalId);
  }, [chat]);

  const headerContent = (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-x-6">
        <div className="flex items-center gap-x-3">
          <span className="text-black dark:text-white">
            {(title || 'New Chat').length > 40 ? (title || 'New Chat').substring(0, 40) + '...' : (title || 'New Chat')}
          </span>
        </div>
        {chat && (
          <>
            <div className="flex items-center gap-x-2 text-gray-600 dark:text-gray-300">
              <Clock className="w-4 h-4" />
              <span className="text-xs">{timeAgo} ago</span>
            </div>
            <div className="flex items-center gap-x-2 text-gray-600 dark:text-gray-300">
              <ScanEye className="w-4 h-4" />
              <span className="text-xs capitalize">{chat?.focusMode}</span>
            </div>
            <div className="flex items-center gap-x-2 text-gray-600 dark:text-gray-300">
              <Zap className="w-4 h-4" />
              <span className="text-xs capitalize">{chat?.optimizationMode}</span>
            </div>
          </>
        )}
      </div>
      <div className="flex items-center ml-auto pl-6">
        <DeleteChat redirect chatId={chatId} chats={[]} setChats={() => { }} />
      </div>
    </div>
  );

  if (error) {
    return (
      <TopNav
        icon={<MessageSquare className="w-5 h-5 text-red-600 dark:text-red-300" />}
        title="Error loading chat"
      >
        <div className="flex flex-col items-center justify-center min-h-screen">
          <p className="dark:text-white/70 text-black/70 text-sm">
            Failed to load chat. Please try again later.
          </p>
        </div>
      </TopNav>
    );
  }

  return (
    <TopNav
      icon={<MessageSquare className="w-5 h-5 text-yellow-600 dark:text-yellow-300" />}
      title={headerContent}
    >
      {isLoading ? (
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-black dark:border-white" />
        </div>
      ) : (
        chat && <ChatWindow chat={chat} initialMessage={initialMessage} />
      )}
    </TopNav>
  );
};

export default Page;
