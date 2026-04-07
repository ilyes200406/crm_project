import { useState } from 'react';

import { Input } from '../../../shared/components/Input';
import {
  useActivateUserMutation,
  useDeactivateUserMutation,
  useUsersQuery,
} from '../hooks/useUsers';
import { UsersTable } from '../components/UsersTable';

export function UsersListPage() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useUsersQuery(search ? { search } : undefined);
  const deactivateMutation = useDeactivateUserMutation();
  const activateMutation = useActivateUserMutation();

  const results = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [];

  return (
    <div className="stack">
      <h1>Users</h1>
      <Input label="Search users" value={search} onChange={(event) => setSearch(event.target.value)} />

      {isLoading ? (
        <p>Loading users...</p>
      ) : (
        <UsersTable
          users={results}
          onDeactivate={(id) => deactivateMutation.mutate(id)}
          onActivate={(id) => activateMutation.mutate(id)}
        />
      )}
    </div>
  );
}
