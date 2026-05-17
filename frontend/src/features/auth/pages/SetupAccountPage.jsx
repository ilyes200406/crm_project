import { SetupAccountForm } from '../components/SetupAccountForm';

export function SetupAccountPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Configuration du compte</h1>
        <p className="text-gray-500 text-sm mt-1">Complétez la configuration depuis votre lien d'invitation.</p>
      </div>
      <SetupAccountForm />
    </div>
  );
}
