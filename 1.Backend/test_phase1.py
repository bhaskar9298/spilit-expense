#!/usr/bin/env python3
"""
Quick Test Runner for Phase 1

Runs all Phase 1 tests and reports results.
Use this for quick verification during development.
"""

import asyncio
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

async def run_schema_tests():
    """Run all schema validation tests"""
    print_header("PHASE 1 SCHEMA TESTS")
    
    try:
        from tests.test_phase1_schema import (
            test_all_collections_exist,
            test_users_indexes,
            test_expenses_indexes,
            test_groups_indexes,
            test_group_members_indexes,
            test_expense_participants_indexes,
            test_balances_indexes,
            test_settlements_indexes,
            test_backward_compatible_expense_insert,
            test_new_expense_format,
            test_group_creation,
            test_group_member_unique_constraint,
            test_balance_unique_constraint
        )
        
        tests = [
            ("Collections Exist", test_all_collections_exist),
            ("Users Indexes", test_users_indexes),
            ("Expenses Indexes", test_expenses_indexes),
            ("Groups Indexes", test_groups_indexes),
            ("Group Members Indexes", test_group_members_indexes),
            ("Expense Participants Indexes", test_expense_participants_indexes),
            ("Balances Indexes", test_balances_indexes),
            ("Settlements Indexes", test_settlements_indexes),
            ("Backward Compatible Insert", test_backward_compatible_expense_insert),
            ("New Expense Format", test_new_expense_format),
            ("Group Creation", test_group_creation),
            ("Group Member Unique Constraint", test_group_member_unique_constraint),
            ("Balance Unique Constraint", test_balance_unique_constraint),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                await test_func(None)
                print_success(f"{test_name}")
                passed += 1
            except Exception as e:
                print_error(f"{test_name}: {str(e)}")
                failed += 1
        
        print(f"\n{BLUE}Schema Tests Summary:{RESET}")
        print(f"  Passed: {GREEN}{passed}{RESET}")
        print(f"  Failed: {RED}{failed}{RESET}")
        
        return failed == 0
        
    except Exception as e:
        print_error(f"Failed to import schema tests: {e}")
        return False

async def run_quick_smoke_test():
    """Run quick smoke tests to verify basic functionality"""
    print_header("QUICK SMOKE TESTS")
    
    try:
        from db.client import (
            expenses_col,
            groups_col,
            group_members_col,
            balances_col
        )
        from datetime import datetime
        from bson import ObjectId
        
        # Test 1: Can insert/delete expense
        try:
            expense = {
                "user_id": "smoke_test_user",
                "date": "2025-12-18",
                "amount": 99.99,
                "category": "test",
                "created_at": datetime.utcnow()
            }
            result = await expenses_col.insert_one(expense)
            await expenses_col.delete_one({"_id": result.inserted_id})
            print_success("Expense CRUD works")
        except Exception as e:
            print_error(f"Expense CRUD failed: {e}")
            return False
        
        # Test 2: Can insert/delete group
        try:
            group = {
                "name": "Smoke Test Group",
                "created_by": "smoke_test_user",
                "is_active": True,
                "group_type": "shared",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await groups_col.insert_one(group)
            await groups_col.delete_one({"_id": result.inserted_id})
            print_success("Group CRUD works")
        except Exception as e:
            print_error(f"Group CRUD failed: {e}")
            return False
        
        # Test 3: Unique constraint works
        try:
            from pymongo.errors import DuplicateKeyError
            
            member1 = {
                "group_id": "test_group",
                "user_id": "test_user",
                "role": "member",
                "is_active": True,
                "joined_at": datetime.utcnow()
            }
            
            result1 = await group_members_col.insert_one(member1)
            
            try:
                await group_members_col.insert_one(member1)
                print_error("Unique constraint NOT working (duplicate allowed)")
                await group_members_col.delete_one({"_id": result1.inserted_id})
                return False
            except DuplicateKeyError:
                print_success("Unique constraints work")
                await group_members_col.delete_one({"_id": result1.inserted_id})
        except Exception as e:
            print_error(f"Unique constraint test failed: {e}")
            return False
        
        # Test 4: Indexes exist
        try:
            indexes = await group_members_col.index_information()
            if "idx_group_user_unique" in indexes:
                print_success("Critical indexes exist")
            else:
                print_warning("Some indexes missing - run setup_phase1.py")
        except Exception as e:
            print_error(f"Index check failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Smoke tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_migration_status():
    """Check if migration has been run (if needed)"""
    print_header("MIGRATION STATUS CHECK")
    
    try:
        from db.client import expenses_col, users_col, groups_col
        
        # Check if there are any users
        user_count = await users_col.count_documents({})
        
        if user_count == 0:
            print_warning("No users in database - migration not needed")
            return True
        
        # Check if there are expenses without group_id
        unmigrated = await expenses_col.count_documents({
            "group_id": {"$exists": False}
        })
        
        if unmigrated > 0:
            print_warning(f"{unmigrated} expenses need migration")
            print(f"  Run: python db/migrations/phase1_migration.py")
            return False
        else:
            print_success(f"All expenses migrated (0 without group_id)")
        
        # Check if Personal groups exist
        personal_groups = await groups_col.count_documents({
            "group_type": "personal"
        })
        
        if personal_groups == user_count:
            print_success(f"All {user_count} users have Personal groups")
        else:
            print_warning(f"Users: {user_count}, Personal groups: {personal_groups}")
            print(f"  Some users may be missing Personal groups")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Migration check failed: {e}")
        return False

async def main():
    """Run all tests"""
    print_header("PHASE 1 TEST SUITE")
    print(f"Testing database schema, indexes, and functionality\n")
    
    # Initialize database first
    try:
        from db.init import setup_collection_hybrid
        print("Ensuring database is initialized...")
        await setup_collection_hybrid()
        print_success("Database initialized\n")
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        print("  Run: python setup_phase1.py")
        return 1
    
    # Run smoke tests first (quick check)
    smoke_passed = await run_quick_smoke_test()
    
    # Run migration check
    migration_ok = await check_migration_status()
    
    # Run full schema tests
    schema_passed = await run_schema_tests()
    
    # Summary
    print_header("FINAL SUMMARY")
    
    results = {
        "Smoke Tests": smoke_passed,
        "Migration Status": migration_ok,
        "Schema Tests": schema_passed
    }
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print()
    if all_passed:
        print(f"{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✓ ALL TESTS PASSED - PHASE 1 READY{RESET}")
        print(f"{GREEN}{'='*70}{RESET}")
        return 0
    else:
        print(f"{RED}{'='*70}{RESET}")
        print(f"{RED}✗ SOME TESTS FAILED - REVIEW OUTPUT ABOVE{RESET}")
        print(f"{RED}{'='*70}{RESET}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
