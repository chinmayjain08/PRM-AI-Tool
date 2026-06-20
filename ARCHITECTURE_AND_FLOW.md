# Project Architecture & Complete Workflow Guide (PRM Tool)

> **Who is this for?**
> This document is written for a developer who wants to understand the backend architecture of this project, specifically the separation of credentials from business data, and how permissions are enforced dynamically.

---

## Table of Contents

1. [The Big Picture — What Does This Application Do?](#1-the-big-picture)
2. [How the Two Sides Talk to Each Other (Client ↔ Server)](#2-client-server-communication)
3. [The Layered Architecture — The Golden Rule of This Project](#3-the-layered-architecture)
4. [Layer 1 — The Database (SQLAlchemy Models)](#4-layer-1-the-database)
5. [Layer 2 — Repositories (The SQL Writers)](#5-layer-2-repositories)
6. [Layer 3 — Services (The Business Rule Enforcers)](#6-layer-3-services)
7. [Layer 4 — Routers (The HTTP Gatekeepers)](#7-layer-4-routers)
8. [The Security System — JWT Tokens & Dynamic Permissions](#8-the-security-system)
9. [The LLM / AI Service — Factory + Adapter + OCP](#9-the-llm-ai-service)
10. [The Background Scheduler — Automated Jobs](#10-the-background-scheduler)
11. [Complete Workflow Walkthroughs (Step-by-Step)](#11-workflow-walkthroughs)
    - [A. Login & Forced Password Change](#a-login--forced-password-change)
    - [B. Admin Creates an Employee Account](#b-admin-creates-an-employee-account)
    - [C. Manager Allocates a Resource to a Project](#c-manager-allocates-a-resource-to-a-project)
    - [D. Resource Submits a Weekly Timesheet](#d-resource-submits-a-weekly-timesheet)
12. [The Console Client — How Users Interact](#12-the-console-client)

---

## 1. The Big Picture

The **PRM Tool (Project & Resource Management Tool)** is a full-stack Python application built for managing an organisation's projects, employees, and workload. 

It has **two sides**:
* **Client**: A Python console app (`client/main.py`) presenting terminal menus.
* **Server**: A FastAPI REST API (`server/main.py`) backed by a PostgreSQL database.

Under the hood, we split login credentials from business profile data and check dynamic fine-grained permissions instead of hardcoded roles.

---

## 2. Client-Server Communication

* **REST API**: The client makes HTTP calls (`GET`, `POST`, `PUT`, `DELETE`) to the server.
* **Role Aliasing for Compatibility**: The database contains roles `ADMIN`, `MANAGER`, and `RESOURCE`. However, because the client menu system expects role strings like `ADMIN`, `MANAGER`, and `EMPLOYEE`, the server dynamically maps `RESOURCE` to `EMPLOYEE` in all client-facing responses. When the client makes requests, the server maps `EMPLOYEE` inputs back to `RESOURCE`.
* **JWT Token**: Login returns a JWT containing the user's role. Future requests send this token in the `Authorization: Bearer` header.

---

## 3. The Layered Architecture

Each layer has exactly one job:

1. **HTTP Router Layer (`server/app/api/`)**: Thin controllers handling HTTP requests, body serialization via Pydantic schemas, and permission dependencies. No SQL or business logic.
2. **Service Layer (`server/app/services/`)**: Enforces validation constraints and business logic rules. Decoupled from HTTP context (raises `ValueError` on validation failure).
3. **Repository Layer (`server/app/repositories/`)**: Encapsulates raw database queries via SQLAlchemy. No business logic or HTTP concepts.

---

## 4. Layer 1 — The Database

The database is built on SQLAlchemy models in `server/app/models/`:

* `Role`: Database representation of system roles (`ADMIN`, `MANAGER`, `RESOURCE`).
* `Permission`: Specific operations (e.g. `SUBMIT_OWN_TIMESHEET`, `MANAGE_EMPLOYEES`).
* `RolePermission`: Many-to-many junction mapping permissions to roles.
* `Employee`: Authentication details and credentials (username, email, hashed_password, role_id, is_active, force_password_change).
* `EmployeeProfile`: Business details (department: ENGINEERING, DELIVERY, HR, FINANCE, OPERATIONS; manager_id referencing another manager's profile; joined_at). Maps 1-to-1 with `Employee` credentials.
* `Skill` & `EmployeeSkill`: Global skill directory and employee skill levels (Beginner, Intermediate, Advanced).
* `Project`: Project details, including start/end dates and health status, managed by a MANAGER employee.
* `Milestone`: Project deliverables (NOT_STARTED, IN_PROGRESS, DONE).
* `Allocation`: Project allocation details (utilisation %, start/end dates, active status) referencing an `EmployeeProfile`. Only `RESOURCE` accounts can have allocations.
* `Timesheet` & `TimesheetTag`: Timesheet submission data (week_start, hours_worked) and optional tags. Only `RESOURCE` accounts can submit timesheets.
* `SystemConfig`: Dynamic configurations (API key, maximum weekly hours).

---

## 5. Layer 2 — Repositories

All database operations are encapsulated inside repositories (`server/app/repositories/`).
* `employee_repository.py` contains credential and profile operations, replacing the retired `user_repository.py`.
* `allocation_repository.py` retrieves allocations, check overlaps, and handles deactivations.
* `timesheet_repository.py` handles weekly logs, tag saving, and hours lookup.
* `project_repository.py` retrieves projects and milestone updates.
* `skill_repository.py` manages skill lookup and employee skill profiles.

---

## 6. Layer 3 — Services

Enforces business rule constraints:
* `auth_service.py` handles login logic, password hashing, strength checks, and role mapping.
* `employee_service.py` coordinates credentials account creation alongside profile initialization, password resets, and cascades (deactivating credentials terminates allocations).
* `allocation_service.py` checks that only `RESOURCE` profiles are allocated, and that total utilization does not exceed 100%.
* `timesheet_service.py` verifies that only `RESOURCE` accounts submit hours, that hours are logged only on active projects, and that log counts do not exceed cap calculations.
* `project_health_service.py` updates project flags (e.g. AT_RISK or ATTENTION).

---

## 7. Layer 4 — Routers

Routers map incoming paths to service logic:
* `auth_router.py` exposes `/login` and `/change-password` routes.
* `admin_router.py` guards user creation, deactivation, and system config with dependencies checking permissions like `MANAGE_EMPLOYEES` or `MANAGE_SYSTEM_CONFIG`.
* `manager_router.py` guards manager dashboards and allocations with permissions like `VIEW_TEAM` or `MANAGE_ALLOCATIONS`.
* `employee_router.py` maps timesheets and skills with permissions like `SUBMIT_OWN_TIMESHEET`.

---

## 8. The Security System

### Dynamic Permissions Checking

We protect endpoints with `Depends(require_permission("PERMISSION_NAME"))`:

```python
def require_permission(permission_name: str):
    def dependency(current_user: Employee = Depends(get_current_user)) -> Employee:
        if not current_user.role or not any(p.name == permission_name for p in current_user.role.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required"
            )
        return current_user
    return dependency
```

FastAPI resolves this dependency before running the controller. If the user's role does not possess the mapped permission, a `403 Forbidden` error is returned automatically.

---

## 9. The LLM / AI Service

AI features (Skill Matcher and Risk Summarizer) are powered by the **Adapter Pattern** (`GeminiAdapter`, `GroqAdapter` extending `LLMAdapter`) and the **Factory Pattern** (`LLMAdapterFactory` reading database provider configurations). Services interact strictly with the abstract `LLMAdapter` contract, ensuring compliance with the Open/Closed Principle.

---

## 10. The Background Scheduler

The scheduler (`server/app/core/scheduler.py`) runs on a background loop. It:
1. **Computes Employee Statuses**: Checks active allocations to mark profiles.
2. **Flags Missed Timesheets**: Finds resources with active allocations who missed submitting hours for the previous week and inserts `MISSED` logs.
3. **Recomputes Project Health**: Flags ACTIVE projects as `AT_RISK` (overdue milestones, low logged effort) or `ATTENTION` (approaching deadline with low story points done).

---

## 11. Complete Workflow Walkthroughs

### A. Login & Forced Password Change
1. User enters username and password in the client.
2. Client posts to `/auth/login`.
3. `auth_service.login()` verifies credentials.
4. If role is `RESOURCE`, maps it to `"EMPLOYEE"` in the JSON response payload.
5. If `force_password_change` is `True`, client prompts the user to enter a new password.
6. Client posts new password to `/auth/change-password`.
7. `auth_service.change_password()` validates password strength, hashes it, updates database, and clears the change flag.
8. Client receives success and launches the corresponding role menu.

### B. Admin Creates an Employee Account
1. Admin enters profile details (role selected from ADMIN, MANAGER, EMPLOYEE).
2. Client posts payload containing `role` (e.g. `"EMPLOYEE"`) to `/admin/users`.
3. Server maps `"EMPLOYEE"` to `"RESOURCE"`.
4. `employee_service.create_employee()` inserts an `Employee` credentials record, hashes the temporary password, and inserts a matching `EmployeeProfile` with a default department.
5. Success returned to client.

### C. Manager Allocates a Resource to a Project
1. Manager selects a project and resource, specifying utilisation % and dates.
2. Client posts to `/manager/allocations`.
3. `allocation_service.create_allocation()` validates:
   - Resource has `RESOURCE` database role.
   - Utilisation does not exceed 100% across overlapping dates.
   - Project belongs to the manager and is active/planned.
4. Record inserted into `allocations` table.

### D. Resource Submits a Weekly Timesheet
1. Resource enters hours and tags for projects.
2. Client posts to `/employee/timesheets`.
3. `timesheet_service.submit_timesheet()` validates:
   - User has `RESOURCE` role.
   - Week is not in the future.
   - User is allocated to the project during the selected week.
   - Logged hours do not exceed project allocation limits.
   - Total logged hours do not exceed the weekly configuration cap.
4. Record committed to `timesheets` and `timesheet_tags`.

---

## 12. The Console Client

The client app (`client/`) is purely presentational:
* Draws borders, options, and tables.
* Wraps endpoint interactions inside `HttpClient` with automatic JWT header handling.
* Routes users using a dispatch mapping (`ROLE_TO_MENU`).
