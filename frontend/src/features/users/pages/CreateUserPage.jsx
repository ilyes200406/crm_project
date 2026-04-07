import { CreateUserForm } from '../components/CreateUserForm';

export function CreateUserPage() {
  return (
    <div className="stack">
      <h1>Create User</h1>
      <p className="muted">Admin invitation endpoint: `/api/auth/admin/create-user/`.</p>
      <CreateUserForm />
    </div>
  );
}
