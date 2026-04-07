import { useEffect } from 'react';

import { useAppStore } from '../../../app/store';
import { authApi } from '../api/authApi';
import { usersApi } from '../../users/api/usersApi';

export function useInitializeAuth() {
  const isBootstrapped = useAppStore((state) => state.isBootstrapped);
  const refreshToken = useAppStore((state) => state.refreshToken);
  const setSession = useAppStore((state) => state.setSession);
  const clearSession = useAppStore((state) => state.clearSession);
  const markBootstrapped = useAppStore((state) => state.markBootstrapped);

  useEffect(() => {
    if (isBootstrapped) {
      return;
    }

    let mounted = true;

    const bootstrap = async () => {
      try {
        const { data } = await authApi.refresh(refreshToken);
        const meResponse = await usersApi.me();

        if (!mounted) return;

        setSession({
          user: meResponse.data,
          accessToken: data.access,
          refreshToken: data.refresh,
        });
      } catch {
        if (!mounted) return;
        clearSession();
      } finally {
        if (mounted) {
          markBootstrapped();
        }
      }
    };

    bootstrap();

    return () => {
      mounted = false;
    };
  }, [isBootstrapped, refreshToken, setSession, clearSession, markBootstrapped]);
}
