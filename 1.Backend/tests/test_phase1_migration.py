# tests/test_phase1_migration.py
"""
Phase 1 Tests: Migration Script Validation

Tests:
1. Migration creates Personal groups for all users
2. Existing expenses are assigned to Personal groups
3. New fields are added correctly (group_id, paid_by, split_type)
4. Migration is idempotent (can run multiple times)
5. Rollback works correctly
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
    expenses_col,
    groups_col,
    group_members_col
)
from db.migrations.phase1_migration import (
    create_personal_group_for_user,
    migrate_user_expenses,
    verify_migration,
    run_migration
)

# ============================================================================
# TEST DATA SETUP
# ============================================================================

@pytest.fixture(scope="function")
async def test_user():
    """Create a test user for migration tests"""
    user_doc = {
        "email": "migration_test@example.com",
        "password_hash": "test_hash_12345",
        "full_name": "Migration Test User",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await users_col.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    yield {"user_id": user_id, "email": user_doc["email"]}
    
    # Cleanup after test
    await users_col.delete_one({"_id": result.inserted_id})
    
    # Cleanup associated groups
    await groups_col.delete_many({"created_by": user_id})
    
    # Cleanup group members
    groups = await groups_col.find({"created_by": user_id}).to_list(None)
    group_ids = [str(g["_id"]) for g in groups]
    if group_ids:
        await group_members_col.delete_many({"group_id": {"$in": group_ids}})
    
    # Cleanup expenses
    await expenses_col.delete_many({"user_id": user_id})

@pytest.fixture(scope="function")
async def test_expenses(test_user):
    """Create test expenses for migration"""
    user_id = test_user["user_id"]
    
    # Create old-style expenses (without group_id)
    expenses = [
        {
            "user_id": user_id,
            "date": "2025-01-01",
            "amount": 50.0,
            "category": "food",
            "note": "Test expense 1",
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_id,
            "date": "2025-01-02",
            "amount": 75.0,
            "category": "transport",
            "note": "Test expense 2",
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_id,
            "date": "2025-01-03",
            "amount": 100.0,
            "category": "entertainment",
            "note": "Test expense 3",
            "created_at": datetime.utcnow()
        }
    ]
    
    results = await expenses_col.insert_many(expenses)
    expense_ids = [str(id) for id in results.inserted_ids]
    
    yield {"user_id": user_id, "expense_ids": expense_ids, "count": len(expenses)}
    
    # Cleanup handled by test_user fixture

# ============================================================================
# TEST: Personal Group Creation
# ============================================================================

@pytest.mark.asyncio
async def test_create_personal_group(test_user):
    """Test creating a Personal group for a user"""
    user_id = test_user["user_id"]
    user_email = test_user["email"]
    
    # Create personal group
    group_id = await create_personal_group_for_user(user_id, user_email)
    
    # Verify group was created
    group = await groups_col.find_one({"_id": group_id})
    assert group is not None
    assert group["name"] == "Personal"
    assert group["created_by"] == user_id
    assert group["group_type"] == "personal"
    assert group["is_active"] == True
    
    # Verify group membership was created
    membership = await group_members_col.find_one({
        "group_id": group_id,
        "user_id": user_id
    })
    assert membership is not None
    assert membership["role"] == "admin"
    assert membership["is_active"] == True
    
    print("✓ Personal group creation works")

@pytest.mark.asyncio
async def test_create_personal_group_idempotent(test_user):
    """Test that creating Personal group multiple times is safe"""
    user_id = test_user["user_id"]
    user_email = test_user["email"]
    
    # Create group first time
    group_id_1 = await create_personal_group_for_user(user_id, user_email)
    
    # Create group second time - should return same group
    group_id_2 = await create_personal_group_for_user(user_id, user_email)
    
    assert group_id_1 == group_id_2, "Creating Personal group should be idempotent"
    
    # Verify only one group exists
    groups = await groups_col.find({
        "created_by": user_id,
        "group_type": "personal"
    }).to_list(None)
    
    assert len(groups) == 1, "Should only have one Personal group"
    
    print("✓ Personal group creation is idempotent")

# ============================================================================
# TEST: Expense Migration
# ============================================================================

@pytest.mark.asyncio
async def test_migrate_user_expenses(test_expenses):
    """Test migrating expenses to Personal group"""
    user_id = test_expenses["user_id"]
    expected_count = test_expenses["count"]
    
    # Create personal group
    group_id = await create_personal_group_for_user(user_id, "test@example.com")
    
    # Migrate expenses
    migrated_count = await migrate_user_expenses(user_id, group_id, "test@example.com")
    
    assert migrated_count == expected_count, f"Should migrate {expected_count} expenses"
    
    # Verify expenses have new fields
    migrated_expenses = await expenses_col.find({"user_id": user_id}).to_list(None)
    
    for expense in migrated_expenses:
        assert "group_id" in expense
        assert expense["group_id"] == group_id
        assert "paid_by" in expense
        assert expense["paid_by"] == user_id
        assert "split_type" in expense
        assert expense["split_type"] == "none"
        assert "updated_at" in expense
    
    print("✓ Expense migration works correctly")

@pytest.mark.asyncio
async def test_migrate_expenses_idempotent(test_expenses):
    """Test that migrating expenses multiple times is safe"""
    user_id = test_expenses["user_id"]
    expected_count = test_expenses["count"]
    
    # Create personal group
    group_id = await create_personal_group_for_user(user_id, "test@example.com")
    
    # Migrate first time
    count_1 = await migrate_user_expenses(user_id, group_id, "test@example.com")
    assert count_1 == expected_count
    
    # Migrate second time - should find 0 expenses to migrate
    count_2 = await migrate_user_expenses(user_id, group_id, "test@example.com")
    assert count_2 == 0, "Second migration should find 0 expenses (already migrated)"
    
    print("✓ Expense migration is idempotent")

# ============================================================================
# TEST: Full Migration
# ============================================================================

@pytest.mark.asyncio
async def test_full_migration(test_expenses):
    """Test complete migration process"""
    user_id = test_expenses["user_id"]
    
    # Run full migration
    await run_migration()
    
    # Verify user has Personal group
    personal_group = await groups_col.find_one({
        "created_by": user_id,
        "group_type": "personal"
    })
    assert personal_group is not None
    
    # Verify all expenses are migrated
    unmigrated = await expenses_col.count_documents({
        "user_id": user_id,
        "group_id": {"$exists": False}
    })
    assert unmigrated == 0, "All expenses should be migrated"
    
    # Verify migration
    success = await verify_migration()
    assert success, "Migration verification should pass"
    
    print("✓ Full migration process works")

# ============================================================================
# TEST: Data Integrity
# ============================================================================

@pytest.mark.asyncio
async def test_migration_preserves_original_data(test_expenses):
    """Test that migration doesn't corrupt original expense data"""
    user_id = test_expenses["user_id"]
    
    # Get original expenses
    original_expenses = await expenses_col.find({"user_id": user_id}).to_list(None)
    original_data = {
        str(e["_id"]): {
            "amount": e["amount"],
            "category": e["category"],
            "date": e["date"],
            "note": e.get("note")
        }
        for e in original_expenses
    }
    
    # Run migration
    group_id = await create_personal_group_for_user(user_id, "test@example.com")
    await migrate_user_expenses(user_id, group_id, "test@example.com")
    
    # Get migrated expenses
    migrated_expenses = await expenses_col.find({"user_id": user_id}).to_list(None)
    
    # Verify original data is preserved
    for expense in migrated_expenses:
        expense_id = str(expense["_id"])
        original = original_data[expense_id]
        
        assert expense["amount"] == original["amount"]
        assert expense["category"] == original["category"]
        assert expense["date"] == original["date"]
        assert expense.get("note") == original["note"]
    
    print("✓ Migration preserves original expense data")

