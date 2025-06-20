'use client';

import EmptyChat from '@/components/EmptyChat';
import { Suspense } from 'react';
import MetadataProvider from '@/components/MetadataProvider';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import crypto from 'crypto';
import TopNav from '@/components/TopNav';
import { useChatContext } from '@/lib/context/ChatContext';

const Home = () => {
  const router = useRouter();
  const { setChatData } = useChatContext();
  const [focusMode, setFocusMode] = useState('webSearch');
  const [optimizationMode, setOptimizationMode] = useState('speed');
  const [files, setFiles] = useState<Array<{ fileName: string; fileExtension: string; fileId: string }>>([]);
  const [fileIds, setFileIds] = useState<string[]>([]);

  const handleSendMessage = (message: string) => {
    // Generate a new chat ID
    const chatId = crypto.randomBytes(20).toString('hex');

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
        <TopNav>
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
