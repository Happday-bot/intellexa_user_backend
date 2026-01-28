from fastapi import FastAPI, HTTPException, File, UploadFile, Cookie, Response, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
import uvicorn
from jose import JWTError, jwt
import os
import shutil
from glob import glob

# Import database and models
from database import db
from models import (
    Domain, Stat, Meetup, CoreMember, Volunteer, Event, NewsItem, 
    CodeQuestion, Broadcast, Hackathon, RoadmapStep, Resource, Roadmap,
    FeedbackItem, UserProgress, Ticket, EventRegistration, TeamContact,
    TeamFinderPost, CheckIn, AdminStats, User
)

app = FastAPI(
    title="FastAPI Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Static Files for Uploads
if not os.path.exists("uploads"):
    os.makedirs("uploads")
if not os.path.exists("uploads/resumes"):
    os.makedirs("uploads/resumes")

app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

# JWT Configuration
import secrets
import json

# Load or generate a persistent SECRET_KEY
def get_secret_key():
    """
    Load SECRET_KEY from environment, .env file, or generate and persist it.
    This ensures the same key is used across server restarts.
    """
    # First, check environment variable
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        print("✓ Using SECRET_KEY from environment variable")
        return env_key
    
    # Second, check if .env.local file exists with the key
    env_file = ".env.local"
    if os.path.exists(env_file):
        try:
            with open(env_file, "r") as f:
                env_data = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_data[key.strip()] = value.strip()
                if "SECRET_KEY" in env_data:
                    print(f"✓ Using SECRET_KEY from {env_file}")
                    return env_data["SECRET_KEY"]
        except Exception as e:
            print(f"Warning: Could not read {env_file}: {e}")
    
    # Third, check if secret is stored in a config file
    secret_file = "secret.key"
    if os.path.exists(secret_file):
        try:
            with open(secret_file, "r") as f:
                key = f.read().strip()
                if key:
                    print(f"✓ Using persistent SECRET_KEY from {secret_file}")
                    return key
        except Exception as e:
            print(f"Warning: Could not read {secret_file}: {e}")
    
    # Finally, generate and persist a new secret key
    new_key = secrets.token_urlsafe(32)
    try:
        with open(secret_file, "w") as f:
            f.write(new_key)
        print(f"✓ Generated and saved new SECRET_KEY to {secret_file}")
    except Exception as e:
        print(f"Warning: Could not save SECRET_KEY to {secret_file}: {e}")
        print(f"⚠ Using ephemeral key - tokens will be invalid after restart!")
    
    return new_key

SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
COOKIE_NAME = "intellexa_refresh"
COOKIE_PATH = "/"  # Root path so cookie is available to all routes
COOKIE_DOMAIN = None  # Set to your domain in production

# -------------------------------------------------
# CORS Configuration (Strict for Credentialed Requests)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # These are the FRONTEND websites allowed to talk to this backend
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.108.155:3000",
        "http://192.168.131.155:3000",
        "https://happday-bot.github.io", # Your GitHub Pages site
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validation Error Logging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"DEBUG: Validation Error at {request.url}")
    print(f"Errors: {json.dumps(exc.errors(), indent=2)}")
    try:
        body = await request.json()
        print(f"Request Body: {json.dumps(body, indent=2)}")
    except:
        print("Could not parse request body as JSON")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"},
    )

# Debug Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")
    if "cookie" in request.headers:
        print(f"Cookies in headers: {request.headers['cookie']}")
    else:
        print("No cookies in headers")
    response = await call_next(request)
    return response

# -------------------------------------------------
# Login & Auth Models
# -------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

# -------------------------------------------------
# Health Check / Base Route
# -------------------------------------------------
@app.get("/")
def test():
    return {
        "status": "200 OK",
        "message": "Working Fine"
    }

@app.get("/api/debug/cookies")
def debug_cookies(request: Request):
    """Debug endpoint to check if cookies are being received"""
    cookies = request.cookies
    return {
        "cookies_received": dict(cookies),
        "cookie_count": len(cookies),
        "headers": dict(request.headers),
        "message": f"Received {len(cookies)} cookies"
    }

# -------------------------------------------------
# JWT Token Functions
# -------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -------------------------------------------------
# Admin Stats
# -------------------------------------------------
@app.get("/api/admin/stats", response_model=AdminStats)
def get_admin_stats():
    total_users = db.count_documents("users")
    active_students = db.count_documents("users", {"role": "student"})
    total_events = db.count_documents("events")
    total_registrations = db.count_documents("tickets")
    total_checkins = db.count_documents("checkins")
    
    return {
        "totalUsers": total_users,
        "activeStudents": active_students,
        "totalEvents": total_events,
        "totalRegistrations": total_registrations,
        "totalCheckins": total_checkins
    }

