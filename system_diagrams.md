# PRM Tool — System Diagrams

Complete visual representation of the Project & Resource Management Tool architecture, data model, workflows, and user interactions.

---

## 1. Use Case Diagram

```mermaid
flowchart LR
    %% ── Actors (left column) ─────────────────────────────────
    Admin(["Admin"])
    Manager(["Manager"])
    Employee(["Employee (Resource)"])
    Scheduler(["Scheduler"])

    %% ── Shared auth use cases (centre-top) ──────────────────
    subgraph AUTH ["Authentication (All Roles)"]
        direction TB
        UC1(["Login with Credentials"])
        UC2(["Change Password"])
    end

    %% ── Admin use cases ─────────────────────────────────────
    subgraph ADMIN_UC ["Admin Functions"]
        direction TB
        subgraph UMgmt ["User & Employee Management"]
            direction TB
            UC3(["Create Employee Account & Profile"])
            UC4(["Reset Credentials Password"])
            UC5(["Deactivate Employee Account & Profile"])
            UC6(["Assign Manager to Profile"])
            UC7(["Manage Profile Skills"])
        end
        subgraph PMgmt ["Project Management"]
            direction TB
            UC8(["Create / Update Project"])
            UC9(["Add Milestone to Project"])
            UC10(["View All Allocations"])
        end
        UC11(["Configure System Settings"])
    end

    %% ── Manager use cases ────────────────────────────────────
    subgraph MANAGER_UC ["Manager Functions"]
        direction TB
        subgraph ResourceMgmt ["Resource Management"]
            direction TB
            UC12(["View Resource Dashboard"])
            UC13(["Allocate Resource to Project"])
            UC14(["Terminate Allocation"])
        end
        subgraph ProjectMgmt ["Project Monitoring"]
            direction TB
            UC15(["View My Projects & Health"])
            UC16(["View Team Timesheets"])
        end
        subgraph AI ["AI Features"]
            direction TB
            UC17(["AI Skill Match Query"])
            UC18(["AI Project Risk Summary"])
        end
    end

    %% ── Employee use cases ───────────────────────────────────
    subgraph EMPLOYEE_UC ["Employee Functions"]
        direction TB
        UC19(["View My Allocations"])
        UC20(["Submit Weekly Timesheet"])
        UC21(["View Timesheet History"])
        UC22(["Check Missed Weeks"])
    end

    %% ── Automated use cases ──────────────────────────────────
    subgraph AUTO_UC ["Automated Tasks"]
        direction TB
        UC23(["Mark Missed Timesheets"])
        UC24(["Recompute Project Health"])
    end

    %% ── Actor connections ────────────────────────────────────
    Admin     --> UC1
    Admin     --> UC2
    Admin     --> UC3
    Admin     --> UC4
    Admin     --> UC5
    Admin     --> UC6
    Admin     --> UC7
    Admin     --> UC8
    Admin     --> UC9
    Admin     --> UC10
    Admin     --> UC11

    Manager   --> UC1
    Manager   --> UC2
    Manager   --> UC12
    Manager   --> UC13
    Manager   --> UC14
    Manager   --> UC15
    Manager   --> UC16
    Manager   --> UC17
    Manager   --> UC18

    Employee  --> UC1
    Employee  --> UC2
    Employee  --> UC19
    Employee  --> UC20
    Employee  --> UC21
    Employee  --> UC22

    Scheduler --> UC23
    Scheduler --> UC24
```

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    employees {
        int id PK
        varchar username UK
        varchar email UK
        varchar full_name
        varchar hashed_password
        int role_id FK
        boolean is_active
        boolean force_password_change
        timestamp created_at
    }
    employee_profiles {
        int id PK
        int employee_id FK, UK
        varchar department
        int manager_id FK
        date joined_at
    }
    roles {
        int id PK
        varchar name UK
    }
    permissions {
        int id PK
        varchar name UK
        varchar description
    }
    role_permissions {
        int role_id PK, FK
        int permission_id PK, FK
    }
    skills {
        int id PK
        varchar name UK
        varchar category
    }
    employee_skills {
        int employee_id PK, FK "references employee_profiles.id"
        int skill_id PK, FK
        varchar proficiency
    }
    projects {
        int id PK
        varchar name
        text description
        date start_date
        date end_date
        varchar status
        int manager_id FK "references employees.id"
        int total_story_pts
        varchar health_status
    }
    milestones {
        int id PK
        int project_id FK
        varchar title
        date due_date
        int story_points
        varchar status
    }
    allocations {
        int id PK
        int employee_id FK "references employee_profiles.id"
        int project_id FK
        int utilisation_percent
        date from_date
        date to_date
        boolean is_active
    }
    timesheets {
        int id PK
        int employee_id FK "references employee_profiles.id"
        int project_id FK
        date week_start
        int hours_worked
        varchar status
        timestamp submitted_at
    }
    timesheet_tags {
        int id PK
        int timesheet_id FK
        varchar tag
    }
    system_config {
        int id PK
        varchar llm_provider
        text llm_api_key
        int scheduler_interval
        int max_weekly_hours
    }

    roles ||--o{ employees : "defines role of"
    employees ||--|| employee_profiles : "has profile"
    employee_profiles |o--o{ employee_profiles : "reports to manager (manager_id)"
    roles ||--o{ role_permissions : "contains"
    permissions ||--o{ role_permissions : "maps to"
    employee_profiles ||--o{ employee_skills : "has"
    skills ||--o{ employee_skills : "belongs to"
    employees ||--o{ projects : "manages (manager_id)"
    employee_profiles ||--o{ allocations : "allocated to"
    projects ||--o{ allocations : "has allocations"
    projects ||--o{ milestones : "has"
    employee_profiles ||--o{ timesheets : "submits"
    projects ||--o{ timesheets : "logs time for"
    timesheets ||--o{ timesheet_tags : "contains"
```

---

## 3. Class Diagram

```mermaid
classDiagram
    class Employee {
        +int id
        +str username
        +str email
        +str full_name
        +str hashed_password
        +int role_id
        +bool is_active
        +bool force_password_change
        +datetime created_at
    }

    class EmployeeProfile {
        +int id
        +int employee_id
        +str department
        +int manager_id
        +date joined_at
    }

    class Role {
        +int id
        +str name
    }

    class Permission {
        +int id
        +str name
        +str description
    }

    class Project {
        +int id
        +str name
        +str status
        +str health_status
        +int manager_id
    }

    class Allocation {
        +int id
        +int employee_id
        +int project_id
        +int utilisation_percent
        +bool is_active
    }

    class Timesheet {
        +int id
        +int employee_id
        +int project_id
        +date week_start
        +int hours_worked
        +str status
    }

    class Milestone {
        +int id
        +int project_id
        +str title
        +date due_date
        +str status
    }

    class AuthService {
        +login(db, username, password) dict
        +change_password(db, employee_id, new_pw) void
    }

    class EmployeeService {
        +create_employee(db, full_name, email, username, temp_pw, role) Employee
        +reset_employee_password(db, employee_id, temp_pw) void
        +deactivate_employee_account(db, employee_id) void
        +reactivate_employee_account(db, employee_id) void
        +get_all_employees(db, filters) list
        +get_employee_detail(db, profile_id) dict
        +deactivate_employee(db, profile_id) void
    }

    class ProjectService {
        +create_project(db, data) Project
        +update_project(db, project_id, updates) Project
        +get_all_projects(db) list
        +get_project_milestones(db, project_id) dict
    }

    class AllocationService {
        +create_allocation(db, emp_id, proj_id, utilization, from_date, to_date) Allocation
        +end_allocation(db, alloc_id, manager_id) void
    }

    class TimesheetService {
        +submit_timesheet(db, emp_id, week_start, entries) void
        +get_timesheet_history(db, emp_id) list
        +get_missed_weeks(db, emp_id) list
    }

    Employee "1" -- "1" EmployeeProfile : has
    EmployeeProfile "many" --> "0..1" EmployeeProfile : reports to manager_id
    Employee "many" --> "1" Role : associated with
    Role "many" -- "many" Permission : contains
    EmployeeProfile "1" --> "many" Allocation : active in
    Project "1" --> "many" Allocation : has
    Project "1" --> "many" Milestone : contains
    EmployeeProfile "1" --> "many" Timesheet : submits
```

---

## 4. Sequence Diagrams

### 4a. Authentication & Forced Password Change

```mermaid
sequenceDiagram
    actor User
    participant Client as Console Client
    participant AuthAPI as auth_api.py
    participant Server as FastAPI Server
    participant AuthService as auth_service.py
    participant DB as Database

    User->>Client: Enter username & password
    Client->>AuthAPI: login(username, password)
    AuthAPI->>Server: POST /auth/login
    Server->>AuthService: login(db, username, password)
    AuthService->>DB: get_employee_by_username(username)
    DB-->>AuthService: Employee credentials record
    AuthService->>AuthService: verify_password(input, hash)
    alt Password Correct
        AuthService->>AuthService: create_access_token(payload)
        AuthService-->>Server: {token, role (mapped to EMPLOYEE if RESOURCE), force_password_change}
        Server-->>Client: 200 OK + JWT
        alt force_password_change = True
            Client->>User: Prompt: Set new password
            User->>Client: Enter new password + confirm
            Client->>Server: POST /auth/change-password
            Server->>AuthService: change_password(employee_id, new_pw)
            AuthService->>DB: update_employee_password()
            AuthService->>DB: set_employee_force_password_change(False)
            Server-->>Client: 200 OK Password updated
            Client-->>User: ✓ Welcome to the system!
        else Normal Login
            Client-->>User: Redirect to Role Menu
        end
    end
```

---

### 4b. Resource Allocation with Capacity Check

```mermaid
sequenceDiagram
    actor Manager
    participant Client as Console Client
    participant ManagerAPI as manager_api.py
    participant Server as FastAPI Server
    participant AllocService as allocation_service.py
    participant DB as Database

    Manager->>Client: Fill allocation form (employee_id, project_id, %, dates)
    Client->>ManagerAPI: create_allocation(data)
    ManagerAPI->>Server: POST /manager/allocations
    Server->>Server: require_permission("MANAGE_ALLOCATIONS") (JWT Permission check)

    Server->>AllocService: create_allocation(db, employee_id, project_id, utilization, from_date, to_date)
    AllocService->>DB: Verify project manager is current manager
    AllocService->>DB: Get target Employee Profile & Role (must be RESOURCE)
    AllocService->>DB: Get overlapping allocations for employee profile
    AllocService->>AllocService: Sum utilisation %
    alt Total > 100%
        AllocService-->>Server: raise ValueError "Over-utilised"
        Server-->>Client: 400 Bad Request
    else Capacity OK
        AllocService->>DB: Insert new Allocation record
        DB-->>AllocService: Allocation created
        Server-->>Client: 201 Created
        Client-->>Manager: ✓ Allocation saved successfully
    end
```

---

### 4c. Timesheet Submission with Cap Validation

```mermaid
sequenceDiagram
    actor Employee
    participant Client as Console Client
    participant EmpAPI as employee_api.py
    participant Server as FastAPI Server
    participant TSService as timesheet_service.py
    participant DB as Database

    Employee->>Client: Select week, enter hours per project + tags
    Client->>EmpAPI: submit_timesheet(week_start, entries)
    EmpAPI->>Server: POST /employee/timesheets
    Server->>Server: require_permission("SUBMIT_OWN_TIMESHEET")

    loop For each project entry
        Server->>TSService: validate entry
        TSService->>DB: Check active allocation for employee profile + project + week
        TSService->>DB: Check for duplicate submission
        TSService->>TSService: Validate hours <= (allocation utilisation % * max_weekly_hours)
    end

    TSService->>TSService: Validate total hours <= max_weekly_hours
    TSService->>DB: Insert Timesheet records + Tags (single transaction)
    DB-->>TSService: Confirmed
    Server-->>Client: 201 Created
    Client-->>Employee: ✓ Timesheet submitted successfully
```
