import clsx, { ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const cn = (...classes: ClassValue[]) => twMerge(clsx(...classes));

/**
 * 解析日期字符串，如果没有时区信息则默认为 UTC
 */
const parseDate = (date: Date | string): Date => {
  if (date instanceof Date) {
    return date;
  }
  
  // 如果是字符串且不包含时区信息，在末尾添加 'Z' 表示 UTC
  if (typeof date === 'string') {
    // 检查是否已经包含时区信息（Z, +XX:XX, -XX:XX）
    const hasTimezone = /[Z]$|[+-]\d{2}:?\d{2}$/.test(date.trim());
    
    if (!hasTimezone) {
      // 如果是 ISO 格式但没有时区信息，添加 Z
      // 支持毫秒（3位）和微秒（6位）格式
      if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3,6})?$/.test(date.trim())) {
        return new Date(date + 'Z');
      }
      // 如果是简单的日期格式，也按 UTC 处理
      if (/^\d{4}-\d{2}-\d{2}$/.test(date.trim())) {
        return new Date(date + 'T00:00:00Z');
      }
    }
  }
  
  return new Date(date);
};

export const formatTimeDifference = (
  date1: Date | string,
  date2: Date | string,
): string => {
  // 确保两个日期都转换为 Date 对象，并考虑本地时区
  const localDate1 = parseDate(date1);
  const localDate2 = parseDate(date2);
  
  // 验证日期是否有效
  if (isNaN(localDate1.getTime()) || isNaN(localDate2.getTime())) {
    return 'Invalid date';
  }

  // 计算时间差（毫秒），使用本地时间
  const diffInSeconds = Math.floor(
    Math.abs(localDate2.getTime() - localDate1.getTime()) / 1000,
  );

  if (diffInSeconds < 60)
    return `${diffInSeconds} second${diffInSeconds !== 1 ? 's' : ''}`;
  else if (diffInSeconds < 3600)
    return `${Math.floor(diffInSeconds / 60)} minute${Math.floor(diffInSeconds / 60) !== 1 ? 's' : ''}`;
  else if (diffInSeconds < 86400)
    return `${Math.floor(diffInSeconds / 3600)} hour${Math.floor(diffInSeconds / 3600) !== 1 ? 's' : ''}`;
  else if (diffInSeconds < 31536000)
    return `${Math.floor(diffInSeconds / 86400)} day${Math.floor(diffInSeconds / 86400) !== 1 ? 's' : ''}`;
  else
    return `${Math.floor(diffInSeconds / 31536000)} year${Math.floor(diffInSeconds / 31536000) !== 1 ? 's' : ''}`;
};
