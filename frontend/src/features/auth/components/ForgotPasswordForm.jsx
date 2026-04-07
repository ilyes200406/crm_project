import { useForm } from 'react-hook-form';

import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { FieldError } from '../../../shared/components/FieldError';
import { useAuth } from '../hooks/useAuth';

export function ForgotPasswordForm() {
  const { forgotPasswordMutation } = useAuth();
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (values) => {
    await forgotPasswordMutation.mutateAsync(values);
  };

  return (
    <form className="stack" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Email" type="email" {...register('email', { required: 'Email is required' })} />
      <FieldError message={errors.email?.message} />
      <Button type="submit" loading={forgotPasswordMutation.isPending}>
        Send Reset Link
      </Button>
    </form>
  );
}
