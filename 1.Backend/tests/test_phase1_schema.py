# tests/test_phase1_schema.py
"""
Phase 1 Tests: Database Schema and Initialization

Tests:
1. Collection creation with proper schemas
2. Index creation
3. Schema validation
4. Backward compatibility
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
    db,
    users_col,
    expenses_col,
    groups_col,
    group_members_col,
    expense_participants_col,
    balances_col,
    settlements_col
)
from db.init import setup_collection_hybrid

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
async def setup_database():
    """Setup database before tests"""
    await setup_collection_hybrid()
    yield
    # Cleanup test data after all tests
    # Note: We don't drop collections to preserve production data

# ============================================================================
# TEST: Collection Creation
# ============================================================================

@pytest.mark.asyncio
async def test_all_collections_exist(setup_database):
    """Test that all required collections were created"""
    collections = await db.list_collection_names()
    
    required_collections = [
        "users",
        "expenses",
        "groups",
        "group_members",
        "expense_participants",
        "balances",
        "settlements"
    ]
    
    for collection_name in required_collections:
        assert collection_name in collections, f"Collection '{collection_name}' not found"
    
    print("✓ All required collections exist")

# ============================================================================
# TEST: Index Creation
# ============================================================================

@pytest.mark.asyncio
async def test_users_indexes(setup_database):
    """Test users collection indexes"""
    indexes = await users_col.index_information()
    
    # Check unique email index exists
    assert "idx_email_unique" in indexes
    assert indexes["idx_email_unique"]["unique"] == True
    
    print("✓ Users indexes verified")

@pytest.mark.asyncio
async def test_expenses_indexes(setup_database):
    """Test expenses collection indexes (backward compatible + new)"""
    indexes = await expenses_col.index_information()
    
    # Existing indexes (backward compatibility)
    assert "idx_user_date" in indexes
    assert "idx_user_category" in indexes
    assert "idx_date_desc" in indexes
    
    # New indexes (Phase 1)
    assert "idx_group_date" in indexes
    assert "idx_group_paidby" in indexes
    assert "idx_paidby" in indexes
    
    print("✓ Expenses indexes verified (backward compatible + Phase 1)")

@pytest.mark.asyncio
async def test_groups_indexes(setup_database):
    """Test groups collection indexes"""
    indexes = await groups_col.index_information()
    
    assert "idx_created_by" in indexes
    assert "idx_is_active" in indexes
    assert "idx_creator_active" in indexes
    
    print("✓ Groups indexes verified")

@pytest.mark.asyncio
async def test_group_members_indexes(setup_database):
    """Test group_members collection indexes"""
    indexes = await group_members_col.index_information()
    
    # Critical: compound unique index
    assert "idx_group_user_unique" in indexes
    assert indexes["idx_group_user_unique"]["unique"] == True
    
    # Query optimization indexes
    assert "idx_user" in indexes
    assert "idx_group" in indexes
    assert "idx_group_active" in indexes
    
    print("✓ Group members indexes verified")

@pytest.mark.asyncio
async def test_expense_participants_indexes(setup_database):
    """Test expense_participants collection indexes"""
    indexes = await expense_participants_col.index_information()
    
    # Critical: compound unique index
    assert "idx_expense_user_unique" in indexes
    assert indexes["idx_expense_user_unique"]["unique"] == True
    
    assert "idx_expense" in indexes
    assert "idx_user" in indexes
    
    print("✓ Expense participants indexes verified")

@pytest.mark.asyncio
async def test_balances_indexes(setup_database):
    """Test balances collection indexes"""
    indexes = await balances_col.index_information()
    
    # Critical: compound unique index for balance lookups
    assert "idx_group_from_to_unique" in indexes
    assert indexes["idx_group_from_to_unique"]["unique"] == True
    
    # Query optimization indexes
    assert "idx_group" in indexes
    assert "idx_group_from" in indexes
    assert "idx_group_to" in indexes
    
    print("✓ Balances indexes verified")

@pytest.mark.asyncio
async def test_settlements_indexes(setup_database):
    """Test settlements collection indexes"""
    indexes = await settlements_col.index_information()
    
    assert "idx_group_settled" in indexes
    assert "idx_paid_by" in indexes
    assert "idx_paid_to" in indexes
    assert "idx_group_payer_payee" in indexes
    
    print("✓ Settlements indexes verified")

# ============================================================================
# TEST: Schema Validation
# ============================================================================

@pytest.mark.asyncio
async def test_backward_compatible_expense_insert(setup_database):
    """Test that old-style expense documents still work (backward compatibility)"""
    # Old format (without new fields)
    old_style_expense = {
        "user_id": "test_user_old_style",
        "date": "2025-01-01",
        "amount": 50.0,
        "category": "food",
        "subcategory": "lunch",
        "note": "test backward compatibility",
        "created_at": datetime.utcnow()
    }
    
    try:
        result = await expenses_col.insert_one(old_style_expense)
        assert result.inserted_id is not None
        
        # Cleanup
        await expenses_col.delete_one({"_id": result.inserted_id})
        
        print("✓ Backward compatible expense insert works")
    except Exception as e:
        pytest.fail(f"Backward compatible insert failed: {e}")

@pytest.mark.asyncio
async def test_new_expense_format(setup_database):
    """Test new expense format with group_id and split_type"""
    new_style_expense = {
        "user_id": "test_user_new",
        "group_id": "test_group_123",
        "paid_by": "test_user_new",
        "date": "2025-01-01",
        "amount": 100.0,
        "category": "food",
        "split_type": "equal",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = await expenses_col.insert_one(new_style_expense)
        assert result.inserted_id is not None
        
        # Cleanup
        await expenses_col.delete_one({"_id": result.inserted_id})
        
        print("✓ New expense format with Phase 1 fields works")
    except Exception as e:
        pytest.fail(f"New format insert failed: {e}")

@pytest.mark.asyncio
async def test_group_creation(setup_database):
    """Test creating a group"""
    group_doc = {
        "name": "Test Group",
        "description": "Test group for schema validation",
        "created_by": "test_user_123",
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = await groups_col.insert_one(group_doc)
        assert result.inserted_id is not None
        
        # Verify retrieval
        group = await groups_col.find_one({"_id": result.inserted_id})
        assert group["name"] == "Test Group"
        assert group["group_type"] == "shared"
        
        # Cleanup
        await groups_col.delete_one({"_id": result.inserted_id})
        
        print("✓ Group creation works")
    except Exception as e:
        pytest.fail(f"Group creation failed: {e}")

@pytest.mark.asyncio
async def test_group_member_unique_constraint(setup_database):
    """Test that duplicate group memberships are prevented"""
    # Create test group first
    group_doc = {
        "name": "Test Group for Members",
        "created_by": "test_user",
        "is_active": True,
        "group_type": "shared",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    group_result = await groups_col.insert_one(group_doc)
    group_id = str(group_result.inserted_id)
    
    # Add first member
    member_doc = {
        "group_id": group_id,
        "user_id": "test_user_abc",
        "role": "member",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    
    try:
        result1 = await group_members_col.insert_one(member_doc)
        assert result1.inserted_id is not None
        
        # Try to add same member again - should fail
        from pymongo.errors import DuplicateKeyError
        with pytest.raises(DuplicateKeyError):
            await group_members_col.insert_one(member_doc)
        
        print("✓ Group member unique constraint works")
        
    finally:
        # Cleanup
        await group_members_col.delete_many({"group_id": group_id})
        await groups_col.delete_one({"_id": group_result.inserted_id})

@pytest.mark.asyncio
async def test_balance_unique_constraint(setup_database):
    """Test that duplicate balance records are prevented"""
    balance_doc = {
        "group_id": "test_group_balance",
        "from_user_id": "user_a",
        "to_user_id": "user_b",
        "amount": 50.0,
        "updated_at": datetime.utcnow()
    }
    
    try:
        result1 = await balances_col.insert_one(balance_doc)
        assert result1.inserted_id is not None
        
        # Try to add same balance record again - should fail
        from pymongo.errors import DuplicateKeyError
        with pytest.raises(DuplicateKeyError):
            await balances_col.insert_one(balance_doc)
        
        print("✓ Balance unique constraint works")
        
    finally:
        # Cleanup
        await balances_col.delete_many({"group_id": "test_group_balance"})

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print("="*70)
    print("PHASE 1 SCHEMA TESTS")
    print("="*70)
    
    # Run tests manually (pytest is better, but this works too)
    async def run_all_tests():
        await setup_collection_hybrid()
        
        print("\n--- Testing Collection Creation ---")
        await test_all_collections_exist(None)
        
        print("\n--- Testing Indexes ---")
        await test_users_indexes(None)
        await test_expenses_indexes(None)
        await test_groups_indexes(None)
        await test_group_members_indexes(None)
        await test_expense_participants_indexes(None)
        await test_balances_indexes(None)
        await test_settlements_indexes(None)
        
        print("\n--- Testing Schema Validation ---")
        await test_backward_compatible_expense_insert(None)
        await test_new_expense_format(None)
        await test_group_creation(None)
        await test_group_member_unique_constraint(None)
        await test_balance_unique_constraint(None)
        
        print("\n" + "="*70)
        print("✓ ALL PHASE 1 SCHEMA TESTS PASSED")
        print("="*70)
    
    asyncio.run(run_all_tests())
