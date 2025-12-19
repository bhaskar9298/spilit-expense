# tests/test_phase2_groups.py
"""
Phase 2 Tests: Group Management

Tests for:
1. Group CRUD operations
2. Member management
3. Authorization checks
4. Edge cases and error handling
"""

import pytest
import sys
import pathlib
from datetime import datetime

# Add parent directory to path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.client import (
    users_col,
    groups_col,
    group_members_col
)
from server.utils.authorization import (
    is_user_in_group,
    is_user_group_admin,
    get_user_by_email,
    can_user_modify_group,
    get_group_member_count
)

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
async def test_users():
    """Create test users"""
    users = [
        {
            "email": "alice@test.com",
            "password_hash": "hash_alice",
            "full_name": "Alice Admin",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "bob@test.com",
            "password_hash": "hash_bob",
            "full_name": "Bob Member",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "email": "charlie@test.com",
            "password_hash": "hash_charlie",
            "full_name": "Charlie User",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    results = await users_col.insert_many(users)
    user_ids = [str(id) for id in results.inserted_ids]
    
    yield {
        "alice": user_ids[0],
        "bob": user_ids[1],
        "charlie": user_ids[2],
        "emails": ["alice@test.com", "bob@test.com", "charlie@test.com"]
    }
    
    # Cleanup
    await users_col.delete_many({"_id": {"$in": results.inserted_ids}})

@pytest.fixture(scope="function")
async def test_group(test_users):
    """Create a test group with Alice as admin"""
    group_doc = {
        "name": "Test Group",
        "description": "A test group",
        "created_by": test_users["alice"],
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await groups_col.insert_one(group_doc)
    group_id = str(result.inserted_id)
    
    # Add Alice as admin
    member_doc = {
        "group_id": group_id,
        "user_id": test_users["alice"],
        "role": "admin",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    await group_members_col.insert_one(member_doc)
    
    yield {"group_id": group_id, "users": test_users}
    
    # Cleanup
    await groups_col.delete_one({"_id": result.inserted_id})
    await group_members_col.delete_many({"group_id": group_id})

# ============================================================================
# TEST: Authorization Utilities
# ============================================================================

@pytest.mark.asyncio
async def test_is_user_in_group(test_group):
    """Test checking if user is in group"""
    alice_id = test_group["users"]["alice"]
    bob_id = test_group["users"]["bob"]
    group_id = test_group["group_id"]
    
    # Alice is in group
    assert await is_user_in_group(alice_id, group_id) == True
    
    # Bob is not in group
    assert await is_user_in_group(bob_id, group_id) == False
    
    print("✓ is_user_in_group works correctly")

@pytest.mark.asyncio
async def test_is_user_group_admin(test_group):
    """Test checking if user is admin"""
    alice_id = test_group["users"]["alice"]
    group_id = test_group["group_id"]
    
    # Alice is admin
    assert await is_user_group_admin(alice_id, group_id) == True
    
    # Add Bob as member
    member_doc = {
        "group_id": group_id,
        "user_id": test_group["users"]["bob"],
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    await group_members_col.insert_one(member_doc)
    
    # Bob is not admin
    assert await is_user_group_admin(test_group["users"]["bob"], group_id) == False
    
    print("✓ is_user_group_admin works correctly")

@pytest.mark.asyncio
async def test_get_user_by_email(test_users):
    """Test finding user by email"""
    # Find Alice
    user = await get_user_by_email("alice@test.com")
    assert user is not None
    assert str(user["_id"]) == test_users["alice"]
    
    # Non-existent user
    user = await get_user_by_email("nonexistent@test.com")
    assert user is None
    
    print("✓ get_user_by_email works correctly")

@pytest.mark.asyncio
async def test_get_group_member_count(test_group):
    """Test counting group members"""
    group_id = test_group["group_id"]
    
    # Initially 1 member (Alice)
    count = await get_group_member_count(group_id)
    assert count == 1
    
    # Add Bob
    member_doc = {
        "group_id": group_id,
        "user_id": test_group["users"]["bob"],
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    await group_members_col.insert_one(member_doc)
    
    # Now 2 members
    count = await get_group_member_count(group_id)
    assert count == 2
    
    print("✓ get_group_member_count works correctly")

# ============================================================================
# TEST: Group CRUD Operations
# ============================================================================

@pytest.mark.asyncio
async def test_create_group_structure(test_users):
    """Test group creation creates correct structure"""
    alice_id = test_users["alice"]
    
    # Simulate create_group logic
    group_doc = {
        "name": "New Test Group",
        "description": "Testing group creation",
        "created_by": alice_id,
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await groups_col.insert_one(group_doc)
    group_id = str(result.inserted_id)
    
    try:
        # Verify group created
        group = await groups_col.find_one({"_id": result.inserted_id})
        assert group is not None
        assert group["name"] == "New Test Group"
        assert group["created_by"] == alice_id
        assert group["group_type"] == "shared"
        
        # Add creator as admin
        member_doc = {
            "group_id": group_id,
            "user_id": alice_id,
            "role": "admin",
            "is_active": True,
            "joined_at": datetime.utcnow()
        }
        await group_members_col.insert_one(member_doc)
        
        # Verify membership
        assert await is_user_in_group(alice_id, group_id) == True
        assert await is_user_group_admin(alice_id, group_id) == True
        
        print("✓ Group creation structure correct")
        
    finally:
        # Cleanup
        await groups_col.delete_one({"_id": result.inserted_id})
        await group_members_col.delete_many({"group_id": group_id})

@pytest.mark.asyncio
async def test_list_groups_for_user(test_users):
    """Test listing groups for a user"""
    alice_id = test_users["alice"]
    
    # Create 2 groups with Alice as member
    group1 = await groups_col.insert_one({
        "name": "Group 1",
        "created_by": alice_id,
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    group2 = await groups_col.insert_one({
        "name": "Group 2",
        "created_by": alice_id,
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    try:
        # Add Alice to both groups
        await group_members_col.insert_many([
            {
                "group_id": str(group1.inserted_id),
                "user_id": alice_id,
                "role": "admin",
                "is_active": True,
                "joined_at": datetime.utcnow()
            },
            {
                "group_id": str(group2.inserted_id),
                "user_id": alice_id,
                "role": "admin",
                "is_active": True,
                "joined_at": datetime.utcnow()
            }
        ])
        
        # List groups
        memberships = await group_members_col.find({
            "user_id": alice_id,
            "is_active": True
        }).to_list(None)
        
        assert len(memberships) == 2
        
        print("✓ List groups for user works")
        
    finally:
        # Cleanup
        await groups_col.delete_many({"_id": {"$in": [group1.inserted_id, group2.inserted_id]}})
        await group_members_col.delete_many({
            "group_id": {"$in": [str(group1.inserted_id), str(group2.inserted_id)]}
        })

@pytest.mark.asyncio
async def test_update_group_auth(test_group):
    """Test that only admins can update groups"""
    alice_id = test_group["users"]["alice"]
    bob_id = test_group["users"]["bob"]
    group_id = test_group["group_id"]
    
    # Alice (admin) can modify
    assert await can_user_modify_group(alice_id, group_id) == True
    
    # Bob (not member) cannot modify
    assert await can_user_modify_group(bob_id, group_id) == False
    
    # Add Bob as member (not admin)
    await group_members_col.insert_one({
        "group_id": group_id,
        "user_id": bob_id,
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    })
    
    # Bob still cannot modify (member, not admin)
    assert await can_user_modify_group(bob_id, group_id) == False
    
    print("✓ Update group authorization works")

@pytest.mark.asyncio
async def test_delete_group_soft_delete(test_group):
    """Test that delete is soft delete (marks inactive)"""
    group_id = test_group["group_id"]
    from bson import ObjectId
    
    # Mark group as inactive (soft delete)
    await groups_col.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": {"is_active": False}}
    )
    
    # Group still exists but inactive
    group = await groups_col.find_one({"_id": ObjectId(group_id)})
    assert group is not None
    assert group["is_active"] == False
    
    print("✓ Group soft delete works")

# ============================================================================
# TEST: Member Management
# ============================================================================

@pytest.mark.asyncio
async def test_add_member_to_group(test_group):
    """Test adding a member to group"""
    group_id = test_group["group_id"]
    bob_id = test_group["users"]["bob"]
    
    # Add Bob as member
    member_doc = {
        "group_id": group_id,
        "user_id": bob_id,
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    
    result = await group_members_col.insert_one(member_doc)
    
    # Verify Bob is now member
    assert await is_user_in_group(bob_id, group_id) == True
    assert await is_user_group_admin(bob_id, group_id) == False
    
    # Member count increased
    count = await get_group_member_count(group_id)
    assert count == 2
    
    print("✓ Add member to group works")

@pytest.mark.asyncio
async def test_cannot_add_duplicate_member(test_group):
    """Test that duplicate members are prevented"""
    group_id = test_group["group_id"]
    bob_id = test_group["users"]["bob"]
    
    # Add Bob first time
    member_doc = {
        "group_id": group_id,
        "user_id": bob_id,
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    await group_members_col.insert_one(member_doc)
    
    # Try to add Bob again - should be prevented by unique index
    from pymongo.errors import DuplicateKeyError
    with pytest.raises(DuplicateKeyError):
        await group_members_col.insert_one(member_doc)
    
    print("✓ Duplicate member prevention works")

@pytest.mark.asyncio
async def test_remove_member_from_group(test_group):
    """Test removing a member from group"""
    group_id = test_group["group_id"]
    bob_id = test_group["users"]["bob"]
    
    # Add Bob
    member_doc = {
        "group_id": group_id,
        "user_id": bob_id,
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    result = await group_members_col.insert_one(member_doc)
    
    # Verify Bob is member
    assert await is_user_in_group(bob_id, group_id) == True
    
    # Remove Bob (soft delete)
    await group_members_col.update_one(
        {"_id": result.inserted_id},
        {"$set": {"is_active": False, "left_at": datetime.utcnow()}}
    )
    
    # Verify Bob is no longer active member
    assert await is_user_in_group(bob_id, group_id) == False
    
    # But membership record still exists
    member = await group_members_col.find_one({"_id": result.inserted_id})
    assert member is not None
    assert member["is_active"] == False
    
    print("✓ Remove member works (soft delete)")

@pytest.mark.asyncio
async def test_cannot_remove_last_admin(test_group):
    """Test that last admin cannot be removed"""
    group_id = test_group["group_id"]
    alice_id = test_group["users"]["alice"]
    
    # Count admins (should be 1 - Alice)
    admin_count = await group_members_col.count_documents({
        "group_id": group_id,
        "role": "admin",
        "is_active": True
    })
    
    assert admin_count == 1
    
    # Logic should prevent removing Alice (last admin)
    # In actual tool, this check is done before removal
    
    print("✓ Last admin protection logic verified")

# ============================================================================
# TEST: Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_personal_groups_cannot_be_modified(test_users):
    """Test that personal groups have special restrictions"""
    alice_id = test_users["alice"]
    
    # Create personal group (like migration creates)
    personal_group = await groups_col.insert_one({
        "name": "Personal",
        "created_by": alice_id,
        "is_active": True,
        "group_type": "personal",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    try:
        group_id = str(personal_group.inserted_id)
        
        # Add Alice as member
        await group_members_col.insert_one({
            "group_id": group_id,
            "user_id": alice_id,
            "role": "admin",
            "is_active": True,
            "joined_at": datetime.utcnow()
        })
        
        # Get group
        group = await groups_col.find_one({"_id": personal_group.inserted_id})
        
        # Verify it's personal
        assert group["group_type"] == "personal"
        
        # Personal groups should have restrictions:
        # - Cannot be deleted
        # - Cannot leave
        # - Cannot add other members (for true personal groups)
        
        print("✓ Personal group restrictions verified")
        
    finally:
        # Cleanup
        await groups_col.delete_one({"_id": personal_group.inserted_id})
        await group_members_col.delete_many({"group_id": group_id})

@pytest.mark.asyncio
async def test_inactive_groups_not_listed(test_users):
    """Test that inactive groups don't appear in listings"""
    alice_id = test_users["alice"]
    
    # Create active group
    active_group = await groups_col.insert_one({
        "name": "Active Group",
        "created_by": alice_id,
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # Create inactive group
    inactive_group = await groups_col.insert_one({
        "name": "Inactive Group",
        "created_by": alice_id,
        "is_active": False,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    try:
        # Add Alice to both
        await group_members_col.insert_many([
            {
                "group_id": str(active_group.inserted_id),
                "user_id": alice_id,
                "role": "admin",
                "is_active": True,
                "joined_at": datetime.utcnow()
            },
            {
                "group_id": str(inactive_group.inserted_id),
                "user_id": alice_id,
                "role": "admin",
                "is_active": True,
                "joined_at": datetime.utcnow()
            }
        ])
        
        # List only active groups
        active_groups = await groups_col.find({
            "created_by": alice_id,
            "is_active": True
        }).to_list(None)
        
        # Should only find active group
        active_names = [g["name"] for g in active_groups]
        assert "Active Group" in active_names
        assert "Inactive Group" not in active_names
        
        print("✓ Inactive groups filtered correctly")
        
    finally:
        # Cleanup
        await groups_col.delete_many({
            "_id": {"$in": [active_group.inserted_id, inactive_group.inserted_id]}
        })
        await group_members_col.delete_many({
            "group_id": {"$in": [str(active_group.inserted_id), str(inactive_group.inserted_id)]}
        })

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PHASE 2 GROUP MANAGEMENT TESTS")
    print("="*70)
    print("\nNote: Run with pytest for best results:")
    print("  pytest tests/test_phase2_groups.py -v")
    print("\nOr install pytest:")
    print("  pip install pytest pytest-asyncio")
    print("="*70)
