# migrations/phase1_migration.py
"""
Phase 1 Migration: Migrate existing expenses to group-based model

This migration:
1. Creates a "Personal" group for each existing user
2. Migrates all existing expenses to their user's Personal group
3. Adds default values for new fields (split_type='none', paid_by=user_id)
4. Creates group_member records for each user's Personal group
5. Does NOT create expense_participants (personal expenses don't have splits)

This migration is SAFE and IDEMPOTENT:
- Can be run multiple times without issues
- Does not delete or modify existing data structure
- Only adds new fields and relationships
- Preserves backward compatibility
"""

import sys
import pathlib
import asyncio
from datetime import datetime
import logging

# Add parent directory to path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.client import (
    db,
    users_col,
    expenses_col,
    groups_col,
    group_members_col
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MIGRATION FUNCTIONS
# ============================================================================

async def get_all_users():
    """Get all users from the database"""
    users = await users_col.find({}).to_list(None)
    logger.info(f"Found {len(users)} users in database")
    return users

async def create_personal_group_for_user(user_id: str, user_email: str):
    """
    Create a 'Personal' group for a user if it doesn't already exist.
    Returns the group_id.
    """
    # Check if personal group already exists for this user
    existing_group = await groups_col.find_one({
        "created_by": user_id,
        "group_type": "personal"
    })
    
    if existing_group:
        logger.info(f"Personal group already exists for user {user_email}: {existing_group['_id']}")
        return str(existing_group["_id"])
    
    # Create new personal group
    group_doc = {
        "name": "Personal",
        "description": "Personal expenses (auto-created during migration)",
        "created_by": user_id,
        "is_active": True,
        "group_type": "personal",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await groups_col.insert_one(group_doc)
    group_id = str(result.inserted_id)
    
    logger.info(f"Created Personal group {group_id} for user {user_email}")
    
    # Create group membership record
    member_doc = {
        "group_id": group_id,
        "user_id": user_id,
        "role": "admin",
        "is_active": True,
        "joined_at": datetime.utcnow()
    }
    
    await group_members_col.insert_one(member_doc)
    logger.info(f"Added user {user_email} as admin of Personal group")
    
    return group_id

async def migrate_user_expenses(user_id: str, group_id: str, user_email: str):
    """
    Migrate all expenses for a user to their Personal group.
    Adds new fields: group_id, paid_by, split_type, updated_at
    """
    # Find expenses that don't have group_id set (need migration)
    expenses_to_migrate = await expenses_col.count_documents({
        "user_id": user_id,
        "group_id": {"$exists": False}
    })
    
    if expenses_to_migrate == 0:
        logger.info(f"No expenses to migrate for user {user_email}")
        return 0
    
    # Update expenses with new fields
    result = await expenses_col.update_many(
        {
            "user_id": user_id,
            "group_id": {"$exists": False}
        },
        {
            "$set": {
                "group_id": group_id,
                "paid_by": user_id,  # User paid for their own expenses
                "split_type": "none",  # Personal expenses have no splits
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    logger.info(f"Migrated {result.modified_count} expenses for user {user_email} to group {group_id}")
    return result.modified_count

async def verify_migration():
    """Verify that migration completed successfully"""
    logger.info("=== Verifying Migration ===")
    
    # Count expenses without group_id
    unmigrated_expenses = await expenses_col.count_documents({
        "group_id": {"$exists": False}
    })
    
    if unmigrated_expenses > 0:
        logger.warning(f"WARNING: {unmigrated_expenses} expenses still without group_id")
        return False
    
    # Count groups
    total_groups = await groups_col.count_documents({})
    personal_groups = await groups_col.count_documents({"group_type": "personal"})
    
    logger.info(f"Total groups: {total_groups}")
    logger.info(f"Personal groups: {personal_groups}")
    
    # Count group members
    total_members = await group_members_col.count_documents({})
    logger.info(f"Total group members: {total_members}")
    
    logger.info("=== Migration Verification Complete ===")
    return unmigrated_expenses == 0

# ============================================================================
# MAIN MIGRATION SCRIPT
# ============================================================================

async def run_migration():
    """
    Main migration function.
    Safe to run multiple times - will skip already migrated data.
    """
    logger.info("="*70)
    logger.info("PHASE 1 MIGRATION: Migrate Expenses to Group-Based Model")
    logger.info("="*70)
    
    try:
        # Get all users
        users = await get_all_users()
        
        if not users:
            logger.warning("No users found in database. Nothing to migrate.")
            return
        
        total_migrated_expenses = 0
        
        # For each user, create Personal group and migrate expenses
        for user in users:
            user_id = str(user["_id"])
            user_email = user.get("email", "unknown")
            
            logger.info(f"\n--- Processing user: {user_email} ---")
            
            # Create or get Personal group
            group_id = await create_personal_group_for_user(user_id, user_email)
            
            # Migrate expenses
            migrated_count = await migrate_user_expenses(user_id, group_id, user_email)
            total_migrated_expenses += migrated_count
        
        # Verify migration
        logger.info(f"\n{'='*70}")
        logger.info(f"MIGRATION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total users processed: {len(users)}")
        logger.info(f"Total expenses migrated: {total_migrated_expenses}")
        
        success = await verify_migration()
        
        if success:
            logger.info("\n✓ MIGRATION COMPLETED SUCCESSFULLY")
        else:
            logger.error("\n✗ MIGRATION COMPLETED WITH WARNINGS - Please review logs")
        
    except Exception as e:
        logger.error(f"\n✗ MIGRATION FAILED: {e}")
        raise

# ============================================================================
# ROLLBACK FUNCTION (if needed)
# ============================================================================

async def rollback_migration():
    """
    Rollback migration by removing added fields.
    WARNING: This will remove group associations but keep the data intact.
    """
    logger.info("="*70)
    logger.info("ROLLING BACK PHASE 1 MIGRATION")
    logger.info("="*70)
    
    # Remove new fields from expenses
    result = await expenses_col.update_many(
        {"split_type": "none"},  # Only rollback personal expenses
        {
            "$unset": {
                "group_id": "",
                "paid_by": "",
                "split_type": "",
                "updated_at": ""
            }
        }
    )
    
    logger.info(f"Removed migration fields from {result.modified_count} expenses")
    
    # Delete personal groups and memberships
    personal_groups = await groups_col.find({"group_type": "personal"}).to_list(None)
    group_ids = [str(g["_id"]) for g in personal_groups]
    
    if group_ids:
        # Delete group members
        member_result = await group_members_col.delete_many({"group_id": {"$in": group_ids}})
        logger.info(f"Deleted {member_result.deleted_count} group memberships")
        
        # Delete groups
        group_result = await groups_col.delete_many({"_id": {"$in": [g["_id"] for g in personal_groups]}})
        logger.info(f"Deleted {group_result.deleted_count} personal groups")
    
    logger.info("\n✓ ROLLBACK COMPLETED")

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("\n⚠️  WARNING: You are about to ROLLBACK the migration!")
        print("This will remove all Personal groups and reset expenses to pre-migration state.")
        response = input("Are you sure? Type 'yes' to continue: ")
        
        if response.lower() == 'yes':
            asyncio.run(rollback_migration())
        else:
            print("Rollback cancelled.")
    else:
        asyncio.run(run_migration())
