import ChatWindow from '@/components/ChatWindow';
import { Metadata } from 'next';
import { Suspense } from 'react';
import MetadataProvider from '@/components/MetadataProvider';

// Note: The metadata is now handled by MetadataProvider component
export const metadata: Metadata = {
  title: 'Chat - Perplexica',
  description: 'Chat with the internet, chat with Perplexica.',
};

const Home = () => {
  return (
    <div>
      <MetadataProvider />
      <Suspense>
        <ChatWindow />
      </Suspense>
    </div>
  );
};

export default Home;
