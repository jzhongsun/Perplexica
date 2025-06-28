'use client';

/* eslint-disable @next/next/no-img-element */
import React, { MutableRefObject, useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import {
  BookCopy,
  Disc3,
  Volume2,
  StopCircle,
  Layers3,
  Plus,
  User,
  SquareTerminal
} from 'lucide-react';
import Copy from './MessageActions/Copy';
import Rewrite from './MessageActions/Rewrite';
import MessageSources from './MessageSources';
import SearchImages from './SearchImages';
import SearchVideos from './SearchVideos';
import { useSpeech } from 'react-text-to-speech';
import { UIMessage } from '@ai-sdk/react';
import { convertUIMessageToMessage } from '@/lib/messages';
import { useTranslation } from 'react-i18next';
import { PartRenderer } from './parts/PartRenderer';

const MessageBox = ({
  uiMessage,
  messageIndex,
  history,
  loading,
  dividerRef,
  isLast,
  rewrite,
  sendMessage,
}: {
  uiMessage: UIMessage;
  messageIndex: number;
  history: UIMessage[];
  loading: boolean;
  dividerRef?: MutableRefObject<HTMLDivElement | null>;
  isLast: boolean;
  rewrite: (messageId: string) => void;
  sendMessage: (message: string) => void;
}) => {
  const { t } = useTranslation();
  // const lastUserMessage = uiMessage.role === 'assistant' ? convertUIMessageToMessage(history[messageIndex - 1]) : message;
  const [parsedMessage, setParsedMessage] = useState('');
  const [speechMessage, setSpeechMessage] = useState('');

  useEffect(() => {
    const message = convertUIMessageToMessage(uiMessage);
    const citationRegex = /\[([^\]]+)\]/g;
    const regex = /\[(\d+)\]/g;
    let processedMessage = message.content;

    if (message.role === 'assistant' && message.content.includes('<think>')) {
      const openThinkTag = processedMessage.match(/<think>/g)?.length || 0;
      const closeThinkTag = processedMessage.match(/<\/think>/g)?.length || 0;

      if (openThinkTag > closeThinkTag) {
        processedMessage += '</think> <a> </a>'; // The extra <a> </a> is to prevent the the think component from looking bad
      }
    }

    if (
      message.role === 'assistant' &&
      message?.sources &&
      message.sources.length > 0
    ) {
      setParsedMessage(
        processedMessage.replace(
          citationRegex,
          (_, capturedContent: string) => {
            const numbers = capturedContent
              .split(',')
              .map((numStr) => numStr.trim());

            const linksHtml = numbers
              .map((numStr) => {
                const number = parseInt(numStr);

                if (isNaN(number) || number <= 0) {
                  return `[${numStr}]`;
                }

                const source = message.sources?.[number - 1];
                const url = (source as any)?.metadata?.url || (source as any)?.url;

                if (url) {
                  return `<a href="${url}" target="_blank" className="bg-light-secondary dark:bg-dark-secondary px-1 rounded ml-1 no-underline text-xs text-black/70 dark:text-white/70 relative">${numStr}</a>`;
                } else {
                  return `[${numStr}]`;
                }
              })
              .join('');

            return linksHtml;
          },
        ),
      );
      setSpeechMessage(message.content.replace(regex, ''));
      return;
    }

    setSpeechMessage(message.content.replace(regex, ''));
    setParsedMessage(processedMessage);
  }, [uiMessage]);

  const { speechStatus, start, stop } = useSpeech({ text: speechMessage });

  return (
    <div>
      {uiMessage.role === 'user' && (
        <div
          className={cn(
            'w-full flex items-start',
            messageIndex === 0 ? 'pt-8' : 'pt-4',
            'break-words',
          )}
        >
          <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0 mr-4 mt-2">
            <User size={20} className="text-blue-600 dark:text-blue-400" />
          </div>
          <div className="min-w-[100px] w-fit bg-blue-50/80 dark:bg-blue-950/20 rounded-lg px-6 pr-6 py-4 shadow-sm mr-4">
            {uiMessage.parts.map((part, index) => (
              part.type === 'text' && (
                <span key={uiMessage + "_" + index} className="text-black dark:text-white font-[400]">
                  {part.text}
                </span>
              )
            ))}
          </div>
        </div>
      )}
      {uiMessage.role === 'assistant' && (
        <div className="w-full flex items-start">
          <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-green-900  flex items-center justify-center flex-shrink-0 mr-4 mt-4">
            <SquareTerminal size={20} className="text-purple-600 dark:text-green-400" />
          </div>
          <div className="min-w-[100px] w-fit mr-4">
            <div
              ref={dividerRef}
              className="w-full bg-gray-50/80 dark:bg-gray-900/20 rounded-lg px-6 py-4 shadow-sm"
            >
              <div className="flex flex-col space-y-2">
                {isLast && loading && (
                  <div className="flex flex-row items-center space-x-2">
                    <Disc3
                      className={cn(
                        'text-black dark:text-white',
                        isLast && loading ? 'animate-spin' : 'animate-none',
                      )}
                      size={20}
                    />
                    <h3 className="text-black dark:text-white text-xl">
                      Answering...
                    </h3>
                  </div>)}
                {uiMessage.parts.map((part, index) => {
                  // 检查是否需要跳过渲染（由于之前的插件处理了多个部分）
                  const skipIndices = new Set<number>();

                  return !skipIndices.has(index) && (
                    <div key={uiMessage.id + "_" + index} className='flex flex-col pb-4'>
                      <PartRenderer
                        part={part}
                        partIndex={index}
                        message={uiMessage}
                      />
                    </div>
                  );
                })}
                {loading && isLast ? null : (
                  <div className="flex flex-row items-center justify-between w-full text-black dark:text-white pt-2 -mx-2">
                    <div className="flex flex-row items-center space-x-1">
                      {/*  <button className="p-2 text-black/70 dark:text-white/70 rounded-xl hover:bg-light-secondary dark:hover:bg-dark-secondary transition duration-200 hover:text-black text-black dark:hover:text-white">
                        <Share size={18} />
                      </button> */}
                      {/* <Rewrite rewrite={rewrite} messageId={message.messageId} /> */}
                    </div>
                    <div className="flex flex-row items-center space-x-1">
                      {/* <Copy initialMessage={message.content} message={message} /> */}
                      <button
                        onClick={() => {
                          if (speechStatus === 'started') {
                            stop();
                          } else {
                            start();
                          }
                        }}
                        className="text-black/70 dark:text-white/70 rounded-xl hover:bg-light-secondary dark:hover:bg-dark-secondary transition duration-200 hover:text-black dark:hover:text-white"
                        title={speechStatus === 'started' ? t('chat.message.stopSpeaking') : t('chat.message.speak')}
                      >
                        {speechStatus === 'started' ? (
                          <StopCircle size={18} />
                        ) : (
                          <Volume2 size={18} />
                        )}
                      </button>
                    </div>
                  </div>
                )}
                {/* {isLast &&
                  message.suggestions &&
                  message.suggestions.length > 0 &&
                  message.role === 'assistant' &&
                  !loading && (
                    <>
                      <div className="h-px w-full bg-light-secondary dark:bg-dark-secondary" />
                      <div className="flex flex-col space-y-3 text-black dark:text-white">
                        <div className="flex flex-row items-center space-x-2 mt-4">
                          <Layers3 />
                          <h3 className="text-xl font-medium">Related</h3>
                        </div>
                        <div className="flex flex-col space-y-3">
                          {message.suggestions.map((suggestion, i) => (
                            <div
                              className="flex flex-col space-y-3 text-sm"
                              key={i}
                            >
                              <div className="h-px w-full bg-light-secondary dark:bg-dark-secondary" />
                              <div
                                onClick={() => {
                                  sendMessage(suggestion);
                                }}
                                className="cursor-pointer flex flex-row justify-between font-medium space-x-2 items-center"
                              >
                                <p className="transition duration-200 hover:text-[#24A0ED]">
                                  {suggestion}
                                </p>
                                <Plus
                                  size={20}
                                  className="text-[#24A0ED] flex-shrink-0"
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )} */}
              </div>
            </div>
          </div>
        </div>
      )}
      {uiMessage.role === 'system' && (
        <div className="flex flex-col space-y-9 lg:space-y-0 lg:flex-row lg:justify-between lg:space-x-9">
          <div
            ref={dividerRef}
            className="flex flex-col space-y-6 w-full lg:w-9/12"
          >
            {/* {message.sources && message.sources.length > 0 && (
              <div className="flex flex-col space-y-2">
                <div className="flex flex-row items-center space-x-2">
                  <BookCopy className="text-black dark:text-white" size={20} />
                  <h3 className="text-black dark:text-white text-xl">
                    Sources
                  </h3>
                </div>
                <MessageSources sources={message.sources} />
              </div>
            )} */}
          </div>
          <div className="lg:sticky lg:top-20 flex flex-col items-center space-y-3 w-full lg:w-3/12 z-30 h-full pb-4">
            {/* <SearchImages
              query={lastUserMessage.content}
              chatHistory={history.slice(0, messageIndex - 1)}
              messageId={message.messageId}
            />
            <SearchVideos
              chatHistory={history.slice(0, messageIndex - 1)}
              query={lastUserMessage.content}
              messageId={message.messageId}
            /> */}
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageBox;
