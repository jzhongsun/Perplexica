'use client';

import { Fragment, useEffect, useRef, useState } from 'react';
import MessageInput from './MessageInput';
import { File } from './ChatWindow';
import MessageBox from './MessageBox';
import MessageBoxLoading from './MessageBoxLoading';
import { UseChatHelpers, UIMessage } from '@ai-sdk/react';
import { convertUIMessageToMessage } from '@/lib/messages';
import WorkspacePanel from './WorkspacePanel';

type WorkspacePanelMode = 'hidden' | 'normal' | 'wide' | 'auto';

const PANEL_WIDTHS: Record<WorkspacePanelMode, string> = {
  hidden: 'w-12', // 48px - just enough for the icon
  normal: 'w-96', // 384px
  wide: 'w-1/2', // 50% of container width
  auto: 'w-1/3', // 33% of container width
};

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
  const [panelMode, setPanelMode] = useState<WorkspacePanelMode>('normal');

  useEffect(() => {
    const scroll = () => {
      messageEnd.current?.scrollIntoView({ behavior: 'smooth' });
    };

    if (messages.length === 1) {
      const message = convertUIMessageToMessage(messages[0]);
      document.title = `${message.content.substring(0, 30)} - Danus`;
    }

    if (messages[messages.length - 1]?.role == 'user') {
      scroll();
    }
  }, [messages]);

  const handlePanelModeChange = (mode: WorkspacePanelMode) => {
    setPanelMode(mode);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left side - Chat area */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Messages area - takes remaining space and scrolls */}
        <div className="flex-1 overflow-y-auto">
          <div className="flex flex-col space-y-6 pb-4 sm:mx-4 md:mx-8">
            {messages.map((msg, i) => {
              const isLast = i === messages.length - 1;

              return (
                <Fragment key={chat.id + "_" + msg.id}>
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
        
        {/* Message Input - fixed at bottom */}
        <div className="flex-shrink-0 px-4 py-4 border-t border-light-200 dark:border-dark-200">
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

      {/* Right side - Workspace panel */}
      <div 
        className={`${PANEL_WIDTHS[panelMode]} pt-4 overflow-y-auto transition-[width] duration-300 ease-in-out`}
      >
        <WorkspacePanel 
          // messages={messages}
          files={files}
          mode={panelMode}
          onModeChange={handlePanelModeChange}
        />
      </div>
    </div>
  );
};

export default Chat;
