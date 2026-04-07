import { SetupAccountForm } from '../components/SetupAccountForm';

export function SetupAccountPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configuration du compte</h1>
        <p className="text-gray-500 text-sm mt-1">Complétez la configuration de votre compte depuis le lien d'invitation.</p>
      </div>
      <SetupAccountForm />
    </div>
  );
}
