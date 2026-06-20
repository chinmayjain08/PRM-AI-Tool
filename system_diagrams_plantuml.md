# PRM Tool — PlantUML System Diagrams

This document contains the complete visual representation of the PRM Tool architecture, data models, workflows, and user interactions in **PlantUML** format.

---

## 1. Use Case Diagram

```plantuml
@startuml PRM_UseCaseDiagram

skinparam actorStyle awesome
skinparam defaultTextAlignment center
skinparam usecase {
    BackgroundColor #EEF3FF
    BorderColor     #3B4DB8
    ArrowColor      #3B4DB8
    FontSize        12
}
skinparam actor {
    BackgroundColor #FAFAFA
    BorderColor     #3B4DB8
    FontSize        12
    FontStyle       bold
}
skinparam package {
    BackgroundColor #F7F9FF
    BorderColor     #9099CC
    FontSize        11
    FontStyle       bold
}

actor "Admin"          as A
actor "Manager"        as M
actor "Employee"       as E
actor ":Scheduler\n(System Clock)" as S

rectangle "PRM Tool — Project & Resource Management System" {

    package "Authentication" <<Rectangle>> {
        usecase "Login"                       as UC_Login
        usecase "Validate Credentials"       as UC_ValidateCreds
        usecase "Change Password"             as UC_ChangePwd
        usecase "Validate Password Strength" as UC_ValidatePwdStr
    }

    package "User & Employee Management" <<Rectangle>> {
        usecase "Create Employee Account & Profile" as UC_CreateUser
        usecase "Reset Credentials Password"     as UC_ResetPwd
        usecase "Deactivate Employee Account"    as UC_Deactivate
        usecase "Assign Manager to Profile"      as UC_AssignMgr
        usecase "Manage Employee Skills"          as UC_ManageSkills
    }

    package "Project Administration" <<Rectangle>> {
        usecase "Create / Update Project"         as UC_ManageProject
        usecase "Add Milestone to Project"        as UC_AddMilestone
        usecase "View All Allocations"            as UC_ViewAllAlloc
    }

    usecase "Configure System Settings"           as UC_ConfigSystem

    package "Resource Management" <<Rectangle>> {
        usecase "View Resource Dashboard"         as UC_Dashboard
        usecase "Allocate Resource to Project"    as UC_Allocate
        usecase "Validate Capacity (100% cap)"   as UC_ValidateCap
        usecase "Terminate Allocation"            as UC_TerminateAlloc
    }

    package "Project Monitoring" <<Rectangle>> {
        usecase "View Projects & Health Status"   as UC_ViewProjects
        usecase "View Team Timesheets"            as UC_ViewTeamTS
    }

    package "AI-Assisted Features" <<Rectangle>> {
        usecase "AI Skill Match Query"            as UC_SkillMatch
        usecase "AI Project Risk Summary"         as UC_RiskSummary
        usecase "Filter by Free Capacity"         as UC_FilterCap
        usecase "Collect Risk Flags"              as UC_CollectFlags
    }

    package "Timesheet Management" <<Rectangle>> {
        usecase "Submit Weekly Timesheet"         as UC_SubmitTS
        usecase "Validate Timesheet Entry"        as UC_ValidateEntry
        usecase "Check Not Future Week"           as UC_FutureWeek
        usecase "Check Active Allocation"         as UC_CheckAlloc
        usecase "Check Hours Cap"                 as UC_HoursCap
        usecase "Prevent Duplicate Submission"    as UC_NoDuplicate
        usecase "View Timesheet History"          as UC_TSHistory
        usecase "Check Missed Weeks"              as UC_MissedWeeks
    }

    usecase "View My Allocations"                 as UC_ViewMyAlloc

    package "Background Scheduled Jobs" <<Rectangle>> {
        usecase "Flag Missed Timesheets"          as UC_FlagMissed
        usecase "Update Project Health Status"    as UC_UpdateHealth
        usecase "Recompute Employee Status"       as UC_RecomputeStatus
    }
}

A --> UC_Login
A --> UC_ChangePwd
A --> UC_CreateUser
A --> UC_ResetPwd
A --> UC_Deactivate
A --> UC_AssignMgr
A --> UC_ManageSkills
A --> UC_ManageProject
A --> UC_AddMilestone
A --> UC_ViewAllAlloc
A --> UC_ConfigSystem

M --> UC_Login
M --> UC_ChangePwd
M --> UC_Dashboard
M --> UC_Allocate
M --> UC_TerminateAlloc
M --> UC_ViewProjects
M --> UC_ViewTeamTS
M --> UC_SkillMatch
M --> UC_RiskSummary

E --> UC_Login
E --> UC_ChangePwd
E --> UC_SubmitTS
E --> UC_TSHistory
E --> UC_MissedWeeks
E --> UC_ViewMyAlloc

S --> UC_FlagMissed
S --> UC_UpdateHealth
S --> UC_RecomputeStatus

UC_Login      ..>  UC_ValidateCreds     : <<include>>
UC_ChangePwd  ..>  UC_ValidatePwdStr    : <<include>>
UC_ResetPwd   ..>  UC_ValidatePwdStr    : <<include>>
UC_CreateUser ..>  UC_ValidatePwdStr    : <<include>>
UC_Allocate   ..>  UC_ValidateCap       : <<include>>
UC_SubmitTS   ..>  UC_ValidateEntry     : <<include>>
UC_ValidateEntry ..> UC_FutureWeek      : <<include>>
UC_ValidateEntry ..> UC_CheckAlloc      : <<include>>
UC_ValidateEntry ..> UC_HoursCap        : <<include>>
UC_ValidateEntry ..> UC_NoDuplicate     : <<include>>
UC_SkillMatch ..>  UC_FilterCap         : <<include>>
UC_RiskSummary ..> UC_CollectFlags      : <<include>>

UC_ChangePwd  ..>  UC_Login             : <<extend>>\n{condition: force_password_change = True}
M -up-|> A : generalizes

@enduml
```

