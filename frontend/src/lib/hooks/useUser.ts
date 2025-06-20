import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { User } from '@/lib/api';

export function useUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function loadUser() {
      try {
        const userData = await api.auth.getMe();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const userData = await api.auth.login(email, password);
      setUser(userData);
      router.push('/');
    } catch (error) {
      console.error('Failed to login:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.auth.logout();
      setUser(null);
      router.push('/');
    } catch (error) {
      console.error('Failed to logout:', error);
      throw error;
    }
  };

  const register = async (data: { email: string; password: string; name: string }) => {
    try {
      const userData = await api.auth.register(data);
      setUser(userData);
      router.push('/');
    } catch (error) {
      console.error('Failed to register:', error);
      throw error;
    }
  };

  return {
    user,
    loading,
    login,
    logout,
    register,
    isAuthenticated: !!user,
  };
} 