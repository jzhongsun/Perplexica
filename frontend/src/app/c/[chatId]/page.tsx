import ChatWindow from '@/components/ChatWindow';
import TopNavContainer from '@/components/TopNavContainer';
import React from 'react';

const Page = ({ params }: { params: Promise<{ chatId: string }> }) => {
  const { chatId } = React.use(params);
  return (
    <TopNavContainer>
      <ChatWindow id={chatId} />
    </TopNavContainer>
  );
};

export default Page;
