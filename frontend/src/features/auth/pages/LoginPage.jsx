import { LoginForm } from '../components/LoginForm';

export function LoginPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Connexion</h1>
        <p className="text-gray-500 text-sm mt-1">Utilisez vos identifiants professionnels.</p>
      </div>
      <LoginForm />
    </div>
  );
}
