from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class Domain(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    color: str
    image: str


class Stat(BaseModel):
    label: str
    value: str
    icon: str


class Meetup(BaseModel):
    id: Optional[int] = None
    image: str
    title: str
    description: str


class CoreMember(BaseModel):
    name: str
    role: str
    image: str
    domain: str


class Volunteer(BaseModel):
    id: Optional[str] = None
    name: str
    role: str
    email: str
    image: Optional[str] = "https://images.unsplash.com/photo-1633332755192-727a05c4013d"
    status: Optional[str] = "Active"


class Event(BaseModel):
    id: Optional[int] = None
    title: str
    date: str
    time: str
    venue: str
    category: str
    image: str
    status: Optional[str] = "Upcoming"
    slotsFilled: Optional[int] = 0
    totalSlots: Optional[int] = 100


class NewsItem(BaseModel):
    id: Optional[int] = None
    title: str
    category: str
    date: str
    image: str
    summary: str
    content: Optional[str] = None
    link: Optional[str] = None


class CodeQuestion(BaseModel):
    id: Optional[str] = None
    title: str
    functionName: str
    difficulty: str
    category: str
    tags: List[str]
    description: str
    constraints: List[str]
    starterCode: Dict[str, str]
    testCases: List[Dict[str, str]]


class Broadcast(BaseModel):
    id: Optional[str] = None
    subject: str
    target: str
    message: str
    createdAt: Optional[str] = None


class Hackathon(BaseModel):
    id: Optional[int] = None
    title: str
    organizer: str
    date: str
    mode: str
    location: str
    prize: str
    image: str
    tags: List[str]
    link: str


class RoadmapStep(BaseModel):
    title: str
    desc: str


class Resource(BaseModel):
    title: str
    type: str
    desc: str
    link: str
    image: str


class Roadmap(BaseModel):
    id: Optional[str] = None
    label: str
    description: str
    icon: str
    color: str
    roadmap: List[RoadmapStep]
    resources: List[Resource]


class FeedbackItem(BaseModel):
    id: Optional[str] = None
    type: str  # 'rating' | 'suggestion'
    eventId: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    user: Optional[str] = "Anonymous"
    date: Optional[str] = None


class UserProgress(BaseModel):
    userId: str
    passedQuestions: List[str] = []  # IDs of passed questions
    totalExp: int = 0
    rank: str = "NOVICE"


class Ticket(BaseModel):
    id: Optional[str] = None
    userId: str
    eventId: int
    registrationDate: str
    qrCode: Optional[str] = None


class EventRegistration(BaseModel):
    userId: str
    eventId: int


class TeamContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class TeamFinderPost(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    hackathon: str
    teamSize: Optional[str] = "Any"
    skills: Optional[List[str]] = []
    createdAt: Optional[str] = None
    contact: Optional[TeamContact] = None


class CheckIn(BaseModel):
    id: Optional[str] = None
    ticketId: Optional[str] = None
    studentId: str
    eventId: int
    scannedAt: Optional[str] = None
    scannedBy: Optional[str] = "admin"


class AdminStats(BaseModel):
    totalUsers: int
    activeStudents: int
    totalEvents: int
    totalRegistrations: int
    totalCheckins: int


class User(BaseModel):
    id: Optional[str] = None
    username: str
    password: Optional[str] = None
    role: str  # 'admin' | 'student'
    name: str
    email: str
    createdAt: Optional[str] = None
    title: Optional[str] = "Student"
    description: Optional[str] = "Ready to code!"
    skills: Optional[List[str]] = []
    contact: Optional[TeamContact] = None
    college: Optional[str] = "Rajalakshmi Engineering College"
    department: Optional[str] = "Information Technology"
    year: Optional[str] = "Final Year"
    location: Optional[str] = "Chennai, India"
    bannerTheme: Optional[str] = "ocean"
    avatar: Optional[str] = "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"
    resumeUrl: Optional[str] = None
    resumeName: Optional[str] = None
