import { Link } from 'react-router-dom';

import { ProfileForm } from '../components/ProfileForm';
import { useMeQuery } from '../hooks/useUsers';

export function MePage() {
  const { data: me, isLoading } = useMeQuery();

  if (isLoading) {
    return <p>Loading profile...</p>;
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Mon profil</h1>
        <p className="text-gray-500 text-sm mt-1">Gérez vos informations personnelles.</p>
      </div>

      <ProfileForm
        defaultValues={{
          first_name: me?.first_name || '',
          last_name: me?.last_name || '',
          email: me?.email || '',
        }}
      />

      <hr className="border-gray-200" />

      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-gray-900">Mot de passe</div>
          <div className="text-xs text-gray-500">Modifiez votre mot de passe de connexion.</div>
        </div>
        <Link
          to="/app/change-password"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Changer le mot de passe
        </Link>
      </div>
    </div>
  );
}
