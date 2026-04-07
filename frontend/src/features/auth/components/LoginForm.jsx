import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { FieldError } from '../../../shared/components/FieldError';
import { useAuth } from '../hooks/useAuth';

export function LoginForm() {
  const navigate = useNavigate();
  const { loginMutation } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values) => {
    await loginMutation.mutateAsync(values);
    navigate('/app', { replace: true });
  };

  return (
    <form className="stack" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Email" type="email" autoComplete="email" {...register('email', { required: 'Email is required' })} />
      <FieldError message={errors.email?.message} />

      <Input
        label="Password"
        type="password"
        autoComplete="current-password"
        {...register('password', { required: 'Password is required' })}
      />
      <FieldError message={errors.password?.message} />

      <Button type="submit" loading={loginMutation.isPending}>
        Sign In
      </Button>
      <Link to="/forgot-password" className="text-sm text-blue-600 hover:underline text-center">
        Mot de passe oublié ?
      </Link>
    </form>
  );
}
