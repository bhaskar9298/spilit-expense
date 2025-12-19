# Phase 2 Quick Reference Guide

## Quick Start

```bash
cd D:\expense\expense-tracker-mcp-server\1.Backend

# 1. Restart MCP server (to load new tools)
python server/server.py

# 2. Run tests
pytest tests/test_phase2_groups.py -v

# 3. Test from frontend or Postman
# Use the API examples below
```

---

## New MCP Tools (8 Total)

### Group CRUD (5 tools)

| Tool | Purpose | Admin Only? |
|------|---------|-------------|
| `create_group` | Create new group | No (creator becomes admin) |
| `list_groups` | List user's groups | No |
| `get_group_details` | View group + members | No (must be member) |
| `update_group` | Edit name/description | Yes |
| `delete_group` | Soft delete group | Yes |

### Member Management (3 tools)

| Tool | Purpose | Admin Only? |
|------|---------|-------------|
| `add_group_member` | Invite user by email | Yes |
| `remove_group_member` | Remove member | Yes |
| `leave_group` | Leave a group | No |
| `get_group_members` | List all members | No (must be member) |

---

## Common Operations

### 1. Create a Group

```javascript
POST /mcp/execute
{
  "tool": "create_group",
  "args": {
    "name": "Weekend Trip",
    "description": "Vacation expenses"
  }
}
```

### 2. Add Member

```javascript
POST /mcp/execute
{
  "tool": "add_group_member",
  "args": {
    "group_id": "67abc123...",
    "member_email": "friend@example.com",
    "role": "member"  // or "admin"
  }
}
```

### 3. View Group

```javascript
POST /mcp/execute
{
  "tool": "get_group_details",
  "args": {
    "group_id": "67abc123..."
  }
}
```

### 4. List My Groups

```javascript
POST /mcp/execute
{
  "tool": "list_groups",
  "args": {}
}
```

---

## Authorization Quick Check

```python
from server.utils.authorization import *

# Check if user is in group
is_member = await is_user_in_group(user_id, group_id)

# Check if user is admin
is_admin = await is_user_group_admin(user_id, group_id)

# Find user by email
user = await get_user_by_email("user@example.com")

# Count members
count = await get_group_member_count(group_id)
```

---

## Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Invalid group ID format" | Bad ObjectId | Check group_id is valid |
| "Access denied: You are not a member" | Not in group | Need to be added first |
| "Only admins can..." | Need admin role | Get promoted by admin |
| "User with email '...' not found" | User doesn't exist | User must sign up first |
| "User is already a member" | Duplicate add | User already in group |
| "Cannot remove the last admin" | Last admin protection | Promote someone else first |
| "Cannot leave personal groups" | Personal group restriction | Personal groups are permanent |

---

## Testing Checklist

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run Phase 2 tests
pytest tests/test_phase2_groups.py -v

# Expected: 16 tests pass
```

**Test Coverage:**
- ✓ Authorization (5 tests)
- ✓ Group CRUD (4 tests)  
- ✓ Member management (4 tests)
- ✓ Edge cases (3 tests)

---

## Key Features

### ✅ Implemented

1. **Group Creation**
   - Shared groups only (personal groups via migration)
   - Creator auto-becomes admin
   - Name validation (1-100 chars)

2. **Member Management**
   - Add by email
   - Assign roles (admin/member)
   - Remove members (admins only)
   - Leave groups

3. **Authorization**
   - Membership checks
   - Role-based permissions
   - Admin-only operations

4. **Safety Features**
   - Last admin protection
   - Duplicate prevention
   - Soft deletes (history preserved)
   - Personal group protection

---

## Files Changed

```
server/
├── server.py               [MODIFIED] +600 lines
└── utils/
    ├── __init__.py         [NEW]
    └── authorization.py    [NEW] 200 lines

tests/
└── test_phase2_groups.py   [NEW] 550 lines
```

**Total New Code:** ~750 lines

---

## Integration Points

### With Phase 1
- Uses `groups` collection
- Uses `group_members` collection
- Leverages Phase 1 indexes
- Follows Phase 1 schema

### With Phase 0
- JWT auth unchanged
- User system unchanged
- All Phase 0 tools still work

---

## Next Phase Preview

**Phase 3: Multi-User Expense Splitting**

Coming features:
```javascript
// Add expense to group with splits
{
  "tool": "add_group_expense",
  "args": {
    "group_id": "67abc...",
    "amount": 90.00,
    "description": "Dinner",
    "split_type": "equal",
    "participants": ["user1", "user2", "user3"]
  }
}
```

---

## Quick Troubleshooting

### Can't add member?
→ Check you're admin: `get_group_details`

### Can't see group?
→ Check you're member: `list_groups`

### Can't update group?
→ Only admins can update

### Tests failing?
→ Check MongoDB connection  
→ Ensure Phase 1 collections exist

---

## Commands Reference

```bash
# Start server
python server/server.py

# Run tests
pytest tests/test_phase2_groups.py -v

# Check imports
python -c "from server.utils import is_user_in_group; print('OK')"

# Test authorization
python -c "
import asyncio
from server.utils.authorization import is_user_in_group
async def test():
    result = await is_user_in_group('user1', 'group1')
    print(f'Result: {result}')
asyncio.run(test())
"
```

---

## Interview Talking Points

**"Why separate authorization module?"**
> "I separated authorization logic from MCP tools for reusability and testing. The same permission checks are used across multiple tools, and having them in one place ensures consistency."

**"How do you prevent duplicate members?"**
> "MongoDB's compound unique index on (group_id, user_id) prevents duplicates at the database level. This is more reliable than application-level checks and handles race conditions."

**"Why soft delete?"**
> "Soft deletes preserve audit history and allow for recovery if needed. We mark groups/members as inactive rather than deleting, maintaining referential integrity for historical expense data."

**"How do you handle the last admin problem?"**
> "Before removing an admin, we count active admins. If they're the last one, the operation fails with a clear error. This ensures every group always has at least one admin."

---

## Status

**Phase 2:** ✅ COMPLETE  
**Tests:** ✅ 16/16 PASSING  
**Backward Compatible:** ✅ YES  
**Ready for Phase 3:** ✅ YES

---

*Updated: December 18, 2025*
