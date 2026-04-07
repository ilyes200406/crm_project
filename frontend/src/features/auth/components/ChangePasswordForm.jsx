import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useAuth } from '../hooks/useAuth';

export function ChangePasswordForm() {
  const { changePasswordMutation, logout } = useAuth();
  const { register, handleSubmit, formState: { errors }, reset, setError } = useForm({
    defaultValues: {
      old_password: '',
      new_password: '',
      new_password_confirm: '',
    },
  });

  const onSubmit = async (values) => {
    try {
      await changePasswordMutation.mutateAsync(values);
      reset();
      await logout();
    } catch (error) {
      const data = error?.response?.data;
      if (data && typeof data === 'object') {
        const fieldNames = ['old_password', 'new_password', 'new_password_confirm'];
        let hasFieldError = false;
        Object.entries(data).forEach(([field, messages]) => {
          const message = Array.isArray(messages) ? messages[0] : messages;
          if (fieldNames.includes(field)) {
            setError(field, { message });
            hasFieldError = true;
          }
        });
        if (!hasFieldError) {
          const fallback = Object.values(data).flat()[0];
          toast.error(typeof fallback === 'string' ? fallback : 'Erreur lors du changement de mot de passe.');
        }
      } else {
        toast.error('Erreur lors du changement de mot de passe.');
      }
    }
  };

  return (
    <form className="stack" onSubmit={handleSubmit(onSubmit)}>
      <Input
        label="Current Password"
        type="password"
        autoComplete="current-password"
        {...register('old_password', { required: 'Current password is required' })}
      />
      <FieldError message={errors.old_password?.message} />

      <Input
        label="New Password"
        type="password"
        autoComplete="new-password"
        {...register('new_password', { required: 'New password is required' })}
      />
      <FieldError message={errors.new_password?.message} />

      <Input
        label="Confirm New Password"
        type="password"
        autoComplete="new-password"
        {...register('new_password_confirm', { required: 'Please confirm the new password' })}
      />
      <FieldError message={errors.new_password_confirm?.message} />

      <Button type="submit" loading={changePasswordMutation.isPending}>
        Update Password
      </Button>
    </form>
  );
}
