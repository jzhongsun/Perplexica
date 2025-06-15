'use client';

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// 语言代码映射表
const languageMap: { [key: string]: string } = {
  zh: 'zh-CN',    // 默认中文映射到简体中文
  'zh-cn': 'zh-CN',
  'zh-hans': 'zh-CN',
  'zh-hk': 'zh-HK',
  'zh-tw': 'zh-HK',
  'zh-hant': 'zh-HK',
};

// 自定义语言检测器
const customLanguageDetector = {
  name: 'customLanguageDetector',
  lookup: () => {
    if (typeof window === 'undefined') return 'en';
    
    let lng;
    try {
      lng = localStorage.getItem('i18nextLng');
    } catch (e) {
      lng = null;
    }

    if (!lng) {
      try {
        lng = navigator.language.toLowerCase();
      } catch (e) {
        return 'en';
      }
    }

    if (lng.startsWith('zh')) {
      return languageMap[lng] || 'zh-CN';
    }
    return lng;
  },
  cacheUserLanguage: (lng: string) => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem('i18nextLng', lng);
    } catch (e) {
      // Ignore storage errors
    }
  }
};

// Initialize i18next only if it hasn't been initialized yet
if (!i18n.isInitialized) {
  i18n
    .use(Backend)
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      fallbackLng: 'en',
      supportedLngs: ['en', 'zh-CN', 'zh-HK'],
      ns: ['common'],
      defaultNS: 'common',
      fallbackNS: false,
      load: 'currentOnly',
      debug: process.env.NODE_ENV === 'development',
      interpolation: {
        escapeValue: false,
      },
      backend: {
        loadPath: '/locales/{{lng}}/{{ns}}.json',
      },
      detection: {
        order: ['customLanguageDetector', 'querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
        lookupQuerystring: 'lang',
        lookupCookie: 'i18next',
        lookupLocalStorage: 'i18nextLng',
        caches: ['localStorage', 'cookie'],
      },
    });

  // 添加自定义语言检测器
  i18n.services.languageDetector.addDetector(customLanguageDetector);
}

export default i18n; 