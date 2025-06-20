'use client';

import { cn } from '@/lib/utils';
import { SquarePen, LogOut, User, Settings } from 'lucide-react';
import Link from 'next/link';
import React, { type ReactNode, useState } from 'react';
import Layout from './Layout';
import { useTranslation } from 'react-i18next';
import {
  Popover,
  PopoverButton,
  PopoverPanel,
  Transition,
} from '@headlessui/react';
import { Fragment } from 'react';
import { UserAvatar } from './UserAvatar';
import { useUser } from '@/lib/hooks/useUser';
import { SettingsPanel } from './SettingsPanel';
import { UserProfilePanel } from './UserProfilePanel';

export interface TopNavContainerProps {
  children: ReactNode;
  leftContent?: ReactNode;
}

export const TopNavContainer = ({ children, leftContent }: TopNavContainerProps) => {
  const { t } = useTranslation();
  const { user, loading, logout } = useUser();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  return (
    <div>
      {/* Desktop Navigation */}
      <div className="hidden md:fixed md:top-0 md:left-0 md:right-0 md:z-50 md:flex md:flex-row">
        <div className="w-full h-12 flex flex-row items-center justify-between px-4 bg-transparent backdrop-blur-sm border-b border-black/5 dark:border-white/5">
          <Link href="/" aria-label={t('nav.home')}>
            <SquarePen className="cursor-pointer w-5 h-5" />
          </Link>

          <div className="flex items-center gap-x-6">
            {leftContent}

            <span className="text-black/30 dark:text-white/30">|</span>
            
            <Popover className="relative">
              <PopoverButton className="flex items-center justify-center rounded-full hover:ring-2 hover:ring-black/5 dark:hover:ring-white/5 transition duration-150">
                <UserAvatar user={user} size={32} />
              </PopoverButton>
              <Transition
                as={Fragment}
                enter="transition ease-out duration-150"
                enterFrom="opacity-0 translate-y-1"
                enterTo="opacity-100 translate-y-0"
                leave="transition ease-in duration-150"
                leaveFrom="opacity-100 translate-y-0"
                leaveTo="opacity-0 translate-y-1"
              >
                <PopoverPanel className="absolute right-0 z-10 mt-2 w-64 rounded-lg bg-white dark:bg-dark-primary border border-black/5 dark:border-white/5 shadow-lg">
                  <div className="p-2">
                    {user && (
                      <div className="px-3 py-2 border-b border-black/5 dark:border-white/5">
                        <div className="font-medium text-sm text-black dark:text-white">
                          {user.fullName || user.username}
                        </div>
                        <div className="text-xs text-black/60 dark:text-white/60">
                          {user.email}
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => setIsProfileOpen(true)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-black/70 dark:text-white/70 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition duration-150"
                    >
                      <User size={16} />
                      {t('nav.profile')}
                    </button>
                    <button
                      onClick={() => setIsSettingsOpen(true)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-black/70 dark:text-white/70 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition duration-150"
                    >
                      <Settings size={16} />
                      {t('nav.settings')}
                    </button>
                    <div className="h-[1px] my-1 bg-black/5 dark:bg-white/5" />
                    <button
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-black/70 dark:text-white/70 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition duration-150"
                      onClick={logout}
                    >
                      <LogOut size={16} />
                      {t('nav.logout')}
                    </button>
                  </div>
                </PopoverPanel>
              </Transition>
            </Popover>
          </div>
        </div>
      </div>

      <Layout>{children}</Layout>

      <SettingsPanel 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      <UserProfilePanel
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
      />
    </div>
  );
};

export default TopNavContainer; 