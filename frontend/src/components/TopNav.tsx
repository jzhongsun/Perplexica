'use client';

import { cn } from '@/lib/utils';
import { BookOpenText, Home, Search } from 'lucide-react';
import Link from 'next/link';
import { useSelectedLayoutSegments } from 'next/navigation';
import React, { type ReactNode, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { TopNavContainer } from './TopNavContainer';

const HorizontalNavContainer = ({ children }: { children: ReactNode }) => {
  return (
    <div className="flex flex-row items-center gap-x-6">{children}</div>
  );
};

const TopNav = ({ children }: { children: React.ReactNode }) => {
  const segments = useSelectedLayoutSegments();
  const { t } = useTranslation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const navLinks = [
    {
      icon: Home,
      href: '/',
      active: segments.length === 0 || segments.includes('c'),
      label: t('nav.home'),
    },
    {
      icon: Search,
      href: '/discover',
      active: segments.includes('discover'),
      label: t('nav.discover'),
    },
    {
      icon: BookOpenText,
      href: '/library',
      active: segments.includes('library'),
      label: t('nav.library'),
    },
  ];

  // Prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  const navigationLinks = (
    <HorizontalNavContainer>
      {navLinks.map((link, i) => (
        <Link
          key={i}
          href={link.href}
          className={cn(
            'relative flex flex-row items-center gap-x-2 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 duration-150 transition px-3 py-1.5 rounded-lg',
            link.active
              ? 'text-black dark:text-white'
              : 'text-black/70 dark:text-white/70',
          )}
          aria-current={link.active ? 'page' : undefined}
        >
          <link.icon size={18} aria-hidden="true" />
          <span className="text-sm">{link.label}</span>
          {link.active && (
            <div className="absolute bottom-0 left-0 h-0.5 w-full rounded-t-lg bg-black dark:bg-white" />
          )}
        </Link>
      ))}
    </HorizontalNavContainer>
  );

  return (
    <TopNavContainer leftContent={navigationLinks}>
      {/* Mobile Navigation */}
      <div className="fixed bottom-0 w-full z-50 flex flex-row items-center justify-around bg-transparent backdrop-blur-sm border-t border-black/5 dark:border-white/5 px-4 py-4 shadow-sm md:hidden">
        {navLinks.map((link, i) => (
          <Link
            href={link.href}
            key={i}
            className={cn(
              'relative flex flex-col items-center space-y-1 text-center',
              link.active
                ? 'text-black dark:text-white'
                : 'text-black dark:text-white/70',
            )}
            aria-current={link.active ? 'page' : undefined}
          >
            {link.active && (
              <div className="absolute top-0 -mt-4 h-1 w-full rounded-b-lg bg-black dark:bg-white" />
            )}
            <link.icon aria-hidden="true" />
            <p className="text-xs">{link.label}</p>
          </Link>
        ))}
      </div>

      {children}
    </TopNavContainer>
  );
};

export default TopNav; 