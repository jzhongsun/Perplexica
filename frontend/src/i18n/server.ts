import { createInstance } from 'i18next';
import { initReactI18next } from 'react-i18next';
import resourcesToBackend from 'i18next-resources-to-backend';
import { join } from 'path';

const initI18next = async (lang: string) => {
  const i18nInstance = createInstance();
  await i18nInstance
    .use(initReactI18next)
    .use(
      resourcesToBackend(
        (language: string, namespace: string) =>
          import(`@/../../public/locales/${language}/${namespace}.json`)
      )
    )
    .init({
      supportedLngs: ['en', 'zh-CN', 'zh-HK'],
      fallbackLng: 'en',
      lng: lang,
      fallbackNS: 'common',
      defaultNS: 'common',
      ns: 'common',
    });
  return i18nInstance;
};

export async function getTranslation(lang: string) {
  const i18nextInstance = await initI18next(lang);
  return {
    t: i18nextInstance.getFixedT(lang, 'common'),
  };
} 