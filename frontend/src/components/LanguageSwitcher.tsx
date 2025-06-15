'use client';

import { useEffect, useState } from 'react';
import Select from './ui/Select';
import { useTranslation } from 'react-i18next';

type Language = 'en' | 'zh-CN' | 'zh-HK' | 'system';

const LanguageSwitcher = ({ className }: { className?: string }) => {
  const [mounted, setMounted] = useState(false);
  const { i18n } = useTranslation();

  const handleLanguageChange = (language: Language) => {
    if (language === 'system') {
      localStorage.removeItem('language');
      // Get system language
      const systemLanguage = navigator.language.toLowerCase();
      const mappedLanguage = mapSystemLanguage(systemLanguage);
      i18n.changeLanguage(mappedLanguage);
    } else {
      localStorage.setItem('language', language);
      i18n.changeLanguage(language);
    }
  };

  const mapSystemLanguage = (systemLang: string): Language => {
    if (systemLang.startsWith('zh')) {
      // Handle Chinese variants
      if (systemLang.includes('hk') || systemLang.includes('tw')) {
        return 'zh-HK';
      }
      return 'zh-CN';
    }
    // Default to English for unsupported languages
    return 'en';
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  // Avoid Hydration Mismatch
  if (!mounted) {
    return null;
  }

  const currentLanguage = localStorage.getItem('language') || 'system';

  return (
    <Select
      className={className}
      value={currentLanguage}
      onChange={(e) => handleLanguageChange(e.target.value as Language)}
      options={[
        { value: 'system', label: 'System (Default)' },
        { value: 'en', label: 'English' },
        { value: 'zh-CN', label: '简体中文' },
        { value: 'zh-HK', label: '繁體中文（香港）' },
      ]}
    />
  );
};

export default LanguageSwitcher; 