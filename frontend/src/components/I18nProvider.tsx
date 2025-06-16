'use client';

import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { useEffect, useState } from 'react';

// Language code mapping table
const languageMap: { [key: string]: string } = {
  zh: 'zh-CN',    // Default Chinese maps to Simplified Chinese
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
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Ensure i18next is initialized
    if (!i18n.isInitialized) {
      i18n.init();
    }

    // Get current language
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

    // If current language is not supported, set to English
    if (!['en', 'zh-CN', 'zh-HK'].includes(currentLang)) {
      currentLang = 'en';
    }

    // Set language
    if (i18n.language !== currentLang) {
      i18n.changeLanguage(currentLang);
    }

    setMounted(true);
  }, []);

  // Prevent hydration mismatch by not rendering until after mount
  if (!mounted) {
    return null;
  }

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
} 