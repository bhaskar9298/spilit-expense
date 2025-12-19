#!/usr/bin/env python3
"""
Phase 1 Setup Script - Quick Start

This script helps you set up Phase 1 database schema and run migration.
Run this after Phase 1 implementation is complete.

Usage:
    python setup_phase1.py [--skip-init] [--skip-migration] [--skip-tests]
"""

import sys
import pathlib
import asyncio
import argparse
from datetime import datetime


# Add parent directory to path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("="*70)
print("PHASE 1 SETUP SCRIPT")
print("="*70)
print()

# ============================================================================
# PARSE ARGUMENTS
# ============================================================================

parser = argparse.ArgumentParser(description="Phase 1 Setup Script")
parser.add_argument("--skip-init", action="store_true", help="Skip database initialization")
parser.add_argument("--skip-migration", action="store_true", help="Skip data migration")
parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
parser.add_argument("--test-only", action="store_true", help="Only run tests")

args = parser.parse_args()

# ============================================================================
# STEP 1: DATABASE INITIALIZATION
# ============================================================================

async def run_initialization():
    """Initialize database with Phase 1 schema"""
    print("Step 1: Initializing Database Schema")
    print("-" * 70)
    
    from db.init import setup_collection_hybrid
    
    try:
        await setup_collection_hybrid()
        print("\n✓ Database initialization completed successfully\n")
        return True
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}\n")
        return False

# ============================================================================
# STEP 2: DATA MIGRATION
# ============================================================================

async def run_migration():
    """Run Phase 1 migration"""
    print("Step 2: Migrating Existing Data")
    print("-" * 70)
    
    from db.migrations.phase1_migration import run_migration as migrate
    
    try:
        await migrate()
        print("\n✓ Data migration completed successfully\n")
        return True
    except Exception as e:
        print(f"\n✗ Data migration failed: {e}\n")
        return False

# ============================================================================
# STEP 3: RUN TESTS
# ============================================================================

async def run_tests():
    """Run Phase 1 tests"""
    print("Step 3: Running Tests")
    print("-" * 70)
    
    try:
        # Import test functions
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
        
        print("\n--- Schema Tests ---")
        await test_all_collections_exist(None)
        await test_users_indexes(None)
        await test_expenses_indexes(None)
        await test_groups_indexes(None)
        await test_group_members_indexes(None)
        await test_expense_participants_indexes(None)
        await test_balances_indexes(None)
        await test_settlements_indexes(None)
        
        print("\n--- Validation Tests ---")
        await test_backward_compatible_expense_insert(None)
        await test_new_expense_format(None)
        await test_group_creation(None)
        await test_group_member_unique_constraint(None)
        await test_balance_unique_constraint(None)
        
        print("\n✓ All tests passed successfully\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Tests failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Main setup routine"""
    
    if args.test_only:
        success = await run_tests()
        if success:
            print("="*70)
            print("✓ PHASE 1 TESTS COMPLETED SUCCESSFULLY")
            print("="*70)
        else:
            print("="*70)
            print("✗ PHASE 1 TESTS FAILED")
            print("="*70)
            sys.exit(1)
        return
    
    # Step 1: Initialize Database
    if not args.skip_init:
        init_success = await run_initialization()
        if not init_success:
            print("Setup failed at initialization step.")
            print("Fix the error and run again.")
            sys.exit(1)
    else:
        print("Step 1: Skipped (--skip-init)\n")
    
    # Step 2: Migrate Data
    if not args.skip_migration:
        migrate_success = await run_migration()
        if not migrate_success:
            print("Setup failed at migration step.")
            print("You can run migration separately: python db/migrations/phase1_migration.py")
            sys.exit(1)
    else:
        print("Step 2: Skipped (--skip-migration)\n")
    
    # Step 3: Run Tests
    if not args.skip_tests:
        test_success = await run_tests()
        if not test_success:
            print("Setup completed but tests failed.")
            print("Review test output above for details.")
            sys.exit(1)
    else:
        print("Step 3: Skipped (--skip-tests)\n")
    
    # Success!
    print("="*70)
    print("✓ PHASE 1 SETUP COMPLETED SUCCESSFULLY")
    print("="*70)
    print()
    print("Next Steps:")
    print("  1. Review PHASE1_README.md for documentation")
    print("  2. Verify database collections in MongoDB")
    print("  3. Test backward compatibility with existing code")
    print("  4. Proceed to Phase 2: Group Management")
    print()
    print("="*70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
