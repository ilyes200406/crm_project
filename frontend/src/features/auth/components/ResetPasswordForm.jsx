import { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams, Link } from 'react-router-dom';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useAuth } from '../hooks/useAuth';

export function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get('token') ?? '', [searchParams]);
  const { resetPasswordMutation } = useAuth();

  const { register, handleSubmit, formState: { errors }, reset } = useForm({
    defaultValues: {
      new_password: '',
      new_password_confirm: '',
    },
  });

  const onSubmit = async (values) => {
    await resetPasswordMutation.mutateAsync({ token, ...values });
    reset();
  };

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Nouveau mot de passe" type="password" {...register('new_password', { required: 'Mot de passe requis' })} />
      <FieldError message={errors.new_password?.message} />
      <Input
        label="Confirmer le mot de passe"
        type="password"
        {...register('new_password_confirm', { required: 'Veuillez confirmer le mot de passe' })}
      />
      <FieldError message={errors.new_password_confirm?.message} />
      <Button type="submit" loading={resetPasswordMutation.isPending} disabled={!token}>
        Réinitialiser le mot de passe
      </Button>
      <Link to="/login" className="text-blue-600 text-sm hover:underline text-center">
        Retour à la connexion
      </Link>
    </form>
  );
}
