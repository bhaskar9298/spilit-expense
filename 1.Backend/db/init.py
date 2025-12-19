# db/init.py - Initialize all collections with schemas and indexes
# Phase 1: Enhanced to support expense sharing functionality

from .client import (
    db, 
    expenses_col, 
    users_col,
    groups_col,
    group_members_col,
    expense_participants_col,
    balances_col,
    settlements_col
)
from .schema import COLLECTION_SCHEMAS
from datetime import datetime
from pymongo.errors import OperationFailure
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# MAIN SETUP FUNCTION
# ============================================================================

async def setup_collection_hybrid():
    """
    Creates collections if missing, applies schema validators,
    creates indexes, and performs test writes.
    
    Phase 1: Enhanced to include all new collections for expense sharing.
    """
    
    logger.info("=== Starting Database Initialization (Phase 1) ===")
    
    # Setup existing collections (backward compatible)
    await setup_users_collection()
    await setup_expenses_collection()
    
    # Setup new collections (Phase 1)
    await setup_groups_collection()
    await setup_group_members_collection()
    await setup_expense_participants_collection()
    await setup_balances_collection()
    await setup_settlements_collection()
    
    logger.info("=== Database Initialization Complete ===")

# ============================================================================
# EXISTING COLLECTIONS (maintained for backward compatibility)
# ============================================================================

