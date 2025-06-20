import { Dialog } from '@headlessui/react';
import { useRef, useState } from 'react';
import { User as UserIcon, X, Camera, Mail, AtSign } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';
import { useUser } from '@/lib/hooks/useUser';
import { UserAvatar } from '@/components/UserAvatar';

interface UserProfilePanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UserProfilePanel({ isOpen, onClose }: UserProfilePanelProps) {
  const { t } = useTranslation();
  const { user } = useUser();
  const [savingStates, setSavingStates] = useState<Record<string, boolean>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [editedUser, setEditedUser] = useState({
    name: user?.name || '',
  });

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('avatar', file);

    try {
      setSavingStates((prev) => ({ ...prev, avatar: true }));
      const response = await fetch('/api/auth/avatar', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to update avatar');
      }

      // Force reload to update user data
      window.location.reload();
    } catch (error) {
      console.error('Error uploading avatar:', error);
    } finally {
      setSavingStates((prev) => ({ ...prev, avatar: false }));
    }
  };

  const handleSave = async () => {
    try {
      setSavingStates((prev) => ({ ...prev, profile: true }));
      // TODO: Implement profile update API endpoint
      const response = await fetch('/api/auth/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editedUser),
      });

      if (!response.ok) {
        throw new Error('Failed to update profile');
      }

      // Force reload to update user data
      window.location.reload();
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setSavingStates((prev) => ({ ...prev, profile: false }));
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
              <div className="flex items-center justify-between px-4 sm:px-6 py-6">
                <h2 className="flex items-center space-x-2 text-2xl font-semibold text-black dark:text-white">
                  <UserIcon className="w-6 h-6" />
                  <span>{t('profile.title')}</span>
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
              <div className="px-4 sm:px-6 py-6">
                {/* Avatar Section */}
                <div className="flex flex-col items-center space-y-4 mb-8">
                  <div className="relative group">
                    <UserAvatar user={user} size={96} />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 rounded-full transition-opacity duration-200"
                    >
                      <Camera className="w-6 h-6 text-white" />
                    </button>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleAvatarUpload}
                      accept="image/*"
                      className="hidden"
                    />
                  </div>
                  {savingStates.avatar && (
                    <p className="text-sm text-black/60 dark:text-white/60">
                      {t('profile.uploading')}
                    </p>
                  )}
                </div>

                {/* Form Fields */}
                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-black/70 dark:text-white/70">
                      {t('profile.name')}
                    </label>
                    <div className="relative">
                      <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-black/40 dark:text-white/40" />
                      <input
                        type="text"
                        value={editedUser.name}
                        onChange={(e) => setEditedUser(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full pl-10 pr-4 py-2 bg-light-secondary dark:bg-dark-secondary rounded-lg border border-light-200 dark:border-dark-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={t('profile.namePlaceholder')}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-black/70 dark:text-white/70">
                      {t('profile.email')}
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-black/40 dark:text-white/40" />
                      <input
                        type="email"
                        value={user?.email}
                        disabled
                        className="w-full pl-10 pr-4 py-2 bg-light-secondary/50 dark:bg-dark-secondary/50 rounded-lg border border-light-200 dark:border-dark-200 text-black/60 dark:text-white/60 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-black/40 dark:text-white/40">
                      {t('profile.emailNote')}
                    </p>
                  </div>
                </div>

                {/* Save Button */}
                <div className="mt-8">
                  <button
                    onClick={handleSave}
                    disabled={savingStates.profile}
                    className={cn(
                      "w-full py-2 px-4 rounded-lg font-medium transition-colors",
                      "bg-blue-500 hover:bg-blue-600 text-white",
                      "disabled:bg-blue-500/50 disabled:cursor-not-allowed"
                    )}
                  >
                    {savingStates.profile ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>{t('profile.saving')}</span>
                      </div>
                    ) : (
                      t('profile.save')
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  );
} 