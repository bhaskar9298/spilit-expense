# Phase 1 Quick Reference

## Quick Start (3 Commands)

```bash
cd 1.Backend

# 1. Initialize schema
python setup_phase1.py

# 2. Verify everything works
python setup_phase1.py --test-only

# 3. Check your database in MongoDB
# You should see 7 collections with indexes
```

---

## Collection Quick Reference

| Collection | Purpose | Key Index | Phase |
|------------|---------|-----------|-------|
| `users` | User accounts | `email` (unique) | 0 |
| `expenses` | All expenses | `(user_id, date)` | 0→1 |
| `groups` | Group entities | `created_by` | 1 |
| `group_members` | Memberships | `(group_id, user_id)` unique | 1 |
| `expense_participants` | Split details | `(expense_id, user_id)` unique | 1 |
| `balances` | Balance cache | `(group_id, from, to)` unique | 1 |
| `settlements` | Payments | `(group_id, settled_at)` | 1 |

---

## Common Queries

### Get user's groups
```python
groups = await group_members_col.find(
    {"user_id": user_id, "is_active": True}
).to_list(None)
```

### Get group expenses
```python
expenses = await expenses_col.find(
    {"group_id": group_id}
).sort("date", -1).to_list(None)
```

### Get user's balance in group
```python
# What user owes
owes = await balances_col.find({
    "group_id": group_id,
    "from_user_id": user_id
}).to_list(None)

# What user is owed
owed = await balances_col.find({
    "group_id": group_id,
    "to_user_id": user_id
}).to_list(None)
```

### Check group membership
```python
is_member = await group_members_col.find_one({
    "group_id": group_id,
    "user_id": user_id,
    "is_active": True
})
```

---

## File Locations

```
1.Backend/
├── db/
│   ├── schema.py              # All collection schemas
│   ├── client.py              # Collection references
│   ├── init.py                # Database initialization
│   └── migrations/
│       └── phase1_migration.py # Data migration script
├── tests/
│   ├── test_phase1_schema.py   # Schema tests
│   └── test_phase1_migration.py # Migration tests
├── PHASE1_README.md            # Full documentation
├── PHASE1_SUMMARY.md           # Implementation summary
└── setup_phase1.py             # Setup automation
```

---

## Troubleshooting

### "Collection not found"
→ Run: `python setup_phase1.py`

### "Index already exists" error
→ Safe to ignore (idempotent)

### "Expenses have no group_id"
→ Run: `python db/migrations/phase1_migration.py`

### Tests failing
→ Check MongoDB connection in `.env`

---

## What Changed vs Phase 0

### Added (New)
- ✅ 5 new collections
- ✅ 19 new indexes
- ✅ Migration script
- ✅ Comprehensive tests

### Modified (Enhanced)
- ✅ expenses schema (optional fields)
- ✅ Database init (new collections)

### Unchanged (Backward Compatible)
- ✅ Users collection
- ✅ Existing MCP tools
- ✅ Authentication system
- ✅ All Phase 0 queries

---

## Phase 2 Preview

Coming next (Group Management):

```python
# New MCP tools in Phase 2:
- create_group(user_id, name, description)
- add_group_member(user_id, group_id, member_email)
- remove_group_member(user_id, group_id, member_id)
- list_groups(user_id)
- get_group_details(user_id, group_id)
- leave_group(user_id, group_id)
```

---

## Key Metrics

- **Collections:** 7 (2 existing + 5 new)
- **Indexes:** 26 (7 existing + 19 new)
- **Lines of Code:** ~2,600 new
- **Test Coverage:** 15 test cases
- **Breaking Changes:** 0
- **Backward Compatible:** ✅ 100%

---

## Commands Reference

```bash
# Setup
python setup_phase1.py                      # Full setup
python setup_phase1.py --skip-migration     # Skip migration
python setup_phase1.py --test-only          # Only tests

# Migration
python db/migrations/phase1_migration.py    # Run migration
python db/migrations/phase1_migration.py --rollback  # Undo migration

# Tests
python tests/test_phase1_schema.py          # Schema tests
pytest tests/test_phase1_migration.py -v    # Migration tests
```

---

## Ready for Interview?

✅ You can now explain:
1. Schema design for expense sharing
2. Denormalized balance strategy
3. Backward compatibility approach
4. Index strategy for performance
5. Migration safety (idempotent)

**Phase 1 Complete! 🎉**
