"""
authentication/permissions.py — Backward-compatibility shim.

All RBAC logic has moved to users/permissions.py (where the User model
and Permission models live).  This file re-exports the symbols that the
rest of the codebase imported from here so no other import needs to change.

If you need a new permission class, add it to users/permissions.py, NOT here.
"""

from ..users.permissions import (   # noqa: F401
    IsAdmin,
    is_admin,
    is_commercial,
    is_technicien,
    is_finance,
)
