# Phase 1: Database Schema Evolution - Documentation

## Overview

Phase 1 extends the existing expense tracker database schema to support expense sharing functionality while maintaining **100% backward compatibility** with the existing system.

## Changes Summary

### New Collections
1. **groups** - Manage expense groups
2. **group_members** - Track group memberships with roles
3. **expense_participants** - Track individual splits for each expense
4. **balances** - Store denormalized user-to-user balances
5. **settlements** - Record payment transactions

### Enhanced Collections
- **expenses** - Added optional fields: `group_id`, `paid_by`, `split_type`, `updated_at`

### Unchanged Collections
- **users** - No changes (fully backward compatible)

## Files Modified/Created

```
1.Backend/
├── db/
│   ├── schema.py           [MODIFIED] - Added new collection schemas
│   ├── client.py           [MODIFIED] - Added new collection references
│   ├── init.py             [MODIFIED] - Enhanced initialization with new collections
│   └── migrations/
│       └── phase1_migration.py [NEW] - Migration script for existing data
└── tests/
    ├── test_phase1_schema.py    [NEW] - Schema validation tests
    └── test_phase1_migration.py [NEW] - Migration tests
```

## Database Schema Details

### Groups Collection

**Purpose:** Store expense groups (both personal and shared)

**Schema:**
```javascript
{
  name: String (required, 1-100 chars),
  description: String (optional, max 500 chars),
  created_by: String (required, user_id),
  is_active: Boolean (default: true),
  group_type: Enum["personal", "shared"] (required),
  created_at: Date (required),
  updated_at: Date (required)
}
```

**Indexes:**
- `idx_created_by` on `created_by`
- `idx_is_active` on `is_active`
- `idx_creator_active` on `(created_by, is_active)`

**Use Cases:**
- Personal groups: Auto-created during migration for existing users
- Shared groups: Created by users for expense sharing (Phase 2)

---

### Group Members Collection

**Purpose:** Track which users belong to which groups

**Schema:**
```javascript
{
  group_id: String (required),
  user_id: String (required),
  role: Enum["admin", "member"] (required),
  is_active: Boolean (default: true),
  joined_at: Date (required),
  left_at: Date (optional)
}
```

**Indexes:**
- `idx_group_user_unique` on `(group_id, user_id)` - **UNIQUE**
- `idx_user` on `user_id`
- `idx_group` on `group_id`
- `idx_group_active` on `(group_id, is_active)`

**Important:** The compound unique index prevents duplicate memberships.

---

### Expense Participants Collection

**Purpose:** Track individual user shares in split expenses

**Schema:**
```javascript
{
  expense_id: String (required),
  user_id: String (required),
  share_amount: Number (required, calculated share),
  share_percentage: Number (optional, for % splits),
  exact_amount: Number (optional, for exact splits),
  created_at: Date (required)
}
```

**Indexes:**
- `idx_expense_user_unique` on `(expense_id, user_id)` - **UNIQUE**
- `idx_expense` on `expense_id`
- `idx_user` on `user_id`

**Note:** Personal expenses (split_type='none') don't have participant records.

---

### Balances Collection

**Purpose:** Denormalized balance tracking for fast lookups

**Schema:**
```javascript
{
  group_id: String (required),
  from_user_id: String (required, who owes),
  to_user_id: String (required, who is owed),
  amount: Number (required, net balance),
  updated_at: Date (required)
}
```

**Indexes:**
- `idx_group_from_to_unique` on `(group_id, from_user_id, to_user_id)` - **UNIQUE**
- `idx_group` on `group_id`
- `idx_group_from` on `(group_id, from_user_id)`
- `idx_group_to` on `(group_id, to_user_id)`

**Design Decision:** Denormalized for O(1) balance lookups vs O(n) aggregation.

---

### Settlements Collection

**Purpose:** Audit trail of payment transactions

**Schema:**
```javascript
{
  group_id: String (required),
  paid_by: String (required, payer user_id),
  paid_to: String (required, recipient user_id),
  amount: Number (required),
  note: String (optional, max 500 chars),
  settled_at: Date (required),
  created_at: Date (required)
}
```

