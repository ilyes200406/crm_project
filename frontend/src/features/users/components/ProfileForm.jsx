import { useForm } from 'react-hook-form';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useUpdateMeMutation } from '../hooks/useUsers';

export function ProfileForm({ defaultValues }) {
  const updateMeMutation = useUpdateMeMutation();
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues,
  });

  const onSubmit = async (values) => {
    await updateMeMutation.mutateAsync(values);
  };

  return (
    <form className="stack" onSubmit={handleSubmit(onSubmit)}>
      <Input label="First name" {...register('first_name')} />
      <Input label="Last name" {...register('last_name')} />
      <Input label="Email" type="email" {...register('email', { required: 'Email is required' })} />
      <FieldError message={errors.email?.message} />
      <Button type="submit" loading={updateMeMutation.isPending}>
        Save Changes
      </Button>
    </form>
  );
}
