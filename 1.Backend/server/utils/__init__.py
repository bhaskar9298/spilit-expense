# server/utils/__init__.py
"""
Utility modules for MCP server
"""

from .authorization import (
    is_user_in_group,
    is_user_group_admin,
    get_user_role_in_group,
    verify_group_exists,
    get_user_by_email,
    can_user_modify_group,
    can_user_add_members,
    can_user_remove_members,
    get_group_member_count,
    AuthorizationError
)

__all__ = [
    'is_user_in_group',
    'is_user_group_admin',
    'get_user_role_in_group',
    'verify_group_exists',
    'get_user_by_email',
    'can_user_modify_group',
    'can_user_add_members',
    'can_user_remove_members',
    'get_group_member_count',
    'AuthorizationError'
]
