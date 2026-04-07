import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { usersApi } from '../api/usersApi';

export function useMeQuery() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const { data } = await usersApi.me();
      return data;
    },
  });
}

export function useUpdateMeMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersApi.updateMe,
    onSuccess: ({ data }) => {
      queryClient.setQueryData(['me'], data);
      toast.success('Profile updated successfully.');
    },
  });
}

export function useUsersQuery(params) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: async () => {
      const { data } = await usersApi.listUsers(params);
      return data;
    },
  });
}

export function useCreateUserMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
      toast.success('User created and invitation sent.');
    },
  });
}

export function useDeactivateUserMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersApi.deactivateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
      toast.success('User deactivated.');
    },
  });
}

export function useActivateUserMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersApi.activateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['user-stats'] });
      toast.success('User activated.');
    },
  });
}

export function useUserStatsQuery() {
  return useQuery({
    queryKey: ['user-stats'],
    queryFn: async () => {
      const { data } = await usersApi.userStats();
      return data;
    },
  });
}
