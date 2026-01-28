# Quick Setup Guide - MongoDB Backend

## Prerequisites
- Python 3.9+
- MongoDB Atlas account (already configured)
- FastAPI dependencies installed

## Installation

### 1. Install Dependencies
```bash
pip install fastapi uvicorn pymongo python-jose[cryptography] pydantic
```

### 2. Database Configuration
Everything is pre-configured. The connection string is:
```
mongodb+srv://alfredsam2006_db_user:3ncbTinBSgTKAg0J@cluster0.o6fg583.mongodb.net/?appName=Cluster0
```

### 3. Start the Server
```bash
cd backend
python main.py
```

Server will start at `http://localhost:8000`

## API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## First Run

On first startup, the application will:
1. ✅ Connect to MongoDB
2. ✅ Create all collections if they don't exist
3. ✅ Migrate data from JSON files (if they exist)
4. ✅ Create default admin user:
   - Username: `admin`
   - Password: `admin123`
   - Role: `admin`
5. ✅ Create default core members
6. ✅ Initialize all indexes

## Testing the API

### Login
```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Get Events
```bash
curl "http://localhost:8000/api/events"
```

### Get Stats
```bash
curl "http://localhost:8000/api/admin/stats"
```

## Collections Overview

| Collection | Purpose | Documents |
|-----------|---------|-----------|
| users | User accounts & profiles | Varies |
| events | Event information | Varies |
| tickets | Event registrations | Varies |
| checkins | Event attendance | Varies |
| news | Blog posts | Varies |
| code_challenges | Coding problems | Varies |
| hackathons | Hackathon info | Varies |
| roadmaps | Learning paths | Varies |
| broadcasts | Announcements | Varies |
| feedback | User feedback | Varies |
| core_members | Team leads | 3 (default) |
| volunteers | Volunteers | Varies |
| domains | Tech domains | Varies |
| stats | System stats | Varies |
| meetups | Meetup info | Varies |
| progress | User progress | Varies |
| team_finder | Team posts | Varies |

## Common Operations

### Create User
```python
from database import db

user = {
    "id": "uuid-here",
    "username": "newuser",
    "password": "password123",
    "role": "student",
    "name": "John Doe",
    "email": "john@example.com"
}
db.insert_one("users", user)
```

### Query Users
```python
# Find all students
students = db.find_many("users", {"role": "student"})

# Find specific user
user = db.find_one("users", {"username": "admin"})
```

### Update User
```python
db.update_one("users", {"id": user_id}, {
    "name": "New Name",
    "email": "newemail@example.com"
})
```

### Delete User
```python
db.delete_one("users", {"id": user_id})
```

## Troubleshooting

### "Connection refused"
- Check MongoDB Atlas cluster is running
- Verify internet connectivity
- Check IP whitelist in MongoDB Atlas

### "Collections empty"
- Run `python migrate.py` to migrate JSON data
- Or populate via API endpoints

### "Invalid token"
- Get new token from login endpoint
- Token expires in 30 minutes

## Environment Variables (Optional)

To use environment variables instead of hardcoded strings:

```bash
# Create .env file
MONGO_URI=mongodb+srv://...
DB_NAME=IntellexaDB
SECRET_KEY=your-secret-key
```

Then update `database.py`:
```python
from os import getenv
MONGO_URI = getenv("MONGO_URI", "default-value")
```

## Development Mode

The server runs with `reload=True` for development:
- Auto-restarts on file changes
- Hot reloading enabled
- Debug mode active

## Production Deployment

For production, change in `main.py`:
```python
# Development
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Production
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
```

## Support

For issues, check:
1. [MONGODB_MIGRATION.md](MONGODB_MIGRATION.md) - Full migration guide
2. MongoDB Atlas console - Check cluster status
3. API docs at `/docs` - Try endpoints directly
4. Database logs - `db.find_all()` to inspect data

---

**Status**: ✅ Ready to use!
