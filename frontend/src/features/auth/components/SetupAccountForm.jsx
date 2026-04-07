import { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useAuth } from '../hooks/useAuth';

export function SetupAccountForm() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = useMemo(() => searchParams.get('token') ?? '', [searchParams]);
  const { setupMutation } = useAuth();

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      first_name: '',
      last_name: '',
      password: '',
      password_confirm: '',
    },
  });

  const onSubmit = async (values) => {
    await setupMutation.mutateAsync({ token, ...values });
    navigate('/app', { replace: true });
  };

  return (
    <form className="stack" onSubmit={handleSubmit(onSubmit)}>
      <Input label="First Name" {...register('first_name')} />
      <Input label="Last Name" {...register('last_name')} />
      <Input label="Password" type="password" {...register('password', { required: 'Password is required' })} />
      <FieldError message={errors.password?.message} />
      <Input
        label="Confirm Password"
        type="password"
        {...register('password_confirm', { required: 'Please confirm your password' })}
      />
      <FieldError message={errors.password_confirm?.message} />
      <Button type="submit" loading={setupMutation.isPending} disabled={!token}>
        Complete Setup
      </Button>
    </form>
  );
}
