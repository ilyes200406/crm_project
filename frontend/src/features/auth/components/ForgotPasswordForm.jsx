import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { Mail, AlertCircle, MailCheck } from 'lucide-react';

import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { FieldError } from '../../../shared/components/FieldError';
import { useAuth } from '../hooks/useAuth';

export function ForgotPasswordForm() {
  const { forgotPasswordMutation } = useAuth();
  const [sent, setSent] = useState(false);
  const [apiError, setApiError] = useState(null);

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { email: '' },
  });

  const onSubmit = async (values) => {
    setApiError(null);
    try {
      await forgotPasswordMutation.mutateAsync(values);
      setSent(true);
    } catch (error) {
      const data = error?.response?.data;
      if (!data) { setApiError('Une erreur est survenue. Veuillez réessayer.'); return; }
      for (const [, msgs] of Object.entries(data)) {
        const msg = Array.isArray(msgs) ? msgs[0] : msgs;
        setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        break;
      }
    }
  };

  if (sent) {
    return (
      <div className="flex flex-col items-center gap-4 py-4 text-center">
        <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center">
          <MailCheck size={24} className="text-green-600" />
        </div>
        <div>
          <p className="font-semibold text-gray-900 mb-1">Email envoyé</p>
          <p className="text-gray-500 text-sm">
            Si cet email existe dans notre système, un lien de réinitialisation vous a été envoyé.
          </p>
        </div>
        <Link to="/login" className="text-sm text-blue-600 hover:underline">
          Retour à la connexion
        </Link>
      </div>
    );
  }

  return (
    <form className="flex flex-col gap-5" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1">
        <Input
          label="Adresse e-mail"
          type="email"
          autoComplete="email"
          icon={Mail}
          error={!!errors.email}
          {...register('email', { required: "L'adresse e-mail est requise." })}
        />
        <FieldError message={errors.email?.message} />
      </div>

      {apiError && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={15} className="shrink-0 mt-0.5" />
          <span>{apiError}</span>
        </div>
      )}

      <Button type="submit" loading={forgotPasswordMutation.isPending}>
        Envoyer le lien
      </Button>

      <Link to="/login" className="text-sm text-blue-600 hover:underline text-center">
        Retour à la connexion
      </Link>
    </form>
  );
}
