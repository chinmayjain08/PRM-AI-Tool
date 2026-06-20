"""
All fixed lists and display constants used across multiple screens.
Named — never inline magic strings or number literals.
"""

# Used in BRD Screen 5.1 (Submit Timesheet)
ACTIVITY_TAGS = [
    "Backend API Development",
    "Microservices / Architecture",
    "Database Design & Queries",
    "WebSocket / Real-time Features",
    "Frontend Development",
    "Code Review / Mentoring",
    "Bug Fixing",
    "DevOps / Deployment",
    "Testing & QA",
    "Documentation",
    "Other",
]

SKILL_CATEGORIES   = ["Backend", "Frontend", "DevOps", "QA", "Other"]
PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

PROJECT_STATUSES_CREATE = ["PLANNED", "ACTIVE", "ON_HOLD"]
PROJECT_STATUSES_UPDATE = ["PLANNED", "ACTIVE", "ON_HOLD", "COMPLETED"]

MILESTONE_STATUSES = ["NOT_STARTED", "IN_PROGRESS", "DONE"]

USER_ROLES = ["Admin", "Manager", "Employee"]

HEALTH_ICONS = {
    "ON_TRACK":  "🟢",
    "ATTENTION": "🟡",
    "AT_RISK":   "🔴",
}

BOX_WIDTH = 46        # Named — not magic number 46 scattered in display.py
DIVIDER   = "─" * BOX_WIDTH
