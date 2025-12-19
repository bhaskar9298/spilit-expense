# Phase 1 Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXPENSE SHARING APPLICATION                  │
│                         (Phase 1 Complete)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   React UI   │  │  Auth Pages  │  │  Dashboard   │         │
│  │  (Phase 0)   │  │   (Phase 0)  │  │  (Phase 0)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (JWT Cookie)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API GATEWAY LAYER                            │
│  ┌──────────────────────────────────────────────────┐           │
│  │           FastAPI Auth Server (main.py)           │           │
│  │  - JWT Authentication                             │           │
│  │  - User Registration/Login                        │           │
│  │  - MCP Request Routing                            │           │
│  │  - User Context Injection (user_id)               │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Internal HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATION LAYER                        │
│  ┌──────────────────────────────────────────────────┐           │
│  │         LangGraph Service (LangGraph)             │           │
│  │  - Natural Language Processing                    │           │
│  │  - Tool Orchestration                             │           │
│  │  - Gemini 2.5 Flash Integration                   │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP SERVER LAYER                            │
│  ┌──────────────────────────────────────────────────┐           │
│  │         FastMCP Server (server.py)                │           │
│  │                                                    │           │
│  │  PHASE 0 TOOLS (Working):                         │           │
│  │    • add_expense(user_id, ...)                    │           │
│  │    • list_expenses(user_id, ...)                  │           │
│  │    • summarize(user_id, ...)                      │           │
│  │    • delete_expense(user_id, ...)                 │           │
│  │                                                    │           │
│  │  PHASE 2 TOOLS (Coming Next):                     │           │
│  │    • create_group(user_id, ...)                   │           │
│  │    • add_group_member(user_id, ...)               │           │
│  │    • list_groups(user_id)                         │           │
│  │    • (Group management tools)                     │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Motor (Async Driver)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│                      MongoDB Atlas                               │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    PHASE 0   │  │   PHASE 1    │  │   PHASE 1    │         │
│  │  Collections │  │  Enhanced    │  │ New Collections│        │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤         │
│  │              │  │              │  │              │         │
│  │ • users      │  │ • expenses   │  │ • groups     │         │
│  │              │  │   (enhanced) │  │ • group_     │         │
│  │              │  │              │  │   members    │         │
│  │              │  │              │  │ • expense_   │         │
│  │              │  │              │  │   participants│        │
│  │              │  │              │  │ • balances   │         │
│  │              │  │              │  │ • settlements│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Add Personal Expense (Phase 0 - Still Works)

```
┌──────────┐
│  User    │  "Add $50 food expense"
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  React Frontend  │  HTTP POST /mcp/execute
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  FastAPI Gateway │  Verify JWT → Extract user_id
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  LangGraph       │  Parse NL → Generate tool call
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  MCP Server      │  add_expense(user_id, amount, category, date)
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  MongoDB         │  Insert into expenses collection
│                  │  {
│                  │    user_id: "...",
│                  │    amount: 50,
│                  │    category: "food",
│                  │    date: "2025-12-18"
│                  │  }
└──────────────────┘
```

---

## Data Flow: Add Shared Expense (Phase 3 - Coming Soon)

```
┌──────────┐
│  User    │  "Split $90 dinner equally with Alice and Bob"
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  React Frontend  │  HTTP POST /mcp/execute
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  FastAPI Gateway │  Verify JWT → Extract user_id
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  LangGraph       │  Parse NL → Generate tool call
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  MCP Server      │  add_expense(
│                  │    user_id,
│                  │    group_id,
│                  │    amount: 90,
│                  │    split_type: "equal",
│                  │    participants: [user_id, alice_id, bob_id]
│                  │  )
└────┬─────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────┐
│  MongoDB - Multi-Collection Transaction              │
│                                                       │
│  1. Insert into expenses:                            │
│     { group_id, paid_by: user_id, amount: 90,        │
│       split_type: "equal" }                          │
│                                                       │
│  2. Insert into expense_participants (3 records):    │
│     { expense_id, user_id: user_id, share: 30 }      │
│     { expense_id, user_id: alice_id, share: 30 }     │
│     { expense_id, user_id: bob_id, share: 30 }       │
│                                                       │
│  3. Update balances (2 records):                     │
│     { from: alice_id, to: user_id, amount: +30 }     │
│     { from: bob_id, to: user_id, amount: +30 }       │
└──────────────────────────────────────────────────────┘
```

---

## Database Schema Relationships (Phase 1)

```
┌─────────────┐
│    users    │
│─────────────│
│ _id (PK)    │◄─────────┐
│ email       │          │
│ password    │          │ created_by
│ full_name   │          │
└─────────────┘          │
       │                 │
       │ user_id         │
       │                 │
       ▼                 │
┌─────────────┐    ┌─────────────┐
│  expenses   │    │   groups    │
│─────────────│    │─────────────│
│ _id (PK)    │    │ _id (PK)    │◄────┐
│ user_id     │    │ name        │     │
│ group_id ───┼───►│ created_by  │     │ group_id
│ paid_by     │    │ group_type  │     │
│ amount      │    │ is_active   │     │
│ split_type  │    └─────────────┘     │
│ date        │           │             │
└─────────────┘           │             │
       │                  │             │
       │ expense_id       │ group_id    │
       │                  │             │
       ▼                  ▼             │
┌──────────────────┐  ┌──────────────────┐
│expense_participants│  │  group_members   │
│──────────────────│  │──────────────────│
│ _id (PK)         │  │ _id (PK)         │
│ expense_id       │  │ group_id ────────┤
│ user_id          │  │ user_id          │
│ share_amount     │  │ role             │
│ share_percentage │  │ is_active        │
└──────────────────┘  └──────────────────┘

                      ┌──────────────────┐
                      │    balances      │
                      │──────────────────│
                      │ _id (PK)         │
                      │ group_id ────────┤
                      │ from_user_id     │
                      │ to_user_id       │
                      │ amount           │
                      └──────────────────┘

                      ┌──────────────────┐
                      │   settlements    │
                      │──────────────────│
                      │ _id (PK)         │
                      │ group_id ────────┤
                      │ paid_by          │
                      │ paid_to          │
                      │ amount           │
                      │ settled_at       │
                      └──────────────────┘
```

---

## Index Strategy (Phase 1)

### Query Pattern → Index Mapping

```
Query: "Get my groups"
├─ Collection: group_members
├─ Filter: { user_id: "..." }
└─ Index: idx_user → O(log n)

Query: "Get group expenses"
├─ Collection: expenses
├─ Filter: { group_id: "...", date: {$gte: ...} }
└─ Index: idx_group_date → O(log n)

Query: "Check if user in group"
├─ Collection: group_members
├─ Filter: { group_id: "...", user_id: "..." }
└─ Index: idx_group_user_unique → O(1)

Query: "Get user's balance"
├─ Collection: balances
├─ Filter: { group_id: "...", from_user_id: "..." }
└─ Index: idx_group_from → O(log n)

Query: "Get expense splits"
├─ Collection: expense_participants
├─ Filter: { expense_id: "..." }
└─ Index: idx_expense → O(log n)
```

---

## Migration Flow (Phase 1)

```
BEFORE MIGRATION:
┌─────────────┐
│  expenses   │
│─────────────│
│ user_id     │  ← Isolated by user
│ date        │
│ amount      │
│ category    │
└─────────────┘

MIGRATION PROCESS:
Step 1: Create Personal Groups
  ┌─────────────┐
  │   groups    │
  │─────────────│
  │ name: "Personal"     │  ← One per user
  │ group_type: "personal" │
  │ created_by: user_id  │
  └─────────────┘

Step 2: Create Memberships
  ┌──────────────────┐
  │  group_members   │
  │──────────────────│
  │ group_id: personal_group │  ← User is admin
  │ user_id: user_id         │
  │ role: "admin"            │
  └──────────────────┘

Step 3: Migrate Expenses
  ┌─────────────┐
  │  expenses   │
  │─────────────│
  │ user_id     │  ← Unchanged
  │ group_id    │  ← NEW: personal_group
  │ paid_by     │  ← NEW: user_id
  │ split_type  │  ← NEW: "none"
  │ date        │
  │ amount      │
  │ category    │
  └─────────────┘

AFTER MIGRATION:
Everything in a group (unified model)
✓ Backward compatible (user_id still works)
✓ Ready for shared expenses (group_id exists)
```

---

## Authentication Flow (Phase 0 - Unchanged)

```
┌──────────┐
│  User    │  Login with email/password
└────┬─────┘
     │
     ▼
┌──────────────────┐
│  FastAPI         │  POST /auth/login
│  main.py         │  1. Verify password (bcrypt)
│                  │  2. Generate JWT
│                  │  3. Set HttpOnly cookie
└────┬─────────────┘
     │
     │  Set-Cookie: access_token=<JWT>
     │  HttpOnly, Secure, SameSite=None
     ▼
┌──────────────────┐
│  Frontend        │  Cookie stored automatically
│  (All requests   │  Sent with every request
│   include cookie)│
└──────────────────┘

Subsequent Requests:
┌──────────┐
│  User    │  Makes any API call
└────┬─────┘
     │  Cookie: access_token=<JWT>
     ▼
┌──────────────────┐
│  FastAPI         │  get_current_user dependency:
│                  │  1. Extract cookie
│                  │  2. Verify JWT
│                  │  3. Extract user_id
│                  │  4. Inject into request
└────┬─────────────┘
     │  user_id injected
     ▼
┌──────────────────┐
│  MCP Tools       │  All tools receive user_id
│                  │  No need to pass explicitly
└──────────────────┘
```

---

## Phase Progression Roadmap

```
PHASE 0 (Completed)                 PHASE 1 (Completed)
┌─────────────────┐                ┌─────────────────┐
│ • Users          │                │ • Enhanced DB    │
│ • Auth (JWT)     │───────────────►│ • 5 New Collections│
│ • Personal       │                │ • Migration      │
│   Expenses       │                │ • Tests          │
└─────────────────┘                └─────────────────┘
                                           │
                                           │
PHASE 2 (Next: Week 2)                    │
┌─────────────────┐                       │
│ • Group APIs     │◄──────────────────────┘
│ • Member Mgmt    │
│ • Authorization  │
└─────────────────┘
        │
        │
PHASE 3 (Week 3)
┌─────────────────┐
│ • Split Expenses │
│ • 3 Split Types  │
│ • Participants   │
└─────────────────┘
        │
        │
PHASE 4 (Week 4)
┌─────────────────┐
│ • Balance Calc   │
│ • Balance View   │
│ • Settlements    │
└─────────────────┘
        │
        │
PHASE 5 (Week 5)
┌─────────────────┐
│ • Simplification │
│ • Graph Algorithm│
│ • Min Transactions│
└─────────────────┘
```

---

## Key Architectural Decisions

### 1. Denormalized Balances
```
Option A (Rejected): Calculate on-the-fly
  expenses → aggregate → balances
  ❌ O(n) time for each balance query
  ❌ Slow for large expense histories

Option B (Chosen): Denormalized table
  expenses → update balance record
  ✅ O(1) time for balance queries
  ✅ Fast even with millions of expenses
  ⚠️ Must update on every expense/settlement
```

### 2. Group-Based Model
```
Option A (Rejected): Expenses have participants
  expenses.participants: [user1, user2, ...]
  ❌ No structure for non-expense group activities
  ❌ Hard to add group features later

Option B (Chosen): Everything in groups
  expenses → belong to groups
  ✅ Unified model (personal = 1-person group)
  ✅ Easy to add group chat, files, etc.
  ✅ Natural authorization (group membership)
```

### 3. Migration Strategy
```
Option A (Rejected): Require manual re-entry
  ❌ User friction
  ❌ Data loss risk

Option B (Chosen): Automatic migration
  ✅ Zero user impact
  ✅ Preserves all data
  ✅ Creates Personal groups automatically
```

---

**Phase 1 Architecture: ✅ COMPLETE**

Next: [Phase 2 - Group Management](PHASE2_PLAN.md)
