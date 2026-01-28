# MongoDB Migration Guide

## Overview
The application has been successfully migrated from JSON file-based storage to MongoDB. All data operations now use MongoDB collections instead of JSON files.

## Changes Made

### 1. **Database Layer** (`database.py`)
- Implemented `MongoDB` class with connection to MongoDB Atlas
- Created all necessary collections with proper indexing
- Added helper methods:
  - `find_all()` - Retrieve all documents
  - `find_one()` - Find single document
  - `find_many()` - Find multiple documents
  - `insert_one()` - Insert single document
  - `insert_many()` - Insert multiple documents
  - `update_one()` - Update single document
  - `replace_one()` - Replace entire document
  - `delete_one()` - Delete single document
  - `delete_many()` - Delete multiple documents
  - `count_documents()` - Count documents with query

### 2. **Models** (`models.py`)
- All data models moved to `models.py` with proper Pydantic definitions
- All 17 collections have proper type definitions:
  - `events`, `news`, `code_challenges`, `hackathons`, `roadmaps`
  - `domains`, `stats`, `meetups`, `broadcasts`, `feedback`
  - `team_finder`, `users`, `core_members`, `volunteers`
  - `progress`, `tickets`, `checkins`

### 3. **API Layer** (`main.py`)
- Removed all JSON file operations (`load_data`, `save_data`, `load_team`, `save_team`)
- All endpoints now use MongoDB collections via `db` instance
- No more global in-memory lists
- Added startup event to initialize default data

## Collections & Schema

### Core Collections
```
events              - Event information and registrations
news                - News/blog articles
code_challenges     - Coding problems and questions
hackathons          - Hackathon details
roadmaps            - Learning roadmaps

domains             - Technology domains
stats               - Dynamic statistics
meetups             - Meetup information
broadcasts          - System broadcasts/announcements
feedback            - User feedback and ratings

team_finder         - Team formation posts
users               - User accounts and profiles
core_members        - Core team members
volunteers          - Volunteer registrations
progress            - User learning progress
tickets             - Event registration tickets
checkins            - Event attendance check-ins
```

## Migration Process

### Step 1: Initial Setup
When the application starts for the first time:

```python
# Automatically runs on startup
@app.on_event("startup")
async def startup_event():
    migrate_from_json()  # Migrates JSON data to MongoDB
```

### Step 2: Manual Migration (Optional)
If you need to migrate data manually, run:

```bash
python migrate.py
```

This script:
- Checks each JSON file
- Skips collections that already have data
- Handles special cases (e.g., progress.json structure)
- Provides detailed migration report

### Step 3: Verification
The startup event also:
- Creates default admin user if it doesn't exist
- Creates default core members if needed
- Initializes all collections

## Database Connection

**MongoDB Atlas Connection String:**
```
mongodb+srv://alfredsam2006_db_user:3ncbTinBSgTKAg0J@cluster0.o6fg583.mongodb.net/?appName=Cluster0
```

**Database Name:** `IntellexaDB`

## Indexes Created

For optimal performance, the following indexes are automatically created:

- `events.id` - Indexed for fast event lookup
- `users.username` - Unique index for user authentication
- `users.email` - Unique index for email validation
- `progress.userId` - Unique index for user progress lookup
- `tickets.userId`, `tickets.eventId` - Composite search
- `checkins.eventId`, `checkins.studentId` - Attendance tracking

## API Endpoints - No Changes
All API endpoints remain the same. The change is transparent to the frontend:

- `GET /api/events` - Fetch all events
- `POST /api/events` - Create new event
- `GET /api/users/{user_id}` - Fetch user
- `POST /api/login` - User authentication
- etc.

## Data Relationships

### Event Flow
```
User Registration
    ↓
Create Ticket (tickets collection)
    ↓
Event Check-in (checkins collection)
    ↓
Update User Progress (progress collection)
```

### Admin Operations
- Track stats: `db.count_documents("users")`
- Get attendance: `db.find_many("checkins", {"eventId": id})`
- User management: `db.update_one("users", {"id": id}, {...})`

## Backward Compatibility

**JSON files are NOT deleted automatically.** They remain as:
- Backup of original data
- Fallback source if needed
- Reference for data structure

To clean up (after verifying migration), optionally delete:
- `events.json`, `news.json`, `code_challenges.json`
- `hackathons.json`, `roadmaps.json`, `domains.json`
- `stats.json`, `meetups.json`, `broadcasts.json`
- `feedback.json`, `team_finder.json`, `users.json`
- `core_members.json`, `volunteers.json`, `progress.json`
- `tickets.json`, `checkins.json`

## Troubleshooting

### Issue: "Collection doesn't exist"
**Solution:** The collection will be created automatically when the first document is inserted. No action needed.

### Issue: "Connection failed to MongoDB"
**Check:**
- Internet connectivity
- MongoDB Atlas cluster is active
- Connection string is correct
- IP whitelist includes your IP address

### Issue: "Duplicate key error"
**Cause:** Attempting to migrate twice into same collection
**Solution:** Collections only migrate if empty. Clear MongoDB collections to re-run migration.

### Issue: "No admin user created"
**Solution:** Manually create admin user via endpoint:
```bash
POST /api/users
{
    "username": "admin",
    "password": "admin123",
    "role": "admin",
    "name": "Admin User",
    "email": "admin@example.com"
}
```

## Performance Notes

- MongoDB operations are async-ready but currently synchronous
- All queries return JSON serializable data (ObjectIds converted to strings)
- Indexes enable O(log n) lookups instead of O(n) file reads
- No file I/O bottleneck for large datasets

## Future Improvements

1. **Async Operations:** Convert database methods to async/await for better performance
2. **Pagination:** Add limit/skip for large result sets
3. **Aggregation Pipeline:** Complex queries using MongoDB aggregation
4. **Schema Validation:** Add JSON schema validation in MongoDB
5. **Transactions:** Use MongoDB transactions for multi-document operations

## Summary

✓ All 17 collections properly defined and indexed
✓ All CRUD operations using MongoDB
✓ Automatic migration on startup
✓ Manual migration script available
✓ Zero API changes - fully backward compatible
✓ Default data initialization included
✓ Production-ready setup

**Status:** ✅ MongoDB integration complete and ready for use!
