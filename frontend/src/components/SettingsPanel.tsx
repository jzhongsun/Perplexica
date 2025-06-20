import { Dialog } from '@headlessui/react';
import { useEffect, useState } from 'react';
import { Settings as SettingsIcon, X, ImagesIcon, VideoIcon } from 'lucide-react';
import { Switch } from '@headlessui/react';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';
import ThemeSwitcher from '@/components/theme/Switcher';
import LanguageSwitcher from '@/components/LanguageSwitcher';
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

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
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

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { t } = useTranslation();
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

    if (isOpen) {
      fetchConfig();
    }
  }, [isOpen]);

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
    <Dialog 
      open={isOpen} 
      onClose={onClose}
      className="relative z-50"
    >
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/25 dark:bg-black/40 backdrop-blur-sm transition-opacity"
        aria-hidden="true"
      />

      {/* Full-screen container for positioning */}
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-start justify-end">
          <div 
            className={cn(
              "relative w-full transform overflow-hidden transition-all",
              "h-[100dvh]", // Full height on mobile
              "sm:w-[32rem]", // Default width on tablet
              // Enhanced visibility in dark mode
              "bg-light-primary border-l border-light-200",
              "dark:bg-dark-primary dark:border-white/10",
              // Shadow enhancement
              "shadow-[0_0_15px_rgba(0,0,0,0.1)]",
              "dark:shadow-[0_0_15px_rgba(0,0,0,0.3)]"
            )}
          >
            {/* Header */}
            <div className="sticky top-0 z-50 bg-light-primary dark:bg-dark-primary border-b border-light-200 dark:border-white/10">
              <div className="flex items-center justify-between px-4 sm:px-6 py-4">
                <h2 className="flex items-center space-x-2 text-xl font-semibold text-black dark:text-white">
                  <SettingsIcon className="w-5 h-5" />
                  <span>{t('settings.title')}</span>
                </h2>
                <button
                  type="button"
                  className="text-black/50 dark:text-white/50 hover:text-black dark:hover:text-white rounded-lg p-1 hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                  onClick={onClose}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="overflow-y-auto h-[calc(100dvh-5rem)]">
              <div className="px-4 sm:px-6 py-6 space-y-6">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black dark:border-white" />
                  </div>
                ) : (
                  config && (
                    <>
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
                    </>
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  );
}