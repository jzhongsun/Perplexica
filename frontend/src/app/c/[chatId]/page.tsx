'use client';

import { MessageSquare, Clock, Zap, ScanEye } from 'lucide-react';
import ChatWindow from '@/components/ChatWindow';
import TopNav from '@/components/TopNav';
import DeleteChat from '@/components/DeleteChat';
import { api } from '@/lib/api';
import { useEffect, useState } from 'react';
import { use } from 'react';
import { useChatContext } from '@/lib/context/ChatContext';
import { formatTimeDifference } from '@/lib/utils';

const Page = ({ params }: { params: Promise<{ chatId: string }> }) => {
  const { chatId } = use(params);
  const { chatData, chats, setChat } = useChatContext();
  const [error, setError] = useState(false);
  const [title, setTitle] = useState('');
  const [timeAgo, setTimeAgo] = useState<string>('');

  useEffect(() => {
    const fetchChat = async () => {
      try {
        if (!chats || !chats[chatId]) {
          const { chat: fetchedChat } = await api.chat.getChat(chatId);
          setChat(chatId, fetchedChat);
          if (fetchedChat.title) {
            setTitle(fetchedChat.title);
          }
        } else {
          setTitle(chats[chatId]?.title ?? '');
        }
        // Set initial time ago
        const newTimeAgo = formatTimeDifference(
          new Date(),
          new Date(chats[chatId]?.createdAt ?? '')
        );
        setTimeAgo(newTimeAgo);
      } catch (e) {
        setError(true);
        console.error('Error fetching chat:', e);
      }
    };

    fetchChat();

    // Update time ago every minute
    const intervalId = setInterval(() => {
      if (chats[chatId]?.createdAt) {
        const newTimeAgo = formatTimeDifference(
          new Date(),
          new Date(chats[chatId]?.createdAt)
        );
        setTimeAgo(newTimeAgo);
      }
    }, 20_000);

    return () => clearInterval(intervalId);
  }, [chatId, chats[chatId]?.createdAt]);

  const headerContent = (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-x-6">
        <div className="flex items-center gap-x-3">
          <span className="text-sm font-medium text-black dark:text-white">
            {title || 'New Chat'}
          </span>
        </div>
        {chats && (
          <>
            <div className="flex items-center gap-x-2 text-gray-600 dark:text-gray-300">
              <Clock className="w-4 h-4" />
              <span className="text-xs">{timeAgo} ago</span>
            </div>
            <div className="flex items-center gap-x-2 text-gray-600 dark:text-gray-300">
              <ScanEye className="w-4 h-4" />
              <span className="text-xs capitalize">{chats[chatId]?.focusMode}</span>
            </div>
            <div className="flex items-center gap-x-2 text-gray-600 dark:text-gray-300">
              <Zap className="w-4 h-4" />
              <span className="text-xs capitalize">{chats[chatId]?.optimizationMode}</span>
            </div>
          </>
        )}
      </div>
      <div className="flex items-center ml-auto pl-6">
        <DeleteChat redirect chatId={chatId} chats={[]} setChats={() => { }} />
      </div>
    </div>
  );

  return (
    <TopNav
      icon={<MessageSquare className="w-5 h-5 text-yellow-600 dark:text-yellow-300" />}
      title={headerContent}
    >
      <ChatWindow id={chatId} initialChat={chats[chatId]} initialChatData={chatData[chatId]} />
    </TopNav>
  );
};

export default Page;
