import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { User, Mail, AlertCircle } from 'lucide-react';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useUpdateMeMutation } from '../hooks/useUsers';

export function ProfileForm({ defaultValues }) {
  const updateMeMutation = useUpdateMeMutation();
  const [apiError, setApiError] = useState(null);

  const { register, handleSubmit, setError, formState: { errors } } = useForm({ defaultValues });

  const FIELDS = ['first_name', 'last_name', 'email'];

  const onSubmit = async (values) => {
    setApiError(null);
    try {
      await updateMeMutation.mutateAsync(values);
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

  return (
    <form className="flex flex-col gap-5" onSubmit={handleSubmit(onSubmit)}>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <Input
            label="Prénom"
            icon={User}
            error={!!errors.first_name}
            {...register('first_name')}
          />
          <FieldError message={errors.first_name?.message} />
        </div>
        <div className="flex flex-col gap-1">
          <Input
            label="Nom"
            icon={User}
            error={!!errors.last_name}
            {...register('last_name')}
          />
          <FieldError message={errors.last_name?.message} />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <Input
          label="Adresse e-mail"
          type="email"
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

      <Button type="submit" loading={updateMeMutation.isPending}>
        Sauvegarder
      </Button>
    </form>
  );
}
