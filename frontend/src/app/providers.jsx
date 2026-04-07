import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

import { queryClient } from '../services/queryClient';
import { useInitializeAuth } from '../features/auth/hooks/useInitializeAuth';

function AuthBootstrap({ children }) {
  useInitializeAuth();
  return children;
}

export function AppProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap>{children}</AuthBootstrap>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}
