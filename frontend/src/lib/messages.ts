import { UIMessage } from "@ai-sdk/react";
import { Message } from "@/components/ChatWindow";
import { randomBytes } from "crypto";
import { Document } from "@langchain/core/documents";

export const extractUIMessageTextContent = (uiMessage: UIMessage): string => {
    let content = '';
    for (const part of uiMessage.parts) {
        if (part.type === 'text') {
            content += part.text;
        }
    }
    return content;
}

export const convertUIMessageToMessage = (uiMessage: UIMessage): Message => {
    console.log('convertUIMessageToMessage', uiMessage);
    let content = '';
    const sources: Document[] = [];
    if (!uiMessage || !uiMessage.parts) {
        return {
            messageId: uiMessage ? (uiMessage.id || randomBytes(7).toString('hex')) : randomBytes(7).toString('hex'),
            chatId: '', // 需要从上下文获取
            createdAt: new Date(),
            content: '',
            role: uiMessage.role === 'system' ? 'assistant' : uiMessage.role,
        }
    }
    // 处理所有消息部分
    for (const part of uiMessage.parts) {
        switch (part.type) {
            case 'text':
                content += part.text;
                break;
            case 'reasoning':
                content += `\n${part.text}\n`;
                break;
            case 'source-url':
                sources.push({
                    pageContent: part.title || part.url,
                    metadata: {
                        source: part.url,
                        type: 'url',
                        id: part.sourceId,
                        ...part.providerMetadata
                    }
                });
                break;
            case 'source-document':
                sources.push({
                    pageContent: part.title,
                    metadata: {
                        source: part.filename || part.title,
                        type: part.mediaType,
                        id: part.sourceId,
                        ...part.providerMetadata
                    }
                });
                break;
            case 'file':
                content += `\n[${part.filename || 'File'}](${part.url})\n`;
                break;
            case 'step-start':
                content += '\n---\n';
                break;
            default:
                // 处理工具调用和数据部分
                if (part.type.startsWith('tool-')) {
                    const toolPart = part as any;
                    if (toolPart.state === 'result' && toolPart.result) {
                        content += `\n[Tool Result] ${JSON.stringify(toolPart.result)}\n`;
                    }
                } else if (part.type.startsWith('data-')) {
                    const dataPart = part as any;
                    if (dataPart.data) {
                        content += `\n[Data] ${JSON.stringify(dataPart.data)}\n`;
                    }
                }
        }
    }

    // 创建消息对象
    const message: Message = {
        messageId: uiMessage.id || randomBytes(7).toString('hex'),
        chatId: '', // 需要从上下文获取
        createdAt: new Date(),
        content: content.trim(),
        role: uiMessage.role === 'system' ? 'assistant' : uiMessage.role,
    };

    // 添加源文档
    if (sources.length > 0) {
        message.sources = sources;
    }

    // 处理元数据
    if (uiMessage.metadata) {
        const metadata = uiMessage.metadata as any;
        if (metadata.suggestions) {
            message.suggestions = metadata.suggestions;
        }
        if (metadata.sources) {
            message.sources = message.sources ? 
                [...message.sources, ...metadata.sources] : 
                metadata.sources;
        }
    }

    return message;
};
