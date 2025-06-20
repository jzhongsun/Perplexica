'use client';

import EmptyChat from '@/components/EmptyChat';
import { Suspense } from 'react';
import MetadataProvider from '@/components/MetadataProvider';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import crypto from 'crypto';
import TopNav from '@/components/TopNav';
import { useChatContext } from '@/lib/context/ChatContext';
import { Sparkles } from 'lucide-react';
import { api } from '@/lib/api';

const Home = () => {
  const router = useRouter();
  const { setChatData } = useChatContext();
  const [focusMode, setFocusMode] = useState('webSearch');
  const [optimizationMode, setOptimizationMode] = useState('speed');
  const [files, setFiles] = useState<Array<{ fileName: string; fileExtension: string; fileId: string }>>([]);
  const [fileIds, setFileIds] = useState<string[]>([]);

  const handleSendMessage = async (message: string) => {
    // Generate a new chat ID
    const chatId = crypto.randomBytes(20).toString('hex');

    const chat = await api.chat.createChat({
      id: chatId,
      messages: [
        {
          role: 'user',
          type: 'text',
          id: crypto.randomBytes(20).toString('hex'),
          createdAt: new Date().toISOString()
        }
      ],
      focusMode,
      optimizationMode,
      files: files.map((file) => ({
        name: file.fileName,
        fileId: file.fileId
      }))
    });

    // Store chat data in context
    setChatData(chatId, {
      message,
      focusMode,
      optimizationMode,
      fileIds,
      files
    });

    // Navigate to the chat page without query parameters
    router.push(`/c/${chatId}`);
  };

  return (
    <div>
      <MetadataProvider />
      <Suspense>
        <TopNav
          icon={
            <div className="flex items-center">
              <Sparkles className="w-5 h-5 text-yellow-500" />
            </div>
          }
          title="Danus - Chat with the internet"
        >
          <EmptyChat
            sendMessage={handleSendMessage}
            focusMode={focusMode}
            setFocusMode={setFocusMode}
            optimizationMode={optimizationMode}
            setOptimizationMode={setOptimizationMode}
            fileIds={fileIds}
            setFileIds={setFileIds}
            files={files}
            setFiles={setFiles}
          />
        </TopNav>
      </Suspense>
    </div>
  );
};

export default Home;
