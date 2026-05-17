import { ResetPasswordForm } from '../components/ResetPasswordForm';

export function ResetPasswordPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Réinitialisation du mot de passe</h1>
        <p className="text-gray-500 text-sm mt-1">Définissez votre nouveau mot de passe.</p>
      </div>
      <ResetPasswordForm />
    </div>
  );
}