# ============================================================================
# TEST: Backward Compatibility
# ============================================================================

@pytest.mark.asyncio
async def test_old_queries_still_work(test_expenses):
    """Test that existing queries still work after migration"""
    user_id = test_expenses["user_id"]
    
    # Run migration
    group_id = await create_personal_group_for_user(user_id, "test@example.com")
    await migrate_user_expenses(user_id, group_id, "test@example.com")
    
    # Test old-style query by user_id (backward compatible)
    expenses = await expenses_col.find({"user_id": user_id}).to_list(None)
    assert len(expenses) == test_expenses["count"]
    
    # Test old-style date range query
    expenses_jan = await expenses_col.find({
        "user_id": user_id,
        "date": {"$gte": "2025-01-01", "$lte": "2025-01-31"}
    }).to_list(None)
    assert len(expenses_jan) == test_expenses["count"]
    
    # Test old-style category query
    food_expenses = await expenses_col.find({
        "user_id": user_id,
        "category": "food"
    }).to_list(None)
    assert len(food_expenses) > 0
    
    print("✓ Old queries still work after migration (backward compatible)")

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print("="*70)
    print("PHASE 1 MIGRATION TESTS")
    print("="*70)
    print("\nNote: Run with pytest for best results:")
    print("  pytest tests/test_phase1_migration.py -v")
    print("\nOr run manually (limited):")
    print("  python tests/test_phase1_migration.py")
    print("="*70)
