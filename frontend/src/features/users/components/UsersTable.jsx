import { Button } from '../../../shared/components/Button';

export function UsersTable({ users = [], onActivate, onDeactivate }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Name</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim()}</td>
              <td>{user.role}</td>
              <td>{user.is_active ? 'Active' : 'Inactive'}</td>
              <td className="table-actions">
                {user.is_active ? (
                  <Button variant="danger" type="button" onClick={() => onDeactivate(user.id)}>
                    Deactivate
                  </Button>
                ) : (
                  <Button type="button" onClick={() => onActivate(user.id)}>
                    Activate
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
