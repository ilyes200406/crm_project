import { Link } from 'react-router-dom';

import { ChangePasswordForm } from '../components/ChangePasswordForm';

export function ChangePasswordPage() {
  return (
    <div className="max-w-lg space-y-6">
      <div>
        <Link to="/app/profile" className="text-sm text-gray-500 hover:text-gray-700">
          ← Retour au profil
        </Link>
      </div>
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Changer le mot de passe</h1>
        <p className="text-gray-500 text-sm mt-1">Vous serez déconnecté après la mise à jour.</p>
      </div>
      <ChangePasswordForm />
    </div>
  );
}
