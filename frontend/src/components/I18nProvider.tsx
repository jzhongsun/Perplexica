'use client';

import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { useEffect } from 'react';

// 语言代码映射表
const languageMap: { [key: string]: string } = {
  zh: 'zh-CN',    // 默认中文映射到简体中文
  'zh-cn': 'zh-CN',
  'zh-hans': 'zh-CN',
  'zh-hk': 'zh-HK',
  'zh-tw': 'zh-HK',
  'zh-hant': 'zh-HK',
};

export default function I18nProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    // 确保 i18next 已经初始化
    if (!i18n.isInitialized) {
      i18n.init();
    }

    // 获取当前语言
    let currentLang = 'en';
    try {
      currentLang = localStorage.getItem('i18nextLng') || navigator.language.toLowerCase();
      if (currentLang.startsWith('zh')) {
        currentLang = currentLang === 'zh-HK' || currentLang === 'zh-TW' || currentLang === 'zh-hant' 
          ? 'zh-HK' 
          : 'zh-CN';
      }
    } catch (e) {
      // Ignore errors
    }

    // 如果当前语言不是支持的语言之一，设置为英语
    if (!['en', 'zh-CN', 'zh-HK'].includes(currentLang)) {
      currentLang = 'en';
    }

    // 设置语言
    if (i18n.language !== currentLang) {
      i18n.changeLanguage(currentLang);
    }
  }, []);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
} 