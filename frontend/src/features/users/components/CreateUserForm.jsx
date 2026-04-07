import { useForm } from 'react-hook-form';

import { Button } from '../../../shared/components/Button';
import { FieldError } from '../../../shared/components/FieldError';
import { Input } from '../../../shared/components/Input';
import { useCreateUserMutation } from '../hooks/useUsers';

export function CreateUserForm() {
  const createUserMutation = useCreateUserMutation();
  const { register, handleSubmit, formState: { errors }, reset } = useForm({
    defaultValues: {
      email: '',
      first_name: '',
      last_name: '',
      role: 'COMMERCIAL',
    },
  });

  const onSubmit = async (values) => {
    await createUserMutation.mutateAsync(values);
    reset();
  };

  return (
    <form className="stack" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Email" type="email" {...register('email', { required: 'Email is required' })} />
      <FieldError message={errors.email?.message} />

      <Input label="First name" {...register('first_name')} />
      <Input label="Last name" {...register('last_name')} />

      <label className="field">
        <span className="label">Role</span>
        <select className="input" {...register('role')}>
          <option value="ADMIN">ADMIN</option>
          <option value="COMMERCIAL">COMMERCIAL</option>
          <option value="TECHNICIEN">TECHNICIEN</option>
          <option value="FINANCE">FINANCE</option>
        </select>
      </label>

      <Button type="submit" loading={createUserMutation.isPending}>
        Create User
      </Button>
    </form>
  );
}
