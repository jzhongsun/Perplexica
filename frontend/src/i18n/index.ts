'use client';

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Language code mapping table
const languageMap: { [key: string]: string } = {
  zh: 'zh-CN',    // Default Chinese maps to Simplified Chinese
  'zh-cn': 'zh-CN',
  'zh-hans': 'zh-CN',
  'zh-hk': 'zh-HK',
  'zh-tw': 'zh-HK',
  'zh-hant': 'zh-HK',
};

// Custom language detector
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

const initI18n = () => {
  if (i18n.isInitialized) {
    return i18n;
  }

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

  // Add custom language detector
  i18n.services.languageDetector.addDetector(customLanguageDetector);

  return i18n;
};

export default initI18n(); 