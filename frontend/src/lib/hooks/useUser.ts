import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export interface User {
  id: string;
  email: string;
  username: string;
  fullName?: string;
  avatar?: string;  // URL to user's avatar image
  isActive: boolean;
  isSuperuser: boolean;
  createdAt: string;
  updatedAt: string;
}

export function useUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function loadUser() {
      try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Failed to load user:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, []);

  const logout = async () => {
    try {
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
      });

      if (response.ok) {
        // Clear user state
        setUser(null);
        // Redirect to home page
        router.push('/');
        // Force reload to clear all state
        window.location.reload();
      } else {
        throw new Error('Logout failed');
      }
    } catch (error) {
      console.error('Failed to logout:', error);
    }
  };

  return {
    user,
    loading,
    logout,
    isAuthenticated: !!user,
  };
} 