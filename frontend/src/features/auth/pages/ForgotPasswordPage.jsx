import { ForgotPasswordForm } from '../components/ForgotPasswordForm';

export function ForgotPasswordPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Mot de passe oublié</h1>
        <p className="text-gray-500 text-sm mt-1">Entrez votre email pour recevoir un lien de réinitialisation.</p>
      </div>
      <ForgotPasswordForm />
    </div>
  );
}
