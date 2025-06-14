'use client';

import { cn } from '@/lib/utils';
import { BookOpenText, Home, Search, SquarePen, Settings } from 'lucide-react';
import Link from 'next/link';
import { useSelectedLayoutSegments } from 'next/navigation';
import React, { type ReactNode } from 'react';
import Layout from './Layout';

const HorizontalNavContainer = ({ children }: { children: ReactNode }) => {
  return (
    <div className="flex flex-row items-center gap-x-6">{children}</div>
  );
};

const TopNav = ({ children }: { children: React.ReactNode }) => {
  const segments = useSelectedLayoutSegments();

  const navLinks = [
    {
      icon: Home,
      href: '/',
      active: segments.length === 0 || segments.includes('c'),
      label: 'Home',
    },
    {
      icon: Search,
      href: '/discover',
      active: segments.includes('discover'),
      label: 'Discover',
    },
    {
      icon: BookOpenText,
      href: '/library',
      active: segments.includes('library'),
      label: 'Library',
    },
  ];

  return (
    <div>
      {/* Desktop Navigation */}
      <div className="hidden md:fixed md:top-0 md:left-0 md:right-0 md:z-50 md:flex md:flex-row">
        <div className="w-full h-12 flex flex-row items-center justify-between px-4 bg-transparent backdrop-blur-sm border-b border-black/5 dark:border-white/5">
          <Link href="/">
            <SquarePen className="cursor-pointer w-5 h-5" />
          </Link>

          <div className="flex items-center gap-x-6">
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
                >
                  <link.icon size={18} />
                  <span className="text-sm">{link.label}</span>
                  {link.active && (
                    <div className="absolute bottom-0 left-0 h-0.5 w-full rounded-t-lg bg-black dark:bg-white" />
                  )}
                </Link>
              ))}
            </HorizontalNavContainer>

            <span className="text-black/30 dark:text-white/30">|</span>
            <Link
              href="/settings"
              className={cn(
                'p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg transition duration-150',
                segments.includes('settings')
                  ? 'text-black dark:text-white'
                  : 'text-black/70 dark:text-white/70'
              )}
            >
              <Settings className="cursor-pointer w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>

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
          >
            {link.active && (
              <div className="absolute top-0 -mt-4 h-1 w-full rounded-b-lg bg-black dark:bg-white" />
            )}
            <link.icon />
            <p className="text-xs">{link.label}</p>
          </Link>
        ))}
      </div>

      <Layout>{children}</Layout>
    </div>
  );
};

export default TopNav;
