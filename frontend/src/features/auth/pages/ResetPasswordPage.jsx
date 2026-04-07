import { ResetPasswordForm } from '../components/ResetPasswordForm';

export function ResetPasswordPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Réinitialisation du mot de passe</h1>
        <p className="text-gray-500 text-sm mt-1">Utilisez le lien reçu par email.</p>
      </div>
      <ResetPasswordForm />
    </div>
  );
}
