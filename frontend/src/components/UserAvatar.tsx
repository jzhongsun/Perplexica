import { User as UserIcon } from 'lucide-react';
import { User } from '@/lib/hooks/useUser';
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
          alt={user.fullName || user.username}
          fill
          className="object-cover"
          sizes={`${size}px`}
        />
      </div>
    );
  }

  // If no avatar, show initials
  const initials = user.fullName
    ? user.fullName
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user.username.slice(0, 2).toUpperCase();

  return (
    <div
      className="flex items-center justify-center rounded-full bg-blue-500 text-white font-medium"
      style={{ width: size, height: size }}
    >
      <span style={{ fontSize: size * 0.4 }}>{initials}</span>
    </div>
  );
} 