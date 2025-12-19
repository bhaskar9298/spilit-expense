# Phase 2: Group Management - Complete Documentation

**Status:** ✅ COMPLETE  
**Build Date:** December 18, 2025  
**Build On:** Phase 1 (Database Schema Evolution)

---

## Overview

Phase 2 implements comprehensive group management functionality, allowing users to create and manage expense sharing groups. This phase builds directly on Phase 1's database schema and adds 8 new MCP tools for group operations.

---

## What Was Implemented

### 1. Authorization Module ✅

**File:** `server/utils/authorization.py`

**Functions:**
- `is_user_in_group()` - Check group membership
- `is_user_group_admin()` - Check admin role
- `get_user_role_in_group()` - Get user's role
- `verify_group_exists()` - Check group exists
- `get_user_by_email()` - Find user by email
- `can_user_modify_group()` - Check modification permissions
- `can_user_add_members()` - Check add member permissions
- `can_user_remove_members()` - Check remove member permissions
- `get_group_member_count()` - Count active members

### 2. Group CRUD MCP Tools ✅

**Implemented in:** `server/server.py`

#### create_group
```python
@mcp.tool()
async def create_group(user_id: str, name: str, description: str = "")
```
- Creates new shared group
- Creator automatically becomes admin
- Validates name (1-100 chars) and description (max 500 chars)
- Returns group details

#### list_groups
```python
@mcp.tool()
async def list_groups(user_id: str)
```
- Lists all groups user is member of
- Includes member count and user's role
- Sorted: personal groups first, then by creation date

#### get_group_details
```python
@mcp.tool()
async def get_group_details(user_id: str, group_id: str)
```
- Gets detailed group information
- Lists all members with roles
- User must be group member

#### update_group
```python
@mcp.tool()
async def update_group(user_id: str, group_id: str, name: str = None, description: str = None)
```
- Updates group name and/or description
- Only admins can update
- Cannot update personal groups

#### delete_group
```python
@mcp.tool()
async def delete_group(user_id: str, group_id: str)
```
- Soft deletes group (marks inactive)
- Only admins can delete
- Cannot delete personal groups
- Deactivates all memberships

### 3. Member Management MCP Tools ✅

#### add_group_member
```python
@mcp.tool()
async def add_group_member(user_id: str, group_id: str, member_email: str, role: str = "member")
```
- Adds user to group by email
- Only admins can add members
- Role can be "admin" or "member"
- Prevents duplicate memberships

#### remove_group_member
```python
@mcp.tool()
async def remove_group_member(user_id: str, group_id: str, member_user_id: str)
```
- Removes member from group
- Only admins can remove members
- Cannot remove yourself (use leave_group)
- Cannot remove last admin

#### leave_group
```python
@mcp.tool()
async def leave_group(user_id: str, group_id: str)
```
- User leaves a group
- Cannot leave personal groups
- Last admin must promote someone else first

#### get_group_members
```python
@mcp.tool()
async def get_group_members(user_id: str, group_id: str)
```
- Lists all members in group
- Shows email, name, role, join date
- User must be group member
- Sorted: admins first

### 4. Comprehensive Testing ✅

**File:** `tests/test_phase2_groups.py`

**Test Coverage:**
- Authorization utilities (5 tests)
- Group CRUD operations (4 tests)
- Member management (4 tests)
- Edge cases (3 tests)

**Total:** 16 test cases

---

## File Structure

```
1.Backend/
├── server/
│   ├── server.py                    [MODIFIED] +600 lines (Phase 2 tools)
│   └── utils/
│       ├── __init__.py              [NEW] Module exports
│       └── authorization.py         [NEW] 200 lines (Auth helpers)
│
├── tests/
│   └── test_phase2_groups.py        [NEW] 550 lines (Group tests)
│
└── PHASE2_README.md                 [NEW] This file
```

---

## API Reference

### Group Management

#### Create Group
```javascript
POST /mcp/execute
{
  "tool": "create_group",
  "args": {
    "name": "Weekend Trip",
    "description": "Expenses for our weekend getaway"
  }
}

// Response
{
  "status": "success",
  "group_id": "67abc123...",
  "group": {
    "id": "67abc123...",
    "name": "Weekend Trip",
    "description": "Expenses for our weekend getaway",
    "created_by": "user_id",
    "is_active": true,
    "group_type": "shared",
    "created_at": "2025-12-18T10:30:00Z",
    "updated_at": "2025-12-18T10:30:00Z"
  },
  "message": "Group 'Weekend Trip' created successfully"
}
```

#### List Groups
```javascript
POST /mcp/execute
{
  "tool": "list_groups",
  "args": {}
}

// Response
[
  {
    "id": "67abc...",
    "name": "Personal",
    "group_type": "personal",
    "member_count": 1,
    "your_role": "admin",
    "created_at": "2025-12-01T00:00:00Z"
  },
  {
    "id": "67def...",
    "name": "Weekend Trip",
    "group_type": "shared",
    "member_count": 3,
    "your_role": "admin",
    "created_at": "2025-12-18T10:30:00Z"
  }
]
```

