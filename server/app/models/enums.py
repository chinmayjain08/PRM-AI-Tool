import enum

class TimesheetStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    MISSED = "MISSED"

class ProjectStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"

class ProjectHealthStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    ATTENTION = "ATTENTION"
    AT_RISK = "AT_RISK"

class MilestoneStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class ProficiencyLevel(str, enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
