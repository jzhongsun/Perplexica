import { useState } from 'react';
import { UIMessage } from '@ai-sdk/react';
import { File } from './ChatWindow';
import { ChevronLeft, ChevronRight, Maximize2, Minimize2, PanelRight, FileText, MessageSquare } from 'lucide-react';
import { convertUIMessageToMessage } from '@/lib/messages';

export type WorkspacePanelMode = 'hidden' | 'normal' | 'wide' | 'auto';

interface WorkspacePanelProps {
  // messages: UIMessage[];
  files: File[];
  mode: WorkspacePanelMode;
  onModeChange: (mode: WorkspacePanelMode) => void;
}

const WorkspacePanel = ({ files, mode, onModeChange }: WorkspacePanelProps) => {
  const nextMode: Record<WorkspacePanelMode, WorkspacePanelMode> = {
    hidden: 'normal',
    normal: 'wide',
    wide: 'auto',
    auto: 'hidden',
  };

  const modeIcons: Record<WorkspacePanelMode, React.ReactNode> = {
    hidden: <PanelRight className="w-4 h-4" />,
    normal: <ChevronLeft className="w-4 h-4" />,
    wide: <Maximize2 className="w-4 h-4" />,
    auto: <Minimize2 className="w-4 h-4" />,
  };

  const modeLabels: Record<WorkspacePanelMode, string> = {
    hidden: 'Show Panel',
    normal: 'Normal View',
    wide: 'Wide View',
    auto: 'Auto Width',
  };

  if (mode === 'hidden') {
    return (
      <div className="flex items-center h-full border-l border-gray-200 dark:border-white/5 bg-white dark:bg-dark-secondary">
        <button
          onClick={() => onModeChange(nextMode[mode])}
          className="p-2 hover:bg-gray-100 dark:hover:bg-dark-secondary/50 rounded-lg transition-colors mx-auto"
          title={modeLabels[nextMode[mode]]}
        >
          {modeIcons[mode]}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-dark-secondary border rounded-lg border-gray-200 dark:border-white/5">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-white/5">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Reference Panel</h2>
        <button
          onClick={() => onModeChange(nextMode[mode])}
          className="p-2 hover:bg-gray-100 dark:hover:bg-dark-secondary/50 rounded-lg transition-colors"
          title={`Switch to ${modeLabels[nextMode[mode]]}`}
        >
          {modeIcons[mode]}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Files Section */}
          {files.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Attached Files</h3>
              </div>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center p-2.5 bg-gray-50 dark:bg-dark-secondary/50 rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-dark-secondary/70 transition-colors border border-gray-200 dark:border-white/5"
                  >
                    <FileText className="w-4 h-4 text-gray-400 dark:text-gray-500 mr-2 flex-shrink-0" />
                    <span className="truncate">
                      {file.fileName}
                      <span className="text-gray-500 dark:text-gray-400">.{file.fileExtension}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Messages Context */}
          {/* {messages.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <MessageSquare className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Recent Context</h3>
              </div>
              <div className="space-y-3">
                {messages.slice(-3).map((message, index) => {
                  const msg = convertUIMessageToMessage(message);
                  return (
                    <div
                      key={index}
                      className="p-3 bg-gray-50 dark:bg-dark-secondary/50 rounded-lg text-sm border border-gray-200 dark:border-white/5"
                    >
                      <div className="font-medium mb-1 text-gray-900 dark:text-gray-100">
                        {message.role === 'user' ? 'You' : 'Assistant'}
                      </div>
                      <div className="text-gray-600 dark:text-gray-300 line-clamp-2">
                        {msg.content}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )} */}
        </div>
      </div>
    </div>
  );
};

export default WorkspacePanel; 