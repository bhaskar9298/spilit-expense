# db/schema.py - Enhanced JSON Schema for Expense Sharing Application
# Phase 1: Added schemas for groups, group_members, expense_participants, balances, settlements

# ============================================================================
# EXISTING SCHEMAS (Maintained for backward compatibility)
# ============================================================================

user_json_schema = {
    "bsonType": "object",
    "required": ["email", "password_hash"],
    "properties": {
        "email": {
            "bsonType": "string",
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "description": "User email (unique)"
        },
        "password_hash": {
            "bsonType": "string",
            "description": "Bcrypt hashed password"
        },
        "full_name": {
            "bsonType": "string",
            "description": "User's full name"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Account creation timestamp"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Last update timestamp"
        }
    }
}

# ============================================================================
# ENHANCED EXPENSE SCHEMA (Phase 1: Added group_id, split_type, paid_by)
# ============================================================================

expense_json_schema = {
    "bsonType": "object",
    "required": ["user_id", "date", "amount", "category"],  # Kept for backward compatibility
    "properties": {
        "user_id": {
            "bsonType": "string",
            "description": "User ID from JWT - isolates user data (kept for backward compatibility)"
        },
        "group_id": {
            "bsonType": "string",
            "description": "Group ID - expenses belong to a group (optional for migration compatibility)"
        },
        "paid_by": {
            "bsonType": "string",
            "description": "User ID who paid for this expense (defaults to user_id for backward compatibility)"
        },
        "date": {
            "bsonType": "string",
            "description": "Date string (prefer ISO format YYYY-MM-DD)"
        },
        "amount": {
            "bsonType": ["double", "int", "decimal"],
            "description": "Total expense amount"
        },
        "category": {
            "bsonType": "string",
            "description": "Expense category"
        },
        "subcategory": {
            "bsonType": "string",
            "description": "Optional subcategory"
        },
        "note": {
            "bsonType": "string",
            "description": "Optional note/description"
        },
        "split_type": {
            "bsonType": "string",
            "enum": ["equal", "exact", "percentage", "none"],
            "description": "How the expense is split: equal, exact, percentage, or none (personal expense)"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Auto-added timestamp"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Last update timestamp"
        }
    },
    "additionalProperties": True
}

# ============================================================================
# NEW SCHEMAS (Phase 1: Group Management)
# ============================================================================

group_json_schema = {
    "bsonType": "object",
    "required": ["name", "created_by", "created_at"],
    "properties": {
        "name": {
            "bsonType": "string",
            "description": "Group name",
            "minLength": 1,
            "maxLength": 100
        },
        "description": {
            "bsonType": "string",
            "description": "Optional group description",
            "maxLength": 500
        },
        "created_by": {
            "bsonType": "string",
            "description": "User ID of group creator"
        },
        "is_active": {
            "bsonType": "bool",
            "description": "Whether group is active (for soft deletes)"
        },
        "group_type": {
            "bsonType": "string",
            "enum": ["personal", "shared"],
            "description": "Type: 'personal' for single-user groups (migration), 'shared' for multi-user"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Group creation timestamp"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Last update timestamp"
        }
    },
    "additionalProperties": True
}

group_member_json_schema = {
    "bsonType": "object",
    "required": ["group_id", "user_id", "joined_at"],
    "properties": {
        "group_id": {
            "bsonType": "string",
            "description": "Reference to group"
        },
        "user_id": {
            "bsonType": "string",
            "description": "Reference to user"
        },
        "role": {
            "bsonType": "string",
            "enum": ["admin", "member"],
            "description": "User role in group: admin (can manage group) or member"
        },
        "is_active": {
            "bsonType": "bool",
            "description": "Whether membership is active (for soft deletes)"
        },
        "joined_at": {
            "bsonType": "date",
            "description": "When user joined the group"
        },
        "left_at": {
            "bsonType": "date",
            "description": "When user left the group (null if active)"
        }
    },
    "additionalProperties": True
}

# ============================================================================
# NEW SCHEMAS (Phase 1: Split Management)
# ============================================================================

expense_participant_json_schema = {
    "bsonType": "object",
    "required": ["expense_id", "user_id", "share_amount"],
    "properties": {
        "expense_id": {
            "bsonType": "string",
            "description": "Reference to expense"
        },
        "user_id": {
            "bsonType": "string",
            "description": "Reference to user participating in expense"
        },
        "share_amount": {
            "bsonType": ["double", "decimal"],
            "description": "Calculated amount this user owes (after split calculation)"
        },
        "share_percentage": {
            "bsonType": "double",
            "description": "Percentage share (for percentage-based splits)"
        },
        "exact_amount": {
            "bsonType": ["double", "decimal"],
            "description": "Exact amount specified (for exact splits)"
        },
        "created_at": {
            "bsonType": "date",
            "description": "When participant was added"
        }
    },
    "additionalProperties": True
}

# ============================================================================
# NEW SCHEMAS (Phase 1: Balance Tracking)
# ============================================================================

balance_json_schema = {
    "bsonType": "object",
    "required": ["group_id", "from_user_id", "to_user_id", "amount", "updated_at"],
    "properties": {
        "group_id": {
            "bsonType": "string",
            "description": "Reference to group"
        },
        "from_user_id": {
            "bsonType": "string",
            "description": "User ID who owes money"
        },
        "to_user_id": {
            "bsonType": "string",
            "description": "User ID who is owed money"
        },
        "amount": {
            "bsonType": ["double", "decimal"],
            "description": "Net balance amount (positive = from_user owes to_user)"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Last balance update timestamp"
        }
    },
    "additionalProperties": True
}

settlement_json_schema = {
    "bsonType": "object",
    "required": ["group_id", "paid_by", "paid_to", "amount", "settled_at"],
    "properties": {
        "group_id": {
            "bsonType": "string",
            "description": "Reference to group"
        },
        "paid_by": {
            "bsonType": "string",
            "description": "User ID who made the payment"
        },
        "paid_to": {
            "bsonType": "string",
            "description": "User ID who received the payment"
        },
        "amount": {
            "bsonType": ["double", "decimal"],
            "description": "Settlement amount"
        },
        "note": {
            "bsonType": "string",
            "description": "Optional payment note",
            "maxLength": 500
        },
        "settled_at": {
            "bsonType": "date",
            "description": "When the settlement occurred"
        },
        "created_at": {
            "bsonType": "date",
            "description": "Record creation timestamp"
        }
    },
    "additionalProperties": True
}

# ============================================================================
# SCHEMA REGISTRY (for easy access in init.py)
# ============================================================================

COLLECTION_SCHEMAS = {
    "users": user_json_schema,
    "expenses": expense_json_schema,
    "groups": group_json_schema,
    "group_members": group_member_json_schema,
    "expense_participants": expense_participant_json_schema,
    "balances": balance_json_schema,
    "settlements": settlement_json_schema
}
