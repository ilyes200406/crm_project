import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { useAppStore } from '../../../app/store';
import { authApi } from '../api/authApi';
import { usersApi } from '../../users/api/usersApi';

export function useAuth() {
  const user = useAppStore((state) => state.user);
  const refreshToken = useAppStore((state) => state.refreshToken);
  const setSession = useAppStore((state) => state.setSession);
  const clearSession = useAppStore((state) => state.clearSession);

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async ({ data }) => {
      const accessToken = data?.tokens?.access;
      const nextRefreshToken = data?.tokens?.refresh;
      const userFromBody = data?.user;

      let nextUser = userFromBody;
      if (!nextUser) {
        const meResponse = await usersApi.me();
        nextUser = meResponse.data;
      }

      setSession({
        user: nextUser,
        accessToken,
        refreshToken: nextRefreshToken,
      });
      toast.success('Login successful.');
    },
  });

  const setupMutation = useMutation({
    mutationFn: authApi.setupAccount,
    onSuccess: ({ data }) => {
      setSession({
        user: data.user,
        accessToken: data.tokens?.access,
        refreshToken: data.tokens?.refresh,
      });
      toast.success('Account setup completed.');
    },
  });

  const forgotPasswordMutation = useMutation({
    mutationFn: authApi.forgotPassword,
    onSuccess: () => {
      toast.success('If the email exists, a reset link was sent.');
    },
  });

  const resetPasswordMutation = useMutation({
    mutationFn: authApi.resetPassword,
    onSuccess: () => {
      toast.success('Password reset completed. You can now sign in.');
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => {
      toast.success('Password changed successfully.');
    },
  });

  const logout = async () => {
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Ignore server-side logout failures and clear local session.
    } finally {
      clearSession();
    }
  };

  return {
    user,
    loginMutation,
    setupMutation,
    forgotPasswordMutation,
    resetPasswordMutation,
    changePasswordMutation,
    logout,
  };
}
