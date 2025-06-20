import { User as UserIcon } from 'lucide-react';
import type { User } from '@/lib/api/types';
import Image from 'next/image';

interface UserAvatarProps {
  user: User | null;
  size?: number;
}

export function UserAvatar({ user, size = 32 }: UserAvatarProps) {
  if (!user) {
    return (
      <div
        className="flex items-center justify-center rounded-full bg-black/5 dark:bg-white/5"
        style={{ width: size, height: size }}
      >
        <UserIcon size={size * 0.6} className="text-black/70 dark:text-white/70" />
      </div>
    );
  }

  // If user has an avatar, display it
  if (user.avatar) {
    return (
      <div
        className="relative rounded-full overflow-hidden"
        style={{ width: size, height: size }}
      >
        <Image
          src={user.avatar}
          alt={user.name || 'User'}
          fill
          className="object-cover"
          sizes={`${size}px`}
        />
      </div>
    );
  }

  // If no avatar and no name, show first letter of email or default
  if (!user.name) {
    const initial = user.email ? user.email[0].toUpperCase() : 'U';
    return (
      <div
        className="flex items-center justify-center rounded-full bg-blue-500 text-white font-medium"
        style={{ width: size, height: size }}
      >
        <span style={{ fontSize: size * 0.4 }}>{initial}</span>
      </div>
    );
  }

  // If no avatar but has name, show name initials
  const initials = user.name
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className="flex items-center justify-center rounded-full bg-blue-500 text-white font-medium"
      style={{ width: size, height: size }}
    >
      <span style={{ fontSize: size * 0.4 }}>{initials}</span>
    </div>
  );
} 