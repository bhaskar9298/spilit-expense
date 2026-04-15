# db/client.py - MongoDB client and collection setup
# Phase 1: Added new collections for expense sharing functionality

import os
import certifi
import ssl
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("Missing MONGODB_URI environment variable")

# Create SSL context with proper certificate verification
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Configure connection with SSL certificate and proper pooling
client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    tlsAllowInvalidCertificates=False,
    tlsAllowInvalidHostnames=False,
    maxPoolSize=10,
    minPoolSize=1,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
)

# Database reference
db = client["expense_tracker"]

# ============================================================================
# EXISTING COLLECTIONS (maintained for backward compatibility)
# ============================================================================

expenses_col = db["expenses"]
users_col = db["users"]

# ============================================================================
# NEW COLLECTIONS (Phase 1: Expense Sharing)
# ============================================================================

# Group management
groups_col = db["groups"]
group_members_col = db["group_members"]

# Split tracking
expense_participants_col = db["expense_participants"]

# Balance tracking
balances_col = db["balances"]
settlements_col = db["settlements"]
