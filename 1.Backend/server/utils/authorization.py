# server/utils/authorization.py
"""
Phase 2: Authorization utilities for group management

Provides authorization helpers to verify:
- User is a member of a group
- User has admin role in a group
- User can perform specific operations
"""

import sys
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.client import group_members_col, groups_col, users_col
from bson import ObjectId
from typing import Optional, Dict

# ============================================================================
# AUTHORIZATION HELPERS
# ============================================================================

async def is_user_in_group(user_id: str, group_id: str) -> bool:
    """
    Check if user is an active member of the group.
    
    Args:
        user_id: User ID to check
        group_id: Group ID to check
        
    Returns:
        True if user is active member, False otherwise
    """
    try:
        member = await group_members_col.find_one({
            "group_id": group_id,
            "user_id": user_id,
            "is_active": True
        })
        return member is not None
    except Exception:
        return False

async def is_user_group_admin(user_id: str, group_id: str) -> bool:
    """
    Check if user is an admin of the group.
    
    Args:
        user_id: User ID to check
        group_id: Group ID to check
        
    Returns:
        True if user is admin, False otherwise
    """
    try:
        member = await group_members_col.find_one({
            "group_id": group_id,
            "user_id": user_id,
            "role": "admin",
            "is_active": True
        })
        return member is not None
    except Exception:
        return False

async def get_user_role_in_group(user_id: str, group_id: str) -> Optional[str]:
    """
    Get user's role in a group.
    
    Args:
        user_id: User ID
        group_id: Group ID
        
    Returns:
        "admin" or "member" if user is in group, None otherwise
    """
    try:
        member = await group_members_col.find_one({
            "group_id": group_id,
            "user_id": user_id,
            "is_active": True
        })
        return member.get("role") if member else None
    except Exception:
        return None

async def verify_group_exists(group_id: str) -> bool:
    """
    Check if group exists and is active.
    
    Args:
        group_id: Group ID to check
        
    Returns:
        True if group exists and is active, False otherwise
    """
    try:
        group = await groups_col.find_one({
            "_id": ObjectId(group_id),
            "is_active": True
        })
        return group is not None
    except Exception:
        return False

async def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Find user by email address.
    
    Args:
        email: Email address to search
        
    Returns:
        User document if found, None otherwise
    """
    try:
        user = await users_col.find_one({"email": email.lower()})
        return user
    except Exception:
        return None

async def can_user_modify_group(user_id: str, group_id: str) -> bool:
    """
    Check if user can modify group (admin or creator).
    
    Args:
        user_id: User ID to check
        group_id: Group ID
        
    Returns:
        True if user can modify group, False otherwise
    """
    try:
        # Check if user is admin
        if await is_user_group_admin(user_id, group_id):
            return True
        
        # Check if user is creator
        group = await groups_col.find_one({
            "_id": ObjectId(group_id),
            "created_by": user_id,
            "is_active": True
        })
        return group is not None
    except Exception:
        return False

async def can_user_add_members(user_id: str, group_id: str) -> bool:
    """
    Check if user can add members to group (admin only).
    
    Args:
        user_id: User ID to check
        group_id: Group ID
        
    Returns:
        True if user can add members, False otherwise
    """
    return await is_user_group_admin(user_id, group_id)

async def can_user_remove_members(user_id: str, group_id: str) -> bool:
    """
    Check if user can remove members from group (admin only).
    
    Args:
        user_id: User ID to check
        group_id: Group ID
        
    Returns:
        True if user can remove members, False otherwise
    """
    return await is_user_group_admin(user_id, group_id)

async def get_group_member_count(group_id: str) -> int:
    """
    Get count of active members in a group.
    
    Args:
        group_id: Group ID
        
    Returns:
        Number of active members
    """
    try:
        count = await group_members_col.count_documents({
            "group_id": group_id,
            "is_active": True
        })
        return count
    except Exception:
        return 0

# ============================================================================
# AUTHORIZATION DECORATORS (for future use with FastAPI)
# ============================================================================

class AuthorizationError(Exception):
    """Raised when authorization fails"""
    pass

def require_group_membership(func):
    """
    Decorator to require group membership.
    Note: For MCP tools, we'll use manual checks instead.
    """
    async def wrapper(user_id: str, group_id: str, *args, **kwargs):
        if not await is_user_in_group(user_id, group_id):
            raise AuthorizationError(f"User {user_id} is not a member of group {group_id}")
        return await func(user_id, group_id, *args, **kwargs)
    return wrapper

def require_group_admin(func):
    """
    Decorator to require group admin role.
    Note: For MCP tools, we'll use manual checks instead.
    """
    async def wrapper(user_id: str, group_id: str, *args, **kwargs):
        if not await is_user_group_admin(user_id, group_id):
            raise AuthorizationError(f"User {user_id} is not an admin of group {group_id}")
        return await func(user_id, group_id, *args, **kwargs)
    return wrapper