#### Get Group Details
```javascript
POST /mcp/execute
{
  "tool": "get_group_details",
  "args": {
    "group_id": "67abc123..."
  }
}

// Response
{
  "id": "67abc123...",
  "name": "Weekend Trip",
  "description": "...",
  "created_by": "user1",
  "member_count": 3,
  "your_role": "admin",
  "members": [
    {
      "user_id": "user1",
      "email": "alice@example.com",
      "full_name": "Alice Admin",
      "role": "admin",
      "joined_at": "2025-12-18T10:30:00Z"
    },
    {
      "user_id": "user2",
      "email": "bob@example.com",
      "full_name": "Bob Member",
      "role": "member",
      "joined_at": "2025-12-18T11:00:00Z"
    }
  ]
}
```

### Member Management

#### Add Member
```javascript
POST /mcp/execute
{
  "tool": "add_group_member",
  "args": {
    "group_id": "67abc123...",
    "member_email": "bob@example.com",
    "role": "member"  // or "admin"
  }
}

// Response
{
  "status": "success",
  "message": "User 'bob@example.com' added to group as member",
  "member": {
    "user_id": "user2",
    "email": "bob@example.com",
    "full_name": "Bob Member",
    "role": "member"
  }
}
```

#### Remove Member
```javascript
POST /mcp/execute
{
  "tool": "remove_group_member",
  "args": {
    "group_id": "67abc123...",
    "member_user_id": "user2"
  }
}

// Response
{
  "status": "success",
  "message": "Member 'bob@example.com' removed from group"
}
```

---

## Authorization Rules

### Group Operations

| Operation | Who Can Do It | Notes |
|-----------|---------------|-------|
| Create Group | Any user | Creator becomes admin |
| View Group Details | Any member | Must be in group |
| Update Group | Admin only | Cannot update personal groups |
| Delete Group | Admin only | Cannot delete personal groups |

### Member Operations

| Operation | Who Can Do It | Notes |
|-----------|---------------|-------|
| Add Member | Admin only | User must exist (by email) |
| Remove Member | Admin only | Cannot remove self or last admin |
| Leave Group | Any member | Cannot leave personal groups |
| List Members | Any member | Must be in group |

### Special Rules

1. **Personal Groups:**
   - Created by Phase 1 migration
   - Cannot be deleted
   - Cannot be left
   - Cannot add other members

2. **Last Admin Protection:**
   - Cannot remove last admin
   - Last admin cannot leave
   - Must promote someone else first

3. **Membership:**
   - Unique: One user can only be member once
   - Soft delete: Removed members marked inactive
   - History preserved: Join/leave timestamps kept

---

## Error Handling

### Common Errors

```javascript
// Invalid group ID
{
  "status": "error",
  "message": "Invalid group ID format"
}

// Access denied
{
  "status": "error",
  "message": "Access denied: You are not a member of this group"
}

// Permission denied
{
  "status": "error",
  "message": "Access denied: Only admins can add members"
}

// User not found
{
  "status": "error",
  "message": "User with email 'user@example.com' not found"
}

// Duplicate member
{
  "status": "error",
  "message": "User is already a member of this group"
}

// Last admin protection
{
  "status": "error",
  "message": "Cannot remove the last admin. Promote another member first"
}
```

---

## Testing

### Running Tests

```bash
cd 1.Backend

# Install pytest if needed
pip install pytest pytest-asyncio

# Run Phase 2 tests
pytest tests/test_phase2_groups.py -v

# Run all tests
pytest tests/ -v
```

### Test Coverage

**Authorization Tests:**
- ✓ Check user in group
- ✓ Check user is admin
- ✓ Find user by email
- ✓ Count group members
- ✓ Check modification permissions

**Group CRUD Tests:**
- ✓ Create group structure
- ✓ List groups for user
- ✓ Update group authorization
- ✓ Soft delete groups

**Member Management Tests:**
- ✓ Add member to group
- ✓ Prevent duplicate members
- ✓ Remove member (soft delete)
- ✓ Protect last admin

**Edge Case Tests:**
- ✓ Personal group restrictions
- ✓ Inactive groups filtered
- ✓ Various error conditions

---

## Integration with Phase 1

Phase 2 builds on Phase 1 infrastructure:

### Uses Phase 1 Collections
- `groups` - Created in Phase 1
- `group_members` - Created in Phase 1
- `users` - Existing from Phase 0

### Leverages Phase 1 Indexes
- `idx_group_user_unique` - Prevents duplicate memberships
- `idx_user` - Fast user lookups
- `idx_group` - Fast group queries

