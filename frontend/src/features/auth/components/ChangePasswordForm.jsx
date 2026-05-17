import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Lock, Eye, EyeOff, AlertCircle } from 'lucide-react';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { useAuth } from '../hooks/useAuth';

export function ChangePasswordForm() {
  const { changePasswordMutation, logout } = useAuth();
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [apiError, setApiError] = useState(null);

  const { register, handleSubmit, setError, reset, formState: { errors } } = useForm({
    defaultValues: { old_password: '', new_password: '', new_password_confirm: '' },
  });

  const FIELDS = ['old_password', 'new_password', 'new_password_confirm'];

  const onSubmit = async (values) => {
    setApiError(null);
    try {
      await changePasswordMutation.mutateAsync(values);
      reset();
      await logout();
    } catch (error) {
      const data = error?.response?.data;
      if (!data) { setApiError('Une erreur est survenue. Veuillez réessayer.'); return; }
      for (const [field, msgs] of Object.entries(data)) {
        const msg = Array.isArray(msgs) ? msgs[0] : msgs;
        if (field === 'non_field_errors' || field === 'detail') {
          setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        } else if (FIELDS.includes(field)) {
          setError(field, { message: typeof msg === 'string' ? msg : String(msg) });
        } else {
          setApiError(typeof msg === 'string' ? msg : 'Une erreur est survenue.');
        }
      }
    }
  };

  const passwordField = (id, label, showState, setShowState, registerName, requiredMsg) => (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-semibold text-gray-700" htmlFor={id}>{label}</label>
      <div className="relative">
        <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
        <input
          id={id}
          type={showState ? 'text' : 'password'}
          autoComplete={id === 'old_password' ? 'current-password' : 'new-password'}
          className={`border ${errors[registerName] ? 'border-red-400 focus:ring-red-400' : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400'} rounded-lg pl-9 pr-10 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors`}
          {...register(registerName, { required: requiredMsg })}
        />
        <button type="button" tabIndex={-1}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
          onClick={() => setShowState((v) => !v)}>
          {showState ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
      </div>
      <FieldError message={errors[registerName]?.message} />
    </div>
  );

  return (
    <form className="flex flex-col gap-5" onSubmit={handleSubmit(onSubmit)}>
      {passwordField('old_password', 'Mot de passe actuel', showOld, setShowOld, 'old_password', 'Le mot de passe actuel est requis.')}
      {passwordField('new_password', 'Nouveau mot de passe', showNew, setShowNew, 'new_password', 'Le nouveau mot de passe est requis.')}
      {passwordField('new_password_confirm', 'Confirmer le nouveau mot de passe', showConfirm, setShowConfirm, 'new_password_confirm', 'Veuillez confirmer le mot de passe.')}

      {apiError && (
        <div className="flex items-start gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle size={15} className="shrink-0 mt-0.5" />
          <span>{apiError}</span>
        </div>
      )}

      <Button type="submit" loading={changePasswordMutation.isPending}>
        Mettre à jour
      </Button>
    </form>
  );
}
