'use client';

import { Settings as SettingsIcon, ArrowLeft, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';
import { Switch } from '@headlessui/react';
import { ImagesIcon, VideoIcon } from 'lucide-react';
import Link from 'next/link';
import ThemeSwitcher from '@/components/theme/Switcher';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { useTranslation } from 'react-i18next';
import { Textarea } from '@/components/ui/textarea';

interface SettingsType {
  openaiApiKey: string;
  groqApiKey: string;
  anthropicApiKey: string;
  geminiApiKey: string;
  ollamaApiUrl: string;
  lmStudioApiUrl: string;
  deepseekApiKey: string;
  customOpenaiApiKey: string;
  customOpenaiApiUrl: string;
  customOpenaiModelName: string;
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  isSaving?: boolean;
  onSave?: (value: string) => void;
}


interface TextareaProps extends React.InputHTMLAttributes<HTMLTextAreaElement> {
  isSaving?: boolean;
  onSave?: (value: string) => void;
}

const SettingsSection = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => (
  <div className="flex flex-col space-y-4 p-4 bg-light-secondary/50 dark:bg-dark-secondary/50 rounded-xl border border-light-200 dark:border-dark-200">
    <h2 className="text-black/90 dark:text-white/90 font-medium">{title}</h2>
    {children}
  </div>
);

const Page = () => {
  const { t } = useTranslation();
  const [mounted, setMounted] = useState(false);
  const [config, setConfig] = useState<SettingsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [automaticImageSearch, setAutomaticImageSearch] = useState(false);
  const [automaticVideoSearch, setAutomaticVideoSearch] = useState(false);
  const [systemInstructions, setSystemInstructions] = useState<string>('');
  const [savingStates, setSavingStates] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchConfig = async () => {
      const res = await fetch(`/api/v1/config`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = (await res.json()) as SettingsType;
      setConfig(data);

      setAutomaticImageSearch(
        localStorage.getItem('autoImageSearch') === 'true',
      );
      setAutomaticVideoSearch(
        localStorage.getItem('autoVideoSearch') === 'true',
      );

      setSystemInstructions(localStorage.getItem('systemInstructions') || '');

      setIsLoading(false);
    };

    fetchConfig();
    setMounted(true);
  }, []);

  // Prevent hydration mismatch by not rendering until after mount
  if (!mounted) {
    return null;
  }

  const saveConfig = async (key: string, value: any) => {
    setSavingStates((prev) => ({ ...prev, [key]: true }));

    try {
      const updatedConfig = {
        ...config,
        [key]: value,
      } as SettingsType;

      const response = await fetch(`/api/v1/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedConfig),
      });

      if (!response.ok) {
        throw new Error('Failed to update config');
      }

      setConfig(updatedConfig);

      if (
        key.toLowerCase().includes('api') ||
        key.toLowerCase().includes('url')
      ) {
        const res = await fetch(`/api/v1/config`, {
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!res.ok) {
          throw new Error('Failed to fetch updated config');
        }

        const data = await res.json();
        setConfig(data);
      }

      if (key === 'automaticImageSearch') {
        localStorage.setItem('autoImageSearch', value.toString());
      } else if (key === 'automaticVideoSearch') {
        localStorage.setItem('autoVideoSearch', value.toString());
      } else if (key === 'systemInstructions') {
        localStorage.setItem('systemInstructions', value);
      }
    } catch (err) {
      console.error('Failed to save:', err);
      setConfig((prev) => ({ ...prev! }));
    } finally {
      setTimeout(() => {
        setSavingStates((prev) => ({ ...prev, [key]: false }));
      }, 500);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex flex-col pt-4">
        <div className="flex items-center space-x-2">
          <Link href="/" className="lg:hidden">
            <ArrowLeft className="text-black/70 dark:text-white/70" />
          </Link>
          <div className="flex flex-row space-x-0.5 items-center">
            <SettingsIcon size={23} />
            <h1 className="text-3xl font-medium p-2">{t('settings.title')}</h1>
          </div>
        </div>
        <hr className="border-t border-[#2B2C2C] my-4 w-full" />
      </div>

      {isLoading ? (
        <div className="flex flex-row items-center justify-center min-h-[50vh]">
          <svg
            aria-hidden="true"
            className="w-8 h-8 text-light-200 fill-light-secondary dark:text-[#202020] animate-spin dark:fill-[#ffffff3b]"
            viewBox="0 0 100 101"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M100 50.5908C100.003 78.2051 78.1951 100.003 50.5908 100C22.9765 99.9972 0.997224 78.018 1 50.4037C1.00281 22.7993 22.8108 0.997224 50.4251 1C78.0395 1.00281 100.018 22.8108 100 50.4251ZM9.08164 50.594C9.06312 73.3997 27.7909 92.1272 50.5966 92.1457C73.4023 92.1642 92.1298 73.4365 92.1483 50.6308C92.1669 27.8251 73.4392 9.0973 50.6335 9.07878C27.8278 9.06026 9.10003 27.787 9.08164 50.594Z"
              fill="currentColor"
            />
            <path
              d="M93.9676 39.0409C96.393 38.4037 97.8624 35.9116 96.9801 33.5533C95.1945 28.8227 92.871 24.3692 90.0681 20.348C85.6237 14.1775 79.4473 9.36872 72.0454 6.45794C64.6435 3.54717 56.3134 2.65431 48.3133 3.89319C45.869 4.27179 44.3768 6.77534 45.014 9.20079C45.6512 11.6262 48.1343 13.0956 50.5786 12.717C56.5073 11.8281 62.5542 12.5399 68.0406 14.7911C73.527 17.0422 78.2187 20.7487 81.5841 25.4923C83.7976 28.5886 85.4467 32.059 86.4416 35.7474C87.1273 38.1189 89.5423 39.6781 91.9676 39.0409Z"
              fill="currentFill"
            />
          </svg>
          <span className="ml-2">{t('settings.loading')}</span>
        </div>
      ) : (
        config && (
          <div className="flex flex-col space-y-6 pb-28 lg:pb-8">
            <SettingsSection title={t('settings.appearance.title')}>
              <div className="flex flex-col space-y-1">
                <p className="text-black/70 dark:text-white/70 text-sm">
                  {t('settings.appearance.theme')}
                </p>
                <ThemeSwitcher />
              </div>
              <div className="flex flex-col space-y-1">
                <p className="text-black/70 dark:text-white/70 text-sm">
                  {t('settings.appearance.language')}
                </p>
                <LanguageSwitcher />
              </div>
            </SettingsSection>

            <SettingsSection title={t('settings.automaticSearch.title')}>
              <div className="flex flex-col space-y-4">
                <div className="flex items-center justify-between p-3 bg-light-secondary dark:bg-dark-secondary rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-light-200 dark:bg-dark-200 rounded-lg">
                      <ImagesIcon
                        size={18}
                        className="text-black/70 dark:text-white/70"
                      />
                    </div>
                    <div>
                      <p className="text-sm text-black/90 dark:text-white/90 font-medium">
                        {t('settings.automaticSearch.images.title')}
                      </p>
                      <p className="text-xs text-black/60 dark:text-white/60 mt-0.5">
                        {t('settings.automaticSearch.images.description')}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={automaticImageSearch}
                    onChange={(checked) => {
                      setAutomaticImageSearch(checked);
                      saveConfig('automaticImageSearch', checked);
                    }}
                    className={cn(
                      automaticImageSearch
                        ? 'bg-[#24A0ED]'
                        : 'bg-light-200 dark:bg-dark-200',
                      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none'
                    )}
                  >
                    <span
                      className={cn(
                        automaticImageSearch ? 'translate-x-6' : 'translate-x-1',
                        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
                      )}
                    />
                  </Switch>
                </div>

                <div className="flex items-center justify-between p-3 bg-light-secondary dark:bg-dark-secondary rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-light-200 dark:bg-dark-200 rounded-lg">
                      <VideoIcon
                        size={18}
                        className="text-black/70 dark:text-white/70"
                      />
                    </div>
                    <div>
                      <p className="text-sm text-black/90 dark:text-white/90 font-medium">
                        {t('settings.automaticSearch.videos.title')}
                      </p>
                      <p className="text-xs text-black/60 dark:text-white/60 mt-0.5">
                        {t('settings.automaticSearch.videos.description')}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={automaticVideoSearch}
                    onChange={(checked) => {
                      setAutomaticVideoSearch(checked);
                      saveConfig('automaticVideoSearch', checked);
                    }}
                    className={cn(
                      automaticVideoSearch
                        ? 'bg-[#24A0ED]'
                        : 'bg-light-200 dark:bg-dark-200',
                      'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none'
                    )}
                  >
                    <span
                      className={cn(
                        automaticVideoSearch ? 'translate-x-6' : 'translate-x-1',
                        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform'
                      )}
                    />
                  </Switch>
                </div>
              </div>
            </SettingsSection>

            <SettingsSection title={t('settings.systemInstructions.title')}>
              <Textarea
                value={systemInstructions}
                placeholder={t('settings.systemInstructions.placeholder')}
                onChange={(e) => setSystemInstructions(e.target.value)}
                onBlur={(e) => saveConfig('systemInstructions', e.target.value)}
                isSaving={savingStates['systemInstructions']}
              />
            </SettingsSection>
          </div>
        )
      )}
    </div>
  );
};

export default Page;