---

## 2. Entity-Relationship (ER) Diagram

```plantuml
@startuml PRM_ERD
!theme plain
hide circle
skinparam linetype ortho

entity "employees" as employees {
  * id : int <<PK>>
  --
  * username : varchar <<UK>>
  * email : varchar <<UK>>
  * full_name : varchar
  * hashed_password : varchar
  * role_id : int <<FK>>
  * is_active : bool
  * force_password_change : bool
  * created_at : timestamp
}

entity "employee_profiles" as employee_profiles {
  * id : int <<PK>>
  --
  * employee_id : int <<FK, UK>>
  * department : varchar
  manager_id : int <<FK>>
  * joined_at : date
}

entity "roles" as roles {
  * id : int <<PK>>
  --
  * name : varchar <<UK>>
}

entity "permissions" as permissions {
  * id : int <<PK>>
  --
  * name : varchar <<UK>>
  description : varchar
}

entity "role_permissions" as role_permissions {
  * role_id : int <<PK, FK>>
  * permission_id : int <<PK, FK>>
}

entity "skills" as skills {
  * id : int <<PK>>
  --
  * name : varchar <<UK>>
  * category : varchar
}

entity "employee_skills" as employee_skills {
  * employee_id : int <<PK, FK>>
  * skill_id : int <<PK, FK>>
  --
  * proficiency : varchar
}

entity "projects" as projects {
  * id : int <<PK>>
  --
  * name : varchar
  description : text
  * start_date : date
  end_date : date
  * status : varchar
  * manager_id : int <<FK>>
  * total_story_pts : int
  * health_status : varchar
}

entity "milestones" as milestones {
  * id : int <<PK>>
  --
  * project_id : int <<FK>>
  * title : varchar
  * due_date : date
  * story_points : int
  * status : varchar
}

entity "allocations" as allocations {
  * id : int <<PK>>
  --
  * employee_id : int <<FK>>
  * project_id : int <<FK>>
  * utilisation_percent : int
  * from_date : date
  * to_date : date
  * is_active : bool
}

entity "timesheets" as timesheets {
  * id : int <<PK>>
  --
  * employee_id : int <<FK>>
  * project_id : int <<FK>>
  * week_start : date
  * hours_worked : int
  * status : varchar
  submitted_at : timestamp
}

entity "timesheet_tags" as timesheet_tags {
  * id : int <<PK>>
  --
  * timesheet_id : int <<FK>>
  * tag : varchar
}

entity "system_config" as system_config {
  * id : int <<PK>>
  --
  * max_weekly_hours : int
  * llm_provider : varchar
  * llm_api_key : text
  * scheduler_interval : int
}

roles ||--o{ employees : "defines role of"
employees ||--|| employee_profiles : "has profile"
employee_profiles |o--o{ employee_profiles : "reports to"
roles ||--o{ role_permissions : "contains"
permissions ||--o{ role_permissions : "maps to"
employee_profiles ||--o{ employee_skills : "has skills"
skills ||--o{ employee_skills : "belongs to"
employees ||--o{ projects : "manages"
employee_profiles ||--o{ allocations : "allocated in"
projects ||--o{ allocations : "receives"
projects ||--o{ milestones : "has"
employee_profiles ||--o{ timesheets : "logs"
projects ||--o{ timesheets : "tracked by"
timesheets ||--o{ timesheet_tags : "tagged with"
@enduml
```

---

## 3. Class Diagram

```plantuml
@startuml PRM_ClassDiagram

skinparam classAttributeIconSize 0
skinparam defaultTextAlignment  left

class Employee {
  +id : int
  +username : str
  +email : str
  +full_name : str
  +hashed_password : str
  +role_id : int
  +is_active : bool
  +force_password_change : bool
  +created_at : datetime
}

class EmployeeProfile {
  +id : int
  +employee_id : int
  +department : str
  +manager_id : int
  +joined_at : date
}

class Role {
  +id : int
  +name : str
}

class Permission {
  +id : int
  +name : str
  +description : str
}

class Project {
  +id : int
  +name : str
  +status : str
  +health_status : str
  +manager_id : int
  +total_story_pts : int
}

class Allocation {
  +id : int
  +employee_id : int
  +project_id : int
  +utilisation_percent : int
  +from_date : date
  +to_date : date
  +is_active : bool
}

class Timesheet {
  +id : int
  +employee_id : int
  +project_id : int
  +week_start : date
  +hours_worked : int
  +status : str
}

class Milestone {
  +id : int
  +project_id : int
  +title : str
  +due_date : date
  +status : str
}

Employee "1" -- "1" EmployeeProfile : has
EmployeeProfile "many" --> "0..1" EmployeeProfile : reports to manager_id
Employee "many" --> "1" Role : associated with
Role "many" -- "many" Permission : contains
EmployeeProfile "1" --> "many" Allocation : active in
Project "1" --> "many" Allocation : has
Project "1" --> "many" Milestone : contains
EmployeeProfile "1" --> "many" Timesheet : submits

@enduml
```
