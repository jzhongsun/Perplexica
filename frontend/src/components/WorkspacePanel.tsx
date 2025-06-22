import { useState } from 'react';
import { UIMessage } from '@ai-sdk/react';
import { File } from './ChatWindow';
import { BookCopy, FileText, Link } from 'lucide-react';
import MessageSources from './MessageSources';
import { convertUIMessageToMessage } from '@/lib/messages';
import { Document } from '@langchain/core/documents';

const WorkspacePanel = ({
  messages,
  files,
}: {
  messages: UIMessage[];
  files: File[];
}) => {
  const [activeTab, setActiveTab] = useState<'sources' | 'attachments'>('sources');

  // Get the latest assistant message with sources
  const latestAssistantMessage = messages
    .slice()
    .reverse()
    .find((msg) => {
      const message = convertUIMessageToMessage(msg);
      return message.role === 'assistant' && message.sources && message.sources.length > 0;
    });

  const convertedMessage = latestAssistantMessage ? convertUIMessageToMessage(latestAssistantMessage) : null;

  return (
    <div className="h-full flex flex-col">
      {/* Fixed header with tabs */}
      <div className="flex-none p-4 border-b border-light-secondary dark:border-dark-secondary bg-light-100 dark:bg-dark-100">
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('sources')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
              activeTab === 'sources'
                ? 'bg-light-secondary dark:bg-dark-secondary text-black dark:text-white'
                : 'text-black/50 dark:text-white/50 hover:bg-light-200 dark:hover:bg-dark-200'
            }`}
          >
            <Link size={16} />
            <span>Sources</span>
          </button>
          <button
            onClick={() => setActiveTab('attachments')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
              activeTab === 'files'
                ? 'bg-light-secondary dark:bg-dark-secondary text-black dark:text-white'
                : 'text-black/50 dark:text-white/50 hover:bg-light-200 dark:hover:bg-dark-200'
            }`}
          >
            <FileText size={16} />
            <span>Files</span>
          </button>
        </div>
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="p-4">
          {activeTab === 'sources' && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <BookCopy className="text-black dark:text-white" size={20} />
                <h3 className="text-black dark:text-white font-medium text-xl">
                  Latest Sources
                </h3>
              </div>
              {convertedMessage?.sources && convertedMessage.sources.length > 0 ? (
                <MessageSources sources={convertedMessage.sources as Document[]} />
              ) : (
                <p className="text-black/50 dark:text-white/50 text-sm">
                  No sources available for the current conversation.
                </p>
              )}
            </div>
          )}

          {activeTab === 'attachments' && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <FileText className="text-black dark:text-white" size={20} />
                <h3 className="text-black dark:text-white font-medium text-xl">
                  Attached Files
                </h3>
              </div>
              {files.length > 0 ? (
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-2 p-3 rounded-lg bg-light-100 dark:bg-dark-100"
                    >
                      <FileText size={16} className="text-black/70 dark:text-white/70" />
                      <span className="text-sm text-black dark:text-white truncate">
                        {file.name}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-black/50 dark:text-white/50 text-sm">
                  No files attached to the current conversation.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkspacePanel; 