# -------------------------------------------------
# Check-in Endpoints
# -------------------------------------------------
@app.post("/api/check-in")
def event_checkin(data: CheckIn):
    # Try to find ticket
    ticket = None
    if data.ticketId:
        ticket = db.find_one("tickets", {"id": data.ticketId})
    else:
        # Fallback for legacy QR codes without ticketId
        ticket = db.find_one("tickets", {"userId": data.studentId, "eventId": data.eventId})
        if ticket:
            data.ticketId = ticket["id"]

    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid Ticket or Registration Not Found")
    
    # Verify student and event match
    if ticket["userId"] != data.studentId or ticket["eventId"] != data.eventId:
        raise HTTPException(status_code=400, detail="Ticket data mismatch")
    
    # Check if already checked in
    if db.find_one("checkins", {"ticketId": data.ticketId}):
        raise HTTPException(status_code=400, detail="Already checked in")
    
    new_checkin = data.dict()
    new_checkin["scannedAt"] = datetime.now().isoformat()
    
    db.insert_one("checkins", new_checkin)
    
    return {"message": "Check-in successful", "studentId": data.studentId}

@app.get("/api/admin/check-ins")
def get_checkins():
    return db.find_all("checkins")

@app.get("/api/admin/attendance/{event_id}")
def get_event_attendance(event_id: int):
    # Get all tickets for this event
    event_tickets = db.find_many("tickets", {"eventId": event_id})
    
    # Get all check-ins for this event
    event_checkins = {c["ticketId"]: c for c in db.find_many("checkins", {"eventId": event_id})}
    
    # Get student details for each ticket
    report = []
    for t in event_tickets:
        student = db.find_one("users", {"id": t["userId"]})
        checkin = event_checkins.get(t["id"])
        
        report.append({
            "studentId": t["userId"],
            "studentName": student.get("name", "Unknown") if student else "Unknown",
            "registrationDate": t.get("registrationDate"),
            "checkedIn": checkin is not None,
            "checkInTime": checkin.get("scannedAt") if checkin else None
        })
    
    return report

@app.post("/api/admin/check-in/manual")
def manual_checkin(data: CheckIn):
    # Try to find ticket
    ticket = None
    if data.ticketId:
        ticket = db.find_one("tickets", {"id": data.ticketId})
    else:
        # Fallback using studentId and eventId
        ticket = db.find_one("tickets", {"userId": data.studentId, "eventId": data.eventId})
        if ticket:
            data.ticketId = ticket["id"]

    if not ticket:
        raise HTTPException(status_code=404, detail="Registration/Ticket not found for this user and event")
    
    # Check if already checked in
    if db.find_one("checkins", {"ticketId": data.ticketId}):
        raise HTTPException(status_code=400, detail="Already checked in")
    
    new_checkin = data.dict()
    new_checkin["scannedAt"] = datetime.now().isoformat()
    new_checkin["scannedBy"] = "admin"
    
    db.insert_one("checkins", new_checkin)
    
    return {"message": "Manual check-in successful", "studentId": data.studentId}

@app.post("/api/admin/register-student")
def register_student_to_event(data: dict):
    user_id = data.get("userId") or data.get("studentId")
    event_id = data.get("eventId")
    
    # Verify user exists
    user = db.find_one("users", {"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify event exists
    event = db.find_one("events", {"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already registered
    if db.find_one("tickets", {"userId": user_id, "eventId": event_id}):
        raise HTTPException(status_code=400, detail="User already registered for this event")
    
    ticket_data = {
        "id": str(uuid.uuid4()),
        "userId": user_id,
        "eventId": event_id,
        "registrationDate": datetime.now().isoformat(),
        "qrCode": None
    }
    
    db.insert_one("tickets", ticket_data)
    
    return {"message": "Student registered successfully", "ticketId": ticket_data["id"]}

# -------------------------------------------------
# Domains CRUD
# -------------------------------------------------
@app.get("/api/domains", response_model=List[Domain])
def get_domains():
    return db.find_all("domains")

@app.post("/api/domains", response_model=Domain)
def add_domain(domain: Domain):
    domain_data = domain.dict()
    db.insert_one("domains", domain_data)
    return domain

@app.put("/api/domains/{domain_id}", response_model=Domain)
def update_domain(domain_id: str, domain: Domain):
    result = db.update_one("domains", {"id": domain_id}, domain.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain

@app.delete("/api/domains/{domain_id}")
def delete_domain(domain_id: str):
    result = db.delete_one("domains", {"id": domain_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Domain not found")
    return {"message": "Domain deleted"}

# -------------------------------------------------
# Stats CRUD
# -------------------------------------------------
@app.get("/api/stats", response_model=List[Stat])
def get_stats():
    # Dynamic Stats
    active_users = db.count_documents("users")
    core_team_count = db.count_documents("core_members")
    volunteer_count = db.count_documents("volunteers")
    
    # Custom Stats from DB
    db_stats = db.find_all("stats")
    
    return db_stats

@app.post("/api/stats", response_model=Stat)
def add_stat(stat: Stat):
    db.insert_one("stats", stat.dict())
    return stat

@app.delete("/api/stats/{label}")
def delete_stat(label: str):
    # Don't allow deleting dynamic stats via this API if we want to protect them
    # But usually, the admin should be able to manage them if they are in DB
    result = db.delete_one("stats", {"label": label})
    # We return success even if 0 documents were deleted to be idempotent, 
    # but for stats specifically, we might want to know if it existed.
    return {"message": "Stat deleted", "count": result}

@app.put("/api/stats/{label}", response_model=Stat)
def update_stat(label: str, stat: Stat):
    # Use replace_one or update_one with upsert if possible, 
    # but database.py update_one doesn't support upsert yet.
    # So we check existence or just perform update.
    
    # The issue reported was 404 if not found or not modified.
    # Let's check if it exists first.
    existing = db.find_one("stats", {"label": label})
    
    stat_data = stat.dict()
    if existing:
        db.update_one("stats", {"label": label}, stat_data)
    else:
        db.insert_one("stats", stat_data)
        
    return stat

# -------------------------------------------------
# Meetups CRUD
# -------------------------------------------------
@app.get("/api/meetups", response_model=List[Meetup])
def get_meetups():
    return db.find_all("meetups")

@app.post("/api/meetups", response_model=Meetup)
def add_meetup(meetup: Meetup):
    if not meetup.id:
        meetup.id = max([m.get("id", 0) for m in db.find_all("meetups")] + [0]) + 1
    db.insert_one("meetups", meetup.dict())
    return meetup

@app.delete("/api/meetups/{meetup_id}")
def delete_meetup(meetup_id: int):
    result = db.delete_one("meetups", {"id": meetup_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return {"message": "Meetup deleted"}

@app.put("/api/meetups/{meetup_id}", response_model=Meetup)
def update_meetup(meetup_id: int, meetup: Meetup):
    result = db.update_one("meetups", {"id": meetup_id}, meetup.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return meetup

# -------------------------------------------------
# Core Members CRUD
# -------------------------------------------------
@app.get("/api/core-members", response_model=List[CoreMember])
def get_core_members():
    return db.find_all("core_members")

@app.post("/api/core-members", response_model=CoreMember)
def add_core_member(member: CoreMember):
    db.insert_one("core_members", member.dict())
    return member

@app.delete("/api/core-members/{name}")
def delete_core_member(name: str):
    result = db.delete_one("core_members", {"name": name})
    if result == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member deleted"}

@app.put("/api/core-members/{name}", response_model=CoreMember)
def update_core_member(name: str, member: CoreMember):
    result = db.update_one("core_members", {"name": name}, member.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

# -------------------------------------------------
# Volunteers CRUD
# -------------------------------------------------
@app.get("/api/volunteers", response_model=List[Volunteer])
def get_volunteers():
    return db.find_all("volunteers")

@app.post("/api/volunteers", response_model=Volunteer)
def add_volunteer(volunteer: Volunteer):
    if not volunteer.id:
        volunteer.id = str(uuid.uuid4())
    db.insert_one("volunteers", volunteer.dict())
    return volunteer

@app.put("/api/volunteers/{volunteer_id}", response_model=Volunteer)
def update_volunteer(volunteer_id: str, volunteer: Volunteer):
    result = db.update_one("volunteers", {"id": volunteer_id}, volunteer.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return volunteer

@app.delete("/api/volunteers/{volunteer_id}")
def delete_volunteer(volunteer_id: str):
    result = db.delete_one("volunteers", {"id": volunteer_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return {"message": "Volunteer deleted"}

# -------------------------------------------------
# Events CRUD
# -------------------------------------------------
@app.get("/api/events")
def get_events():
    # Enrich events with dynamic slotsFilled count and dynamic status
    enriched_events = []
    now = datetime.now().date()
    
    for event in db.find_all("events"):
        # Calculate slots filled
        count = db.count_documents("tickets", {"eventId": event["id"]})
        
        # Calculate dynamic status
        try:
            event_date = datetime.strptime(event["date"], "%B %d, %Y").date()
            if event_date < now:
                status = "Past"
            elif event_date == now:
                status = "Today"
            else:
                status = "Upcoming"
        except Exception:
            status = "Upcoming"
            
        enriched_events.append({
            **event, 
            "slotsFilled": count,
            "status": status
        })
    return enriched_events

@app.post("/api/events", response_model=Event)
def add_event(event: Event):
    if not event.id:
        event.id = max([e.get("id", 0) for e in db.find_all("events")] + [0]) + 1
    db.insert_one("events", event.dict())
    return event

@app.get("/api/events/{event_id}")
def get_api_event(event_id: int):
    event = db.find_one("events", {"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    count = db.count_documents("tickets", {"eventId": event_id})
    now = datetime.now().date()
    try:
        event_date = datetime.strptime(event["date"], "%B %d, %Y").date()
        if event_date < now:
            status = "Past"
        elif event_date == now:
            status = "Today"
        else:
            status = "Upcoming"
    except Exception:
        status = "Upcoming"
        
    return {
        **event, 
        "slotsFilled": count,
        "status": status
    }

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    result = db.delete_one("events", {"id": event_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted"}

@app.put("/api/events/{event_id}", response_model=Event)
def update_event(event_id: int, event: Event):
    result = db.update_one("events", {"id": event_id}, event.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@app.post("/api/events/register")
def register_for_event(registration: EventRegistration):
    # Check if user exists
    user = db.find_one("users", {"id": registration.userId})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if event exists
    event = db.find_one("events", {"id": registration.eventId})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already registered
    existing_ticket = db.find_one("tickets", {"userId": registration.userId, "eventId": registration.eventId})
    if existing_ticket:
        raise HTTPException(status_code=400, detail="You are already registered for this event")
    
    # Create ticket
    ticket_id = str(uuid.uuid4())
    new_ticket = {
        "id": ticket_id,
        "userId": registration.userId,
        "eventId": registration.eventId,
        "registrationDate": datetime.now().isoformat(),
        "qrCode": f"TICKET-{ticket_id}"
    }
    
    db.insert_one("tickets", new_ticket)
    
    return {"message": "Successfully registered", "ticketId": ticket_id}

# -------------------------------------------------
# News CRUD
# -------------------------------------------------
@app.get("/api/news", response_model=List[NewsItem])
def get_news():
    return db.find_all("news")

@app.get("/api/news/{news_id}", response_model=NewsItem)
def get_news_item(news_id: int):
    news = db.find_one("news", {"id": news_id})
    if not news:
        raise HTTPException(status_code=404, detail="News item not found")
    return news

@app.post("/api/news", response_model=NewsItem)
def add_news(news: NewsItem):
    if not news.id:
        news.id = max([n.get("id", 0) for n in db.find_all("news")] + [0]) + 1
    db.insert_one("news", news.dict())
    return news

@app.delete("/api/news/{news_id}")
def delete_news(news_id: int):
    result = db.delete_one("news", {"id": news_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="News not found")
    return {"message": "News deleted"}

@app.put("/api/news/{news_id}", response_model=NewsItem)
def update_news(news_id: int, news: NewsItem):
    result = db.update_one("news", {"id": news_id}, news.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="News not found")
    return news

# -------------------------------------------------
# Code Challenges CRUD
# -------------------------------------------------
@app.get("/api/code-challenges", response_model=List[CodeQuestion])
def get_code_challenges():
    return db.find_all("code_challenges")

@app.post("/api/code-challenges", response_model=CodeQuestion)
def add_code_challenge(challenge: CodeQuestion):
    if not challenge.id:
        challenge.id = str(uuid.uuid4())
    db.insert_one("code_challenges", challenge.dict())
    return challenge

@app.get("/api/code-challenges/{challenge_id}", response_model=CodeQuestion)
def get_code_challenge(challenge_id: str):
    challenge = db.find_one("code_challenges", {"id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

@app.delete("/api/code-challenges/{challenge_id}")
def delete_code_challenge(challenge_id: str):
    result = db.delete_one("code_challenges", {"id": challenge_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"message": "Challenge deleted"}

@app.put("/api/code-challenges/{challenge_id}", response_model=CodeQuestion)
def update_code_challenge(challenge_id: str, challenge: CodeQuestion):
    result = db.update_one("code_challenges", {"id": challenge_id}, challenge.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge

# -------------------------------------------------
# Hackathons CRUD
# -------------------------------------------------
@app.get("/api/hackathons", response_model=List[Hackathon])
def get_hackathons():
    return db.find_all("hackathons")

@app.post("/api/hackathons", response_model=Hackathon)
def add_hackathon(hackathon: Hackathon):
    if not hackathon.id:
        hackathon.id = max([h.get("id", 0) for h in db.find_all("hackathons")] + [0]) + 1
    db.insert_one("hackathons", hackathon.dict())
    return hackathon

@app.delete("/api/hackathons/{hackathon_id}")
def delete_hackathon(hackathon_id: int):
    result = db.delete_one("hackathons", {"id": hackathon_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return {"message": "Hackathon deleted"}

@app.put("/api/hackathons/{hackathon_id}", response_model=Hackathon)
def update_hackathon(hackathon_id: int, hackathon: Hackathon):
    result = db.update_one("hackathons", {"id": hackathon_id}, hackathon.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return hackathon

# -------------------------------------------------
# Roadmaps CRUD
# -------------------------------------------------
@app.get("/api/roadmaps", response_model=List[Roadmap])
def get_roadmaps():
    return db.find_all("roadmaps")

@app.post("/api/roadmaps", response_model=Roadmap)
def add_roadmap(roadmap: Roadmap):
    if not roadmap.id:
        roadmap.id = str(uuid.uuid4())
    db.insert_one("roadmaps", roadmap.dict())
    return roadmap

@app.get("/api/roadmaps/{roadmap_id}", response_model=Roadmap)
def get_roadmap(roadmap_id: str):
    roadmap = db.find_one("roadmaps", {"id": roadmap_id})
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap

@app.delete("/api/roadmaps/{roadmap_id}")
def delete_roadmap(roadmap_id: str):
    result = db.delete_one("roadmaps", {"id": roadmap_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return {"message": "Roadmap deleted"}

@app.put("/api/roadmaps/{roadmap_id}", response_model=Roadmap)
def update_roadmap(roadmap_id: str, roadmap: Roadmap):
    result = db.update_one("roadmaps", {"id": roadmap_id}, roadmap.dict())
    if result == 0:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap

# -------------------------------------------------
# Broadcasts CRUD
# -------------------------------------------------
@app.get("/api/broadcasts", response_model=List[Broadcast])
def get_broadcasts():
    return db.find_all("broadcasts")

@app.post("/api/broadcasts", response_model=Broadcast)
def add_broadcast(broadcast: Broadcast):
    if not broadcast.id:
        broadcast.id = str(uuid.uuid4())
    if not broadcast.createdAt:
        broadcast.createdAt = datetime.now().isoformat()
    db.insert_one("broadcasts", broadcast.dict())
    return broadcast

@app.delete("/api/broadcasts/{broadcast_id}")
def delete_broadcast(broadcast_id: str):
    result = db.delete_one("broadcasts", {"id": broadcast_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return {"message": "Broadcast deleted"}

# -------------------------------------------------
# Feedback CRUD
# -------------------------------------------------
@app.get("/api/feedback", response_model=List[FeedbackItem])
def get_feedback():
    return db.find_all("feedback")

@app.post("/api/feedback", response_model=FeedbackItem)
def add_feedback(feedback: FeedbackItem):
    if not feedback.id:
        feedback.id = str(uuid.uuid4())
    if not feedback.date:
        feedback.date = datetime.now().isoformat()
    db.insert_one("feedback", feedback.dict())
    return feedback

@app.get("/api/feedback/{event_id}")
def get_event_feedback(event_id: int):
    feedback_list = db.find_many("feedback", {"eventId": event_id})
    return feedback_list

# -------------------------------------------------
# Team Finder CRUD
# -------------------------------------------------
@app.get("/api/team-finder")
def get_team_finder_posts():
    return db.find_all("team_finder")

@app.post("/api/team-finder", response_model=TeamFinderPost)
def create_team_finder_post(post: TeamFinderPost):
    if not post.id:
        post.id = str(uuid.uuid4())
    if not post.createdAt:
        post.createdAt = datetime.now().isoformat()
    db.insert_one("team_finder", post.dict())
    post_dict = post.dict()
    post_dict.pop("_id", None)
    return post_dict

@app.delete("/api/team-finder/{post_id}")
def delete_team_finder_post(post_id: str):
    result = db.delete_one("team_finder", {"id": post_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted"}

# -------------------------------------------------
# User Progress CRUD
# -------------------------------------------------
@app.get("/api/progress/{user_id}", response_model=UserProgress)
def get_user_progress(user_id: str):
    progress = db.find_one("progress", {"userId": user_id})
    if not progress:
        # Return default progress
        return UserProgress(userId=user_id)
    return progress

@app.post("/api/progress", response_model=UserProgress)
def update_user_progress(progress: UserProgress):
    existing = db.find_one("progress", {"userId": progress.userId})
    if existing:
        db.update_one("progress", {"userId": progress.userId}, progress.dict())
    else:
        db.insert_one("progress", progress.dict())
    return progress

@app.get("/api/leaderboard")
def get_leaderboard():
    """Get all users sorted by totalExp in descending order"""
    leaderboard_data = db.find_all("progress")
    # Remove MongoDB's _id field and sort by totalExp descending
    cleaned = []
    for item in leaderboard_data:
        item.pop("_id", None)
        cleaned.append(item)
    # Sort by totalExp in descending order
    cleaned.sort(key=lambda x: x.get("totalExp", 0), reverse=True)
    return cleaned

# -------------------------------------------------
# Tickets CRUD
# -------------------------------------------------
@app.get("/api/tickets")
def get_all_tickets():
    return db.find_all("tickets")

@app.get("/api/tickets/{user_id}")
def get_user_tickets(user_id: str):
    return db.find_many("tickets", {"userId": user_id})

@app.post("/api/tickets", response_model=Ticket)
def create_ticket(ticket: Ticket):
    if not ticket.id:
        ticket.id = str(uuid.uuid4())
    if not ticket.registrationDate:
        ticket.registrationDate = datetime.now().isoformat()
    db.insert_one("tickets", ticket.dict())
    return ticket

@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: str):
    result = db.delete_one("tickets", {"id": ticket_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted"}

# -------------------------------------------------
# User Authentication & Management
# -------------------------------------------------
@app.post("/api/login")
def login_endpoint(creds: LoginRequest, response: Response):
    # Find user in MongoDB
    user = db.find_one("users", {"username": creds.username})
    
    if not user or user.get("password") != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user["username"], "userId": user["id"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token_str = create_refresh_token(
        data={"sub": user["username"], "userId": user["id"]}
    )
    
    # Set refresh token as HttpOnly cookie (secure, httpOnly, sameSite)
    # Proper cookie settings for automatic transmission with requests
    # In production (Render/GitHub Pages), we MUST use secure=True and samesite="none"
    is_prod = os.getenv("RENDER") is not None or os.getenv("PRODUCTION") is not None
    print(f"DEBUG: Environment detection - RENDER={os.getenv('RENDER')}, PRODUCTION={os.getenv('PRODUCTION')}, is_prod={is_prod}")
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=refresh_token_str,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 days
        httponly=True,  # Not accessible via JavaScript - XSS protection
        secure=True if is_prod else False,  # MUST be True for SameSite=None
        samesite="none" if is_prod else "lax",  # REQUIRED for cross-site cookies
        path=COOKIE_PATH,  # Root path so it's available everywhere
        domain=COOKIE_DOMAIN  # All subdomains if None
    )
    
    print(f"✓ Login successful for user: {user['username']}")
    print(f"✓ Refresh token cookie set: {COOKIE_NAME} (path={COOKIE_PATH}, httponly=True, samesite=lax)")
    print(f"✓ Access token created (expires in {ACCESS_TOKEN_EXPIRE_MINUTES} minutes)")
    print(f"DEBUG: Set-Cookie header: {response.headers.get('set-cookie')}")
    
    return {
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role")
        }
    }

@app.post("/api/auth/login")
def auth_login(creds: LoginRequest, response: Response):
    """Backward compatible login endpoint"""
    return login_endpoint(creds, response)

@app.post("/api/refresh")
def refresh_access_token(response: Response, refresh_token: str = Cookie(None, alias=COOKIE_NAME)):
    """Refresh access token using refresh token from HttpOnly cookie"""
    print(f"DEBUG: Refresh endpoint called. Cookie: {refresh_token}")
    if not refresh_token:
        print("✗ No refresh token provided in cookie")
        raise HTTPException(status_code=401, detail="No refresh token provided")
    
    try:
        # Decode the refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")
        
        # Validate token type
        if not username or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Get user from database
        user = db.find_one("users", {"username": username})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Create new access token
        new_access_token = create_access_token(
            data={"sub": username, "userId": user["id"], "role": user["role"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Optionally refresh the refresh token as well (token rotation)
        new_refresh_token = create_refresh_token(
            data={"sub": username, "userId": user["id"]}
        )
        
        is_prod = os.getenv("RENDER") is not None or os.getenv("PRODUCTION") is not None
        response.set_cookie(
            key=COOKIE_NAME,
            value=new_refresh_token,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=True if is_prod else False,
            samesite="none" if is_prod else "lax",
            path=COOKIE_PATH,
            domain=COOKIE_DOMAIN
        )
        
        print(f"✓ Token refresh successful for user: {username}")
        print(f"✓ New refresh token cookie set with token rotation")
        
        return {
            "access_token": new_access_token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role")
            }
        }
    except JWTError as e:
        print(f"✗ Token refresh failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}") 

@app.post("/api/auth/refresh")
def auth_refresh(response: Response, refresh_token: str = Cookie(None, alias=COOKIE_NAME)):
    """Backward compatible refresh endpoint"""
    return refresh_access_token(response, refresh_token)

@app.post("/api/auth/logout")
def logout(response: Response):
    """Logout by clearing the refresh token cookie"""
    is_prod = os.getenv("RENDER") is not None or os.getenv("PRODUCTION") is not None
    # Delete cookie with same path and domain it was set with
    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
        secure=True if is_prod else False,
        samesite="none" if is_prod else "lax"
    )
    print(f"✓ Logout successful: Refresh token cookie cleared ({COOKIE_NAME})")
    return {"message": "Logged out successfully"}

@app.get("/api/users", response_model=List[User])
def get_all_users(role: Optional[str] = None):
    if role:
        if role.lower() == "all":
            return db.find_all("users")
        return db.find_many("users", {"role": role})
    return db.find_all("users")

@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    user = db.find_one("users", {"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/users/role/{role}", response_model=List[User])
def get_users_by_role_new(role: str):
    if role.lower() == "all":
        return db.find_all("users")
    return db.find_many("users", {"role": role})

# Backward compatible role route (deprecated, move below specific routes)
@app.get("/api/users/filter/{role}", response_model=List[User])
def get_users_by_role_deprecated(role: str):
    return get_users_by_role_new(role)

@app.put("/api/users/{user_id}", response_model=User)
def update_user(user_id: str, user: User):
    existing_user = db.find_one("users", {"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if username is taken by another user
    if user.username != existing_user.get("username"):
        if db.find_one("users", {"username": user.username}):
            raise HTTPException(status_code=400, detail="Username already exists")
            
    # Check if email is taken by another user
    if user.email != existing_user.get("email"):
        if db.find_one("users", {"email": user.email}):
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Merge data and preserve sensitive/immutable fields
    updated_data = existing_user.copy()
    user_dict = user.dict(exclude_unset=True)
    
    # Update with new values
    updated_data.update(user_dict)
    
    # Ensure sensitive fields are preserved if they were somehow overwritten
    updated_data["id"] = user_id
    updated_data["createdAt"] = existing_user.get("createdAt")
    updated_data["password"] = existing_user.get("password")
    
    db.update_one("users", {"id": user_id}, updated_data)
    
    # Fetch the full updated document to be sure
    final_user = db.find_one("users", {"id": user_id})
    final_user.pop("_id", None)
    return User(**final_user)

@app.delete("/api/users/{user_id}")
def delete_user(user_id: str):
    result = db.delete_one("users", {"id": user_id})
    if result == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

@app.post("/api/users")
def add_user(user: User):
    # Check if username exists
    if db.find_one("users", {"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    if db.find_one("users", {"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    if not user.id:
        user.id = str(uuid.uuid4())
    if not user.createdAt:
        user.createdAt = datetime.now().strftime("%Y-%m-%d")
        
    user_dict = user.dict()
    db.insert_one("users", user_dict)
    # Remove MongoDB's _id field if present before returning
    user_dict.pop("_id", None)
    return user_dict

# -------------------------------------------------
# Authentication Endpoints (Backward Compatibility)
# -------------------------------------------------
@app.post("/api/auth/register")
def register(user: User):
    """Backward compatible registration endpoint"""
    return add_user(user)

# -------------------------------------------------
# Resume Upload
# -------------------------------------------------
@app.post("/api/upload-resume/{user_id}")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    try:
        # Verify user exists
        user = db.find_one("users", {"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Save file
        filename = f"{user_id}_{file.filename}"
        filepath = os.path.join("uploads/resumes", filename)
        
        with open(filepath, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Update user with resume URL
        resume_url = f"/api/uploads/resumes/{filename}"
        db.update_one("users", {"id": user_id}, {
            "resumeUrl": resume_url,
            "resumeName": file.filename
        })
        
        return {
            "message": "Resume uploaded successfully",
            "resumeUrl": resume_url,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/uploads/resumes/{filename}")
async def get_resume(filename: str):
    filepath = os.path.join("uploads/resumes", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="Resume not found")

@app.get("/api/users/{user_id}/resume/download")
async def download_user_resume(user_id: str):
    user = db.find_one("users", {"id": user_id})
    if not user or not user.get("resumeUrl"):
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Extract filename from URL/path
    filename = os.path.basename(user["resumeUrl"])
    filepath = os.path.join("uploads/resumes", filename)
    
    if os.path.exists(filepath):
        return FileResponse(
            filepath, 
            media_type='application/octet-stream',
            filename=user.get("resumeName", filename)
        )
    raise HTTPException(status_code=404, detail="Resume file missing")

# -------------------------------------------------
# Initialization
# -------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("Starting up...")
    
    # Migrate data from JSON files if needed
    # migrate_from_json() - Removed as the transition to MongoDB is complete
    
    # Initialize default admin user if not exists
    admin = db.find_one("users", {"username": "admin"})
    if not admin:
        default_admin = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password": "admin123",
            "role": "admin",
            "name": "Super Admin",
            "email": "admin@intellexa.com",
            "createdAt": "2024-01-01"
        }
        db.insert_one("users", default_admin)
        print("Default admin user created")
    
    # Initialize default core members if not exists
    if db.count_documents("core_members") == 0:
        default_members = [
            {
                "name": "Alfred Sam D",
                "role": "Tech Lead",
                "image": "https://media.licdn.com/dms/image/v2/D5603AQE3KNBQc3_xjQ/profile-displayphoto-scale_400_400/B56ZhjSis9HkAk-/0/1754012464437?e=1769040000&v=beta&t=XwqHGVf7juMmyj1clVLQNW-KFtfurVdQwjR4U4Idyfk",
                "domain": "Full Stack, AI, Quantum Computing"
            },
            {
                "name": "Sarah J",
                "role": "Asst Tech Lead",
                "image": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1000&auto=format&fit=crop",
                "domain": "Cloud Computing"
            },
            {
                "name": "Mike T",
                "role": "Event Head",
                "image": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1000&auto=format&fit=crop",
                "domain": "Cybersecurity"
            }
        ]
        db.insert_many("core_members", default_members)
        print("Default core members created")
    
    # Initialize default team finder posts if not exists
    if db.count_documents("team_finder") == 0:
        sample_posts = [
            {
                "id": str(uuid.uuid4()),
                "title": "Need Backend Developer for AI Chatbot",
                "description": "Building an AI-powered chatbot for customer support. Looking for someone experienced with Python and FastAPI to help with the backend infrastructure.",
                "hackathon": "GenAI Hackathon 2026",
                "teamSize": "2 Members",
                "skills": ["Python", "FastAPI", "MongoDB", "API Design"],
                "createdAt": datetime.now().isoformat(),
                "contact": {
                    "name": "Priya Sharma",
                    "email": "priya.sharma@example.com"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Seeking Frontend Expert for Web App",
                "description": "Creating a real-time collaboration tool. Need a React/TypeScript expert to build responsive UI components and handle state management.",
                "hackathon": "Web Dev Challenge 2026",
                "teamSize": "2 Members",
                "skills": ["React", "TypeScript", "Tailwind CSS", "Redux"],
                "createdAt": datetime.now().isoformat(),
                "contact": {
                    "name": "Arjun Patel",
                    "email": "arjun.patel@example.com"
                }
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Cloud & DevOps Specialist Needed",
                "description": "Deploying a microservices architecture on AWS. Looking for someone who can handle containerization, CI/CD pipelines, and cloud infrastructure setup.",
                "hackathon": "Cloud Summit 2026",
                "teamSize": "1 Member",
                "skills": ["AWS", "Docker", "Kubernetes", "CI/CD"],
                "createdAt": datetime.now().isoformat(),
                "contact": {
                    "name": "Rahul Verma",
                    "email": "rahul.verma@example.com"
                }
            }
        ]
        db.insert_many("team_finder", sample_posts)
        print("Default team finder posts created")
    
    print("✓ Database initialized successfully")

# -------------------------------------------------
# Entry Point
# -------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