**Indexes:**
- `idx_group_settled` on `(group_id, settled_at DESC)`
- `idx_paid_by` on `paid_by`
- `idx_paid_to` on `paid_to`
- `idx_group_payer_payee` on `(group_id, paid_by, paid_to)`

---

### Enhanced Expenses Collection

**New Optional Fields:**
- `group_id` (String) - Group this expense belongs to
- `paid_by` (String) - User who paid (defaults to user_id for backward compat)
- `split_type` (Enum) - "equal" | "exact" | "percentage" | "none"
- `updated_at` (Date) - Last modification timestamp

**New Indexes:**
- `idx_group_date` on `(group_id, date DESC)`
- `idx_group_paidby` on `(group_id, paid_by)`
- `idx_paidby` on `paid_by`

**Backward Compatibility:** Existing indexes and queries remain unchanged.

---

## Migration Script

### What It Does

The migration script (`phase1_migration.py`) performs the following:

1. **Creates Personal Groups**
   - For each existing user, creates a "Personal" group
   - Sets `group_type="personal"` for identification
   - Makes the user an admin of their Personal group

2. **Migrates Expenses**
   - Finds all expenses without `group_id`
   - Assigns them to the user's Personal group
   - Sets `paid_by = user_id`
   - Sets `split_type = "none"` (personal expenses)
   - Adds `updated_at` timestamp

3. **Creates Group Memberships**
   - Each user is automatically added to their Personal group

4. **Verification**
   - Confirms all expenses have `group_id`
   - Reports migration statistics

### How to Run

```bash
# Navigate to backend directory
cd 1.Backend

# Run migration
python db/migrations/phase1_migration.py

# Run with rollback (removes all migration changes)
python db/migrations/phase1_migration.py --rollback
```

### Migration Output Example

```
======================================================================
PHASE 1 MIGRATION: Migrate Expenses to Group-Based Model
======================================================================
Found 3 users in database

--- Processing user: alice@example.com ---
Created Personal group 67abc123... for user alice@example.com
Added user alice@example.com as admin of Personal group
Migrated 15 expenses for user alice@example.com to group 67abc123...

--- Processing user: bob@example.com ---
Created Personal group 67def456... for user bob@example.com
Added user bob@example.com as admin of Personal group
Migrated 23 expenses for user bob@example.com to group 67def456...

======================================================================
MIGRATION SUMMARY
======================================================================
Total users processed: 3
Total expenses migrated: 52

=== Verifying Migration ===
Total groups: 3
Personal groups: 3
Total group members: 3
=== Migration Verification Complete ===

✓ MIGRATION COMPLETED SUCCESSFULLY
```

### Safety Features

- **Idempotent:** Can be run multiple times safely
- **Non-destructive:** Only adds fields, never removes data
- **Rollback support:** Can undo changes if needed
- **Verification:** Built-in checks after migration

---

## Testing

### Running Schema Tests

```bash
# Using pytest (recommended)
cd 1.Backend
pytest tests/test_phase1_schema.py -v

# Or run directly
python tests/test_phase1_schema.py
```

**Tests cover:**
- ✓ All collections created
- ✓ All indexes exist with correct properties
- ✓ Unique constraints work
- ✓ Schema validation accepts valid documents
- ✓ Backward compatible expense format still works

### Running Migration Tests

```bash
# Using pytest
pytest tests/test_phase1_migration.py -v
```

**Tests cover:**
- ✓ Personal group creation
- ✓ Expense migration with correct field values
- ✓ Idempotency (running multiple times is safe)
- ✓ Data integrity (original data preserved)
- ✓ Backward compatibility (old queries still work)

---

## Backward Compatibility Guarantees

### Existing Code Continues to Work

**Old-style expense creation:**
```python
# This still works (no group_id required)
expense = {
    "user_id": "user123",
    "date": "2025-01-15",
    "amount": 50.0,
    "category": "food",
    "created_at": datetime.utcnow()
}
await expenses_col.insert_one(expense)
```

