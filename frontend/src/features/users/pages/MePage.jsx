import { Link } from 'react-router-dom';
import { User } from 'lucide-react';

import { ProfileForm } from '../components/ProfileForm';
import { useMeQuery } from '../hooks/useUsers';

export function MePage() {
  const { data: me, isLoading } = useMeQuery();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center">
          <User size={18} className="text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mon profil</h1>
          <p className="text-sm text-gray-500">Gérez vos informations personnelles.</p>
        </div>
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
