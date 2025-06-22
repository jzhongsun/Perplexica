'use client';

import { Fragment, useEffect, useRef } from 'react';
import MessageInput from './MessageInput';
import { File } from './ChatWindow';
import MessageBox from './MessageBox';
import MessageBoxLoading from './MessageBoxLoading';
import { UseChatHelpers, UIMessage } from '@ai-sdk/react';
import { convertUIMessageToMessage } from '@/lib/messages';

const Chat = ({
  loading,
  chat,
  messages,
  sendMessage,
  messageAppeared,
  rewrite,
  fileIds,
  setFileIds,
  files,
  setFiles,
}: {
  chat: UseChatHelpers<UIMessage<any>>;
  messages: UIMessage[];
  sendMessage: (message: string) => void;
  loading: boolean;
  messageAppeared: boolean;
  rewrite: (messageId: string) => void;
  fileIds: string[];
  setFileIds: (fileIds: string[]) => void;
  files: File[];
  setFiles: (files: File[]) => void;
}) => {
  const dividerRef = useRef<HTMLDivElement | null>(null);
  const messageEnd = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const scroll = () => {
      messageEnd.current?.scrollIntoView({ behavior: 'smooth' });
    };

    if (messages.length === 1) {
      const message = convertUIMessageToMessage(messages[0]);
      document.title = `${message.content.substring(0, 30)} - Perplexica`;
    }

    if (messages[messages.length - 1]?.role == 'user') {
      scroll();
    }
  }, [messages]);

  return (
    <div className="h-[calc(100vh-4rem)] overflow-hidden">
      <div className="h-full overflow-y-auto">
        <div className="flex flex-col space-y-6 pt-8 pb-32 sm:mx-4 md:mx-8">
          {messages.map((msg, i) => {
            const isLast = i === messages.length - 1;

            return (
              <Fragment key={msg.id}>
                <MessageBox
                  key={i}
                  uiMessage={msg}
                  messageIndex={i}
                  history={messages}
                  loading={loading}
                  dividerRef={isLast ? dividerRef : undefined}
                  isLast={isLast}
                  rewrite={rewrite}
                  sendMessage={sendMessage}
                />
                {!isLast && msg.role === 'assistant' && (
                  <div className="h-px w-full bg-light-secondary dark:bg-dark-secondary" />
                )}
              </Fragment>
            );
          })}
          {loading && !messageAppeared && <MessageBoxLoading />}
          <div ref={messageEnd} className="h-0" />
        </div>
      </div>
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
        <div className="mx-auto px-4 py-4">
          <MessageInput
            loading={loading}
            sendMessage={sendMessage}
            fileIds={fileIds}
            setFileIds={setFileIds}
            files={files}
            setFiles={setFiles}
          />
        </div>
      </div>
    </div>
  );
};

export default Chat;