async def setup_users_collection():
    """Setup users collection with email index"""
    cname = "users"
    collection = users_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                    validationLevel="moderate",
                    validationAction="error"
                )
                logger.info(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Unique index on email
        await collection.create_index([("email", 1)], unique=True, name="idx_email_unique")
        logger.info(f"[OK] {cname} indexes ensured.")
        
    except Exception as e:
        logger.error(f"Error setting up {cname}: {e}")
        raise

async def setup_expenses_collection():
    """
    Setup expenses collection with enhanced schema and indexes.
    Phase 1: Added group_id and split_type fields (optional for backward compatibility)
    """
    cname = "expenses"
    collection = expenses_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise

    if cname not in existing:
        try:
            await db.create_collection(
                cname,
                validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                validationLevel="moderate",
                validationAction="error"
            )
            logger.info(f"[OK] Created '{cname}' with JSON-schema validator.")
        except Exception as e:
            await db.create_collection(cname)
            logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
    else:
        try:
            await db.command({
                "collMod": cname,
                "validator": {"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                "validationLevel": "moderate",
                "validationAction":"error"
            })
            logger.info(f"[OK] Validator updated on '{cname}'.")
        except OperationFailure:
            logger.warning(f"[WARN] collMod restricted; continuing without update.")
        except Exception as e:
            logger.warning(f"[WARN] collMod error: {e}")

    # Indexes for expenses (backward compatible + new group-based indexes)
    try:
        # Existing indexes (backward compatibility)
        await collection.create_index([("user_id", 1), ("date", -1)], name="idx_user_date")
        await collection.create_index([("user_id", 1), ("category", 1)], name="idx_user_category")
        await collection.create_index([("date", -1)], name="idx_date_desc")
        
        # New indexes (Phase 1: group-based queries)
        await collection.create_index([("group_id", 1), ("date", -1)], name="idx_group_date")
        await collection.create_index([("group_id", 1), ("paid_by", 1)], name="idx_group_paidby")
        await collection.create_index([("paid_by", 1)], name="idx_paidby")
        
        logger.info(f"[OK] {cname} indexes ensured.")
    except Exception as e:
        logger.warning(f"Index creation issue for {cname}: {e}")

    # Test write (backward compatible)
    try:
        test_doc = {
            "user_id": "test_user_phase1",
            "date": "2000-01-01",
            "amount": 0,
            "category": "test",
            "subcategory": "",
            "note": "phase1-init-test",
            "created_at": datetime.utcnow()
        }
        inserted = await collection.insert_one(test_doc)
        await collection.delete_one({"_id": inserted.inserted_id})
        logger.info(f"[OK] {cname} test write OK.")
    except Exception as e:
        logger.error(f"Test write failed for {cname}: {e}")
        raise

# ============================================================================
# NEW COLLECTIONS (Phase 1: Expense Sharing)
# ============================================================================

async def setup_groups_collection():
    """Setup groups collection with creator index"""
    cname = "groups"
    collection = groups_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                    validationLevel="moderate",
                    validationAction="error"
                )
                logger.info(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Indexes
        await collection.create_index([("created_by", 1)], name="idx_created_by")
        await collection.create_index([("is_active", 1)], name="idx_is_active")
        await collection.create_index(
            [("created_by", 1), ("is_active", 1)], 
            name="idx_creator_active"
        )
        
        logger.info(f"[OK] {cname} indexes ensured.")
        
    except Exception as e:
        logger.error(f"Error setting up {cname}: {e}")
        raise

async def setup_group_members_collection():
    """Setup group_members collection with compound unique index"""
    cname = "group_members"
    collection = group_members_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                    validationLevel="moderate",
                    validationAction="error"
                )
                logger.info(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Critical: Compound unique index to prevent duplicate memberships
        await collection.create_index(
            [("group_id", 1), ("user_id", 1)], 
            unique=True, 
            name="idx_group_user_unique"
        )
        
        # Query optimization indexes
        await collection.create_index([("user_id", 1)], name="idx_user")
        await collection.create_index([("group_id", 1)], name="idx_group")
        await collection.create_index(
            [("group_id", 1), ("is_active", 1)], 
            name="idx_group_active"
        )
        
        logger.info(f"[OK] {cname} indexes ensured.")
        
    except Exception as e:
        logger.error(f"Error setting up {cname}: {e}")
        raise

async def setup_expense_participants_collection():
    """Setup expense_participants collection for split tracking"""
    cname = "expense_participants"
    collection = expense_participants_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                    validationLevel="moderate",
                    validationAction="error"
                )
                logger.info(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Compound unique index to prevent duplicate participants
        await collection.create_index(
            [("expense_id", 1), ("user_id", 1)], 
            unique=True, 
            name="idx_expense_user_unique"
        )
        
        # Query optimization indexes
        await collection.create_index([("expense_id", 1)], name="idx_expense")
        await collection.create_index([("user_id", 1)], name="idx_user")
        
        logger.info(f"[OK] {cname} indexes ensured.")
        
    except Exception as e:
        logger.error(f"Error setting up {cname}: {e}")
        raise

async def setup_balances_collection():
    """Setup balances collection with compound unique index for balance lookups"""
    cname = "balances"
    collection = balances_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                    validationLevel="moderate",
                    validationAction="error"
                )
                logger.info(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Critical: Compound unique index for fast balance lookups
        await collection.create_index(
            [("group_id", 1), ("from_user_id", 1), ("to_user_id", 1)], 
            unique=True, 
            name="idx_group_from_to_unique"
        )
        
        # Query optimization indexes
        await collection.create_index([("group_id", 1)], name="idx_group")
        await collection.create_index(
            [("group_id", 1), ("from_user_id", 1)], 
            name="idx_group_from"
        )
        await collection.create_index(
            [("group_id", 1), ("to_user_id", 1)], 
            name="idx_group_to"
        )
        
        logger.info(f"[OK] {cname} indexes ensured.")
        
    except Exception as e:
        logger.error(f"Error setting up {cname}: {e}")
        raise

async def setup_settlements_collection():
    """Setup settlements collection for payment tracking"""
    cname = "settlements"
    collection = settlements_col
    
    logger.info(f"Setting up collection: {cname}")
    
    try:
        existing = await db.list_collection_names()
        
        if cname not in existing:
            try:
                await db.create_collection(
                    cname,
                    validator={"$jsonSchema": COLLECTION_SCHEMAS[cname]},
                    validationLevel="moderate",
                    validationAction="error"
                )
                logger.info(f"[OK] Created '{cname}' with validator.")
            except Exception as e:
                await db.create_collection(cname)
                logger.warning(f"[OK] Created '{cname}' WITHOUT validator. Details: {e}")
        
        # Indexes for settlement queries
        await collection.create_index(
            [("group_id", 1), ("settled_at", -1)], 
            name="idx_group_settled"
        )
        await collection.create_index([("paid_by", 1)], name="idx_paid_by")
        await collection.create_index([("paid_to", 1)], name="idx_paid_to")
        await collection.create_index(
            [("group_id", 1), ("paid_by", 1), ("paid_to", 1)], 
            name="idx_group_payer_payee"
        )
        
        logger.info(f"[OK] {cname} indexes ensured.")
        
    except Exception as e:
        logger.error(f"Error setting up {cname}: {e}")
        raise