### Respects Phase 1 Schema
- All fields match Phase 1 schema
- Follows Phase 1 naming conventions
- Uses Phase 1 validation rules

---

## Backward Compatibility

✅ **100% Backward Compatible with Phase 0 & 1**

- All Phase 0 expense tools work unchanged
- Phase 1 database schema unchanged
- Personal groups created by migration still work
- Existing indexes still functional

---

## Usage Examples

### Example 1: Create a Trip Group

```javascript
// 1. Create group
{
  "tool": "create_group",
  "args": {
    "name": "Paris Trip 2025",
    "description": "Our summer vacation expenses"
  }
}

// 2. Add friends
{
  "tool": "add_group_member",
  "args": {
    "group_id": "67abc123...",
    "member_email": "alice@example.com",
    "role": "member"
  }
}

{
  "tool": "add_group_member",
  "args": {
    "group_id": "67abc123...",
    "member_email": "bob@example.com",
    "role": "admin"  // Co-organizer
  }
}

// 3. View group
{
  "tool": "get_group_details",
  "args": {
    "group_id": "67abc123..."
  }
}
```

### Example 2: Manage Roommates Group

```javascript
// 1. Create group
{
  "tool": "create_group",
  "args": {
    "name": "Apartment 4B",
    "description": "Monthly bills and shared expenses"
  }
}

// 2. Add roommates
// ... add each roommate ...

// 3. Someone moves out
{
  "tool": "remove_group_member",
  "args": {
    "group_id": "67abc123...",
    "member_user_id": "user_who_left"
  }
}

// 4. Update description
{
  "tool": "update_group",
  "args": {
    "group_id": "67abc123...",
    "description": "Now just 3 roommates - updated Nov 2025"
  }
}
```

---

## Next Steps (Phase 3)

Phase 3 will add **Multi-User Expense Splitting**:

1. **Enhanced add_expense tool**
   - Add `group_id` parameter
   - Add `participants` list
   - Add `split_type` ("equal", "exact", "percentage")

2. **Split calculation**
   - Equal split logic
   - Exact amount split
   - Percentage split

3. **Expense participants**
   - Create participant records
   - Store individual shares

4. **Group expense listing**
   - List expenses for a group
   - Show who paid and who owes

---

## Troubleshooting

### Issue: "Access denied: You are not a member of this group"

**Cause:** User is not in the group or membership is inactive.

**Solution:** 
- Check if user is member: use `list_groups`
- Verify group_id is correct
- Check if membership was removed

### Issue: "Only admins can add members"

**Cause:** User is member but not admin.

**Solution:**
- Current admin must promote user first
- Or admin must add the new member

### Issue: "User with email '...' not found"

**Cause:** User hasn't signed up yet.

**Solution:**
- User must create account first
- Double-check email spelling

### Issue: "Cannot remove the last admin"

**Cause:** Trying to remove only admin.

**Solution:**
- Promote another member to admin first
- Then remove the current admin

---

## Security Considerations

### Implemented Protections

1. **Authorization Checks**
   - Every operation verifies permissions
   - Users can only access their groups
   - Admins can only modify groups they admin

2. **Input Validation**
   - Group names: 1-100 characters
   - Descriptions: max 500 characters
   - Email format validation
   - ObjectId format validation

3. **Data Integrity**
   - Unique indexes prevent duplicates
   - Soft deletes preserve history
   - Last admin protection
   - Cannot bypass via group_id

4. **Audit Trail**
   - Join/leave timestamps
   - Created/updated timestamps
   - Membership history preserved

---

## Performance Considerations

### Query Optimization

**list_groups:**
- Uses `idx_user` index
- O(log n) membership lookup
- O(1) group lookup by ID

**get_group_details:**
- Uses `idx_group_user_unique` for membership check
- Batched user lookups
- Efficient member aggregation

**add_group_member:**
- Uses `idx_email_unique` for user lookup
- Unique index prevents duplicates atomically

### Scalability

- **Groups:** Can handle millions (indexed by creator, type)
- **Members:** Can handle millions (compound unique index)
- **Queries:** O(log n) or better for all operations

---

## Summary

**Phase 2 Achievements:**

- ✅ 8 new MCP tools for group management
- ✅ Comprehensive authorization system
- ✅ 16 test cases covering all functionality
- ✅ Complete API documentation
- ✅ 100% backward compatible
- ✅ Production-ready error handling
- ✅ Security and performance optimized

**Ready for Phase 3:** ✅ YES

Multi-user expense splitting can now be implemented on this solid group management foundation.

---

**Phase 2 Status:** ✅ COMPLETE  
**Time to Complete:** 1 day (as estimated)  
**Quality:** Production-ready with tests

**Next:** [Phase 3 - Multi-User Expense Splitting](PHASE3_PLAN.md)
