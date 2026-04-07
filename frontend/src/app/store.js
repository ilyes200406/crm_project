import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAppStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isBootstrapped: false,

      setSession: ({ user, accessToken, refreshToken }) => {
        set({
          user,
          accessToken,
          refreshToken: refreshToken ?? get().refreshToken,
        });
      },

      setAccessToken: (accessToken) => set({ accessToken }),

      setRefreshToken: (refreshToken) => set({ refreshToken }),

      clearSession: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
        }),

      markBootstrapped: () => set({ isBootstrapped: true }),

      isAuthenticated: () => Boolean(get().user && get().accessToken),

      hasRole: (roles) => {
        const currentUser = get().user;
        if (!currentUser) return false;
        if (!roles || roles.length === 0) return true;
        return roles.includes(currentUser.role);
      },
    }),
    {
      name: 'crm-session', // localStorage key
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        // isBootstrapped intentionally excluded — must reset to false on every page load
      }),
    }
  )
);