**Old-style queries:**
```python
# User expenses (still works)
expenses = await expenses_col.find({"user_id": "user123"}).to_list(None)

# Date range query (still works)
expenses = await expenses_col.find({
    "user_id": "user123",
    "date": {"$gte": "2025-01-01", "$lte": "2025-01-31"}
}).to_list(None)

# Category summary (still works)
pipeline = [
    {"$match": {"user_id": "user123"}},
    {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}
]
```

### Existing MCP Tools Continue to Work

All Phase 0 MCP tools (`add_expense`, `list_expenses`, `summarize`, `delete_expense`) work without modification because:
- They use `user_id` filtering (unchanged)
- New fields are optional
- Queries remain backward compatible

---

## Index Performance

### Query Performance Analysis

**Personal expense queries (existing):**
- Uses `idx_user_date` → O(log n) lookup, same as before ✓

**Group expense queries (new):**
- Uses `idx_group_date` → O(log n) lookup for group expenses ✓

**Balance lookups (new):**
- Uses `idx_group_from_to_unique` → O(1) lookup ✓

**Group membership checks (new):**
- Uses `idx_group_user_unique` → O(1) lookup ✓

---

## Database Initialization

To initialize the database with Phase 1 schema:

```bash
cd 1.Backend

# Option 1: Call setup directly from Python
python -c "import asyncio; from db.init import setup_collection_hybrid; asyncio.run(setup_collection_hybrid())"

# Option 2: Use the existing MCP tool (if available)
# This will be exposed via the setup_database tool in Phase 0

# Option 3: Initialize automatically on server start
# The main.py or server.py should call setup_collection_hybrid() on startup
```

---

## Next Steps (Phase 2)

Phase 1 lays the foundation. Phase 2 will add:

1. **Group Management MCP Tools**
   - `create_group`
   - `add_group_member`
   - `list_groups`
   - `get_group_details`

2. **Enhanced Expense Tools**
   - Update `add_expense` to support splits
   - Add participant tracking

3. **Authorization Middleware**
   - Verify group membership before operations

**Phase 1 Status:** ✅ **COMPLETE AND TESTED**

---

## Troubleshooting

### Issue: Migration reports "0 users found"

**Cause:** No users in the database yet.

**Solution:** Create test users first or run migration after users exist.

---

### Issue: "DuplicateKeyError" during migration

**Cause:** Migration was run multiple times and tried to create duplicate group members.

**Solution:** This is expected and safe. The migration is idempotent - duplicate inserts are prevented by unique indexes.

---

### Issue: Old expenses not showing up

**Cause:** Queries might be filtering by `group_id` which old expenses don't have (before migration).

**Solution:** Run the migration script to assign all expenses to Personal groups.

---

### Issue: Schema validation errors

**Cause:** JSON schema validation rejecting documents.

**Solution:** Check that required fields are present. If validation is too strict, modify `validationLevel` in init.py to "moderate" (already set).

---

## Technical Decisions & Rationale

### Why Denormalized Balances?

**Decision:** Store balances in separate collection vs calculating on-the-fly.

**Rationale:**
- Read-heavy workload (users check balances frequently)
- O(1) lookup vs O(n) aggregation over all expenses
- Simplified balance queries
- Trade-off: Slight write complexity accepted for massive read performance gain

### Why Optional group_id in Expenses?

**Decision:** Made `group_id` optional instead of required.

**Rationale:**
- Maintains backward compatibility
- Allows gradual migration
- Old code doesn't break
- Personal groups created during migration

### Why Compound Unique Indexes?

**Decision:** Use `(group_id, user_id)` unique indexes vs single-field indexes.

**Rationale:**
- Prevents duplicate memberships/splits at database level
- Faster than application-level checks
- Atomic constraint enforcement
- Better query performance for compound lookups

---

## Summary

**Phase 1 delivers:**
- ✅ Complete schema for expense sharing
- ✅ All necessary indexes for performance
- ✅ Safe migration script with rollback
- ✅ Comprehensive test suite
- ✅ 100% backward compatibility
- ✅ Production-ready database layer

**Time to complete:** 1-2 days (schema + migration + tests)

**Risk level:** ✅ LOW - No breaking changes, tested thoroughly

**Ready for:** Phase 2 - Group Management Implementation
