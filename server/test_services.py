import unittest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

# Inject app directory to sys.path to run tests standalone
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.models.enums import (
    TimesheetStatus,
    ProjectStatus,
    ProjectHealthStatus,
    MilestoneStatus,
    ProficiencyLevel
)
from app.models.employee import Employee, EmployeeProfile
from app.models.role import Role
from app.models.project import Project, Milestone
from app.models.allocation import Allocation
from app.models.timesheet import Timesheet

# Import services
from app.services import auth_service
from app.services import employee_service
from app.services import project_service
from app.services import allocation_service
from app.services import timesheet_service
from app.services import project_health_service
from app.services import ai_risk_summarizer
from app.services import ai_skill_matcher


class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    def test_validate_password_strength_valid(self):
        # Should not raise ValueError
        auth_service.validate_password_strength("StrongPass1")

    def test_validate_password_strength_too_short(self):
        with self.assertRaises(ValueError) as ctx:
            auth_service.validate_password_strength("Sh1")
        self.assertIn("must be at least", str(ctx.exception))

    def test_validate_password_strength_no_upper(self):
        with self.assertRaises(ValueError) as ctx:
            auth_service.validate_password_strength("weakpass123")
        self.assertIn("uppercase letter", str(ctx.exception))

    def test_validate_password_strength_no_digit(self):
        with self.assertRaises(ValueError) as ctx:
            auth_service.validate_password_strength("WeakpassNoDigit")
        self.assertIn("at least one number", str(ctx.exception))

    @patch("app.services.auth_service.employee_repository")
    @patch("app.services.auth_service.verify_password")
    @patch("app.services.auth_service.create_access_token")
    def test_login_success(self, mock_create_token, mock_verify_pass, mock_repo):
        # Mock user
        mock_role = MagicMock()
        mock_role.name = "RESOURCE"
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_active = True
        mock_user.hashed_password = "hashed_dummy"
        mock_user.role = mock_role
        mock_user.full_name = "Test User"
        mock_user.force_password_change = False

        mock_repo.get_employee_by_username.return_value = mock_user
        mock_verify_pass.return_value = True
        mock_create_token.return_value = "token_abc"

        res = auth_service.login(self.db, "testuser", "Password123")

        self.assertEqual(res["access_token"], "token_abc")
        self.assertEqual(res["role"], "EMPLOYEE")  # RESOURCE maps to EMPLOYEE
        self.assertEqual(res["full_name"], "Test User")
        self.assertEqual(res["force_password_change"], False)

    @patch("app.services.auth_service.employee_repository")
    def test_login_invalid_username(self, mock_repo):
        mock_repo.get_employee_by_username.return_value = None
        with self.assertRaises(ValueError) as ctx:
            auth_service.login(self.db, "nonexistent", "Password123")
        self.assertEqual(str(ctx.exception), "Invalid username or password")

    @patch("app.services.auth_service.employee_repository")
    def test_login_inactive_user(self, mock_repo):
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_repo.get_employee_by_username.return_value = mock_user
        with self.assertRaises(ValueError) as ctx:
            auth_service.login(self.db, "testuser", "Password123")
        self.assertEqual(str(ctx.exception), "Invalid username or password")

    @patch("app.services.auth_service.employee_repository")
    @patch("app.services.auth_service.verify_password")
    def test_login_wrong_password(self, mock_verify_pass, mock_repo):
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.hashed_password = "hashed"
        mock_repo.get_employee_by_username.return_value = mock_user
        mock_verify_pass.return_value = False

        with self.assertRaises(ValueError) as ctx:
            auth_service.login(self.db, "testuser", "WrongPassword")
        self.assertEqual(str(ctx.exception), "Invalid username or password")

    @patch("app.services.auth_service.employee_repository")
    @patch("app.services.auth_service.hash_password")
    def test_change_password(self, mock_hash, mock_repo):
        mock_hash.return_value = "hashed_new"
        auth_service.change_password(self.db, 10, "NewPass123")
        mock_repo.update_employee_password.assert_called_once_with(self.db, 10, "hashed_new")
        mock_repo.set_employee_force_password_change.assert_called_once_with(self.db, 10, False)


class TestEmployeeService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    @patch("app.services.employee_service.employee_repository")
    @patch("app.core.security.hash_password")
    def test_create_employee_success(self, mock_hash, mock_repo):
        mock_hash.return_value = "hashed"
        mock_role = MagicMock()
        mock_role.id = 5
        self.db.query().filter().first.return_value = mock_role

        mock_repo.get_employee_by_username.return_value = None
        mock_repo.get_employee_by_email.return_value = None

        saved_mock = MagicMock()
        saved_mock.id = 100
        mock_repo.save_new_employee.return_value = saved_mock

        emp = employee_service.create_employee(
            self.db,
            full_name="Jane Doe",
            email="jane@example.com",
            username="jane",
            temp_password="Password123",
            role_name="EMPLOYEE",
            department="ENGINEERING"
        )

        mock_repo.save_new_employee.assert_called_once()
        mock_repo.create_employee.assert_called_once_with(self.db, 100, department="ENGINEERING", joined_at=date.today())
        self.assertEqual(emp, saved_mock)

    @patch("app.services.employee_service.employee_repository")
    def test_create_employee_invalid_department(self, mock_repo):
        mock_repo.get_employee_by_username.return_value = None
        mock_repo.get_employee_by_email.return_value = None

        with self.assertRaises(ValueError) as ctx:
            employee_service.create_employee(
                self.db,
                full_name="Jane Doe",
                email="jane@example.com",
                username="jane",
                temp_password="Password123",
                role_name="EMPLOYEE",
                department="INVALID_DEPT"
            )
        self.assertEqual(str(ctx.exception), "Invalid department name")

    @patch("app.services.employee_service.employee_repository")
    def test_create_employee_role_does_not_exist(self, mock_repo):
        mock_repo.get_employee_by_username.return_value = None
        mock_repo.get_employee_by_email.return_value = None
        self.db.query().filter().first.return_value = None

        with self.assertRaises(ValueError) as ctx:
            employee_service.create_employee(
                self.db,
                full_name="Jane Doe",
                email="jane@example.com",
                username="jane",
                temp_password="Password123",
                role_name="MANAGER",
                department="DELIVERY"
            )
        self.assertIn("does not exist", str(ctx.exception))

    @patch("app.services.employee_service.employee_repository")
    def test_create_employee_duplicate_username(self, mock_repo):
        mock_repo.get_employee_by_username.return_value = MagicMock()

        with self.assertRaises(ValueError) as ctx:
            employee_service.create_employee(
                self.db,
                full_name="Jane Doe",
                email="jane@example.com",
                username="jane",
                temp_password="Password123",
                role_name="EMPLOYEE",
                department="ENGINEERING"
            )
        self.assertIn("already taken", str(ctx.exception))

    @patch("app.services.employee_service.employee_repository")
    def test_create_employee_duplicate_email(self, mock_repo):
        mock_repo.get_employee_by_username.return_value = None
        mock_repo.get_employee_by_email.return_value = MagicMock()

        with self.assertRaises(ValueError) as ctx:
            employee_service.create_employee(
                self.db,
                full_name="Jane Doe",
                email="jane@example.com",
                username="jane",
                temp_password="Password123",
                role_name="EMPLOYEE",
                department="ENGINEERING"
            )
        self.assertIn("already registered", str(ctx.exception))

    @patch("app.services.employee_service.employee_repository")
    def test_reset_employee_password(self, mock_repo):
        employee_service.reset_employee_password(self.db, 42, "NewPass123")
        mock_repo.update_employee_password.assert_called_once()
        mock_repo.set_employee_force_password_change.assert_called_once_with(self.db, 42, True)

    @patch("app.services.employee_service.employee_repository")
    @patch("app.services.employee_service.allocation_repository")
    def test_deactivate_employee_account(self, mock_alloc_repo, mock_emp_repo):
        mock_profile = MagicMock()
        mock_profile.id = 99
        mock_emp_repo.get_employee_by_user_id.return_value = mock_profile

        employee_service.deactivate_employee_account(self.db, 12)
        mock_emp_repo.set_employee_active_status.assert_called_once_with(self.db, 12, False)
        mock_alloc_repo.end_all_allocations_for_employee.assert_called_once_with(self.db, 99, date.today())

    @patch("app.services.employee_service.employee_repository")
    def test_reactivate_employee_account(self, mock_emp_repo):
        employee_service.reactivate_employee_account(self.db, 12)
        mock_emp_repo.set_employee_active_status.assert_called_once_with(self.db, 12, True)


class TestProjectService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    @patch("app.services.project_service.project_repository")
    @patch("app.services.project_service.employee_repository")
    def test_create_project_success(self, mock_emp_repo, mock_proj_repo):
        mock_user = MagicMock()
        mock_user.role.name = "MANAGER"
        mock_emp_repo.get_employee_account_by_id.return_value = mock_user

        data = {
            "name": "Project X",
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 6, 1),
            "manager_id": 10
        }
        project_service.create_project(self.db, data)
        mock_proj_repo.create_project.assert_called_once_with(self.db, data)

    def test_create_project_invalid_dates(self):
        data = {
            "name": "Project X",
            "start_date": date(2026, 6, 1),
            "end_date": date(2026, 1, 1),
            "manager_id": 10
        }
        with self.assertRaises(ValueError) as ctx:
            project_service.create_project(self.db, data)
        self.assertEqual(str(ctx.exception), "End date must be after start date")

    @patch("app.services.project_service.employee_repository")
    def test_create_project_not_manager(self, mock_emp_repo):
        mock_user = MagicMock()
        mock_user.role.name = "RESOURCE"
        mock_emp_repo.get_employee_account_by_id.return_value = mock_user

        data = {
            "name": "Project X",
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 6, 1),
            "manager_id": 10
        }
        with self.assertRaises(ValueError) as ctx:
            project_service.create_project(self.db, data)
        self.assertIn("is not a Manager", str(ctx.exception))

    @patch("app.services.project_service.project_repository")
    def test_get_project_milestones_success(self, mock_proj_repo):
        mock_project = MagicMock()
        mock_project.total_story_pts = 100
        mock_proj_repo.get_project_by_id.return_value = mock_project

        mock_m1 = MagicMock()
        mock_m1.status = MilestoneStatus.DONE
        mock_m1.story_points = 30
        mock_m2 = MagicMock()
        mock_m2.status = MilestoneStatus.IN_PROGRESS
        mock_m2.story_points = 70
        mock_proj_repo.get_milestones_for_project.return_value = [mock_m1, mock_m2]

        res = project_service.get_project_milestones(self.db, 55)
        self.assertEqual(res["project"], mock_project)
        self.assertEqual(res["done_story_pts"], 30)
        self.assertEqual(res["remaining_pts"], 70)


class TestAllocationService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    @patch("app.services.allocation_service.employee_repository")
    @patch("app.services.allocation_service.project_repository")
    @patch("app.services.allocation_service.allocation_repository")
    def test_create_allocation_success(self, mock_alloc_repo, mock_proj_repo, mock_emp_repo):
        # Employee Setup
        mock_emp = MagicMock()
        mock_emp.employee.role.name = "RESOURCE"
        mock_emp_repo.get_employee_by_id.return_value = mock_emp

        # Project Setup
        mock_proj = MagicMock()
        mock_proj.status = "ACTIVE"
        mock_proj_repo.get_project_by_id.return_value = mock_proj

        # Capacity checks
        mock_alloc_repo.get_overlapping_allocations.return_value = []

        allocation_service.create_allocation(
            self.db,
            employee_id=1,
            project_id=10,
            utilisation_percent=50,
            from_date=date(2026, 6, 1),
            to_date=date(2026, 8, 1)
        )
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    @patch("app.services.allocation_service.employee_repository")
    def test_create_allocation_invalid_role(self, mock_emp_repo):
        mock_emp = MagicMock()
        mock_emp.employee.role.name = "MANAGER"
        mock_emp_repo.get_employee_by_id.return_value = mock_emp

        with self.assertRaises(ValueError) as ctx:
            allocation_service.create_allocation(
                self.db,
                employee_id=1,
                project_id=10,
                utilisation_percent=50,
                from_date=date(2026, 6, 1),
                to_date=date(2026, 8, 1)
            )
        self.assertIn("only be created for employees/resources", str(ctx.exception))

    @patch("app.services.allocation_service.employee_repository")
    def test_create_allocation_invalid_dates(self, mock_emp_repo):
        mock_emp = MagicMock()
        mock_emp.employee.role.name = "RESOURCE"
        mock_emp_repo.get_employee_by_id.return_value = mock_emp

        with self.assertRaises(ValueError) as ctx:
            allocation_service.create_allocation(
                self.db,
                employee_id=1,
                project_id=10,
                utilisation_percent=50,
                from_date=date(2026, 8, 1),
                to_date=date(2026, 6, 1)
            )
        self.assertEqual(str(ctx.exception), "From date must be before to date")

    @patch("app.services.allocation_service.employee_repository")
    @patch("app.services.allocation_service.allocation_repository")
    def test_create_allocation_exceeds_utilisation(self, mock_alloc_repo, mock_emp_repo):
        mock_emp = MagicMock()
        mock_emp.employee.role.name = "RESOURCE"
        mock_emp_repo.get_employee_by_id.return_value = mock_emp

        mock_alloc = MagicMock()
        mock_alloc.utilisation_percent = 70
        mock_alloc_repo.get_overlapping_allocations.return_value = [mock_alloc]

        with self.assertRaises(ValueError) as ctx:
            allocation_service.create_allocation(
                self.db,
                employee_id=1,
                project_id=10,
                utilisation_percent=40,  # 70 + 40 = 110% (> 100)
                from_date=date(2026, 6, 1),
                to_date=date(2026, 8, 1)
            )
        self.assertIn("Maximum allowed is 100%", str(ctx.exception))

    @patch("app.services.allocation_service.project_repository")
    def test_end_allocation_success(self, mock_proj_repo):
        mock_alloc = MagicMock()
        mock_alloc.id = 5
        mock_alloc.project_id = 10
        mock_alloc.employee_id = 1
        self.db.query().filter().first.return_value = mock_alloc

        mock_proj = MagicMock()
        mock_proj.manager_id = 88
        mock_proj_repo.get_project_by_id.return_value = mock_proj

        allocation_service.end_allocation(self.db, 5, 88)
        self.db.commit.assert_called_once()

    def test_end_allocation_not_found(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(ValueError) as ctx:
            allocation_service.end_allocation(self.db, 999, 88)
        self.assertIn("not found", str(ctx.exception))


class TestTimesheetService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.query().filter().first.return_value = None

    @patch("app.repositories.employee_repository.get_employee_by_id")
    @patch("app.services.timesheet_service.allocation_repository")
    @patch("app.services.timesheet_service.timesheet_repository")
    def test_submit_timesheet_success(self, mock_timesheet_repo, mock_alloc_repo, mock_get_employee):
        # Profile mock
        mock_profile = MagicMock()
        mock_profile.employee.role.name = "RESOURCE"
        mock_get_employee.return_value = mock_profile

        # Allocations Mock
        mock_alloc = MagicMock()
        mock_alloc.project_id = 10
        mock_alloc.from_date = date(2026, 6, 1)
        mock_alloc.to_date = date(2026, 6, 30)
        mock_alloc.max_hours = 20
        mock_alloc.utilisation_percent = 50
        mock_alloc_repo.get_active_allocations_for_employee.return_value = [mock_alloc]

        # No duplicate
        mock_timesheet_repo.get_timesheet_for_week.return_value = None

        mock_saved_timesheet = MagicMock()
        mock_saved_timesheet.id = 200
        mock_timesheet_repo.save_timesheet.return_value = mock_saved_timesheet

        entries = [{"project_id": 10, "hours_worked": 15, "tags": ["Backend"]}]
        timesheet_service.submit_timesheet(self.db, 1, date(2026, 6, 8), entries)

        mock_timesheet_repo.save_timesheet.assert_called_once()
        mock_timesheet_repo.save_tags.assert_called_once_with(self.db, 200, ["Backend"])

    @patch("app.repositories.employee_repository.get_employee_by_id")
    def test_submit_timesheet_future_week(self, mock_get_employee):
        mock_profile = MagicMock()
        mock_profile.employee.role.name = "RESOURCE"
        mock_get_employee.return_value = mock_profile

        future_date = date.today() + timedelta(days=7)
        entries = [{"project_id": 10, "hours_worked": 15}]

        with self.assertRaises(ValueError) as ctx:
            timesheet_service.submit_timesheet(self.db, 1, future_date, entries)
        self.assertEqual(str(ctx.exception), "Cannot submit a timesheet for a future week")


class TestProjectHealthService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    @patch("app.services.project_health_service.project_repository")
    @patch("app.services.project_health_service.allocation_repository")
    def test_compute_health_for_project_on_track(self, mock_alloc_repo, mock_proj_repo):
        # Milestones: none overdue
        mock_proj_repo.get_milestones_for_project.return_value = []
        mock_alloc_repo.get_all_allocations.return_value = []
        mock_proj = MagicMock()
        mock_proj.total_story_pts = 100
        mock_proj.end_date = date.today() + timedelta(days=45) # safe
        mock_proj_repo.get_project_by_id.return_value = mock_proj

        health = project_health_service.compute_health_for_project(self.db, 1)
        self.assertEqual(health, ProjectHealthStatus.ON_TRACK)

    @patch("app.services.project_health_service.project_repository")
    def test_compute_health_for_project_at_risk_overdue(self, mock_proj_repo):
        # Milestones: one overdue
        mock_m = MagicMock()
        mock_m.status = MilestoneStatus.NOT_STARTED
        mock_m.due_date = date.today() - timedelta(days=1)
        mock_proj_repo.get_milestones_for_project.return_value = [mock_m]

        health = project_health_service.compute_health_for_project(self.db, 1)
        self.assertEqual(health, ProjectHealthStatus.AT_RISK)


class TestAiRiskSummarizer(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    @patch("app.services.ai_risk_summarizer.project_repository")
    @patch("app.services.ai_risk_summarizer.collect_risk_flags")
    @patch("app.services.ai_risk_summarizer.get_llm_adapter")
    def test_generate_risk_summary(self, mock_get_adapter, mock_collect_flags, mock_proj_repo):
        mock_project = MagicMock()
        mock_project.name = "Project Testing"
        mock_project.end_date = date(2026, 12, 31)
        mock_proj_repo.get_project_by_id.return_value = mock_project
        mock_proj_repo.get_milestones_for_project.return_value = []
        mock_collect_flags.return_value = ["Backend overdue by 2 days"]

        mock_llm = MagicMock()
        mock_llm.complete.return_value = "This is a mock AI summary paragraph explaining risks."
        mock_get_adapter.return_value = mock_llm

        summary = ai_risk_summarizer.generate_risk_summary(self.db, 1)
        self.assertEqual(summary, "This is a mock AI summary paragraph explaining risks.")
        mock_llm.complete.assert_called_once()


class TestAiSkillMatcher(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    def test_parse_requested_hours(self):
        self.assertEqual(ai_skill_matcher.parse_requested_hours("I need a developer for 15 hrs/week"), 15)
        self.assertEqual(ai_skill_matcher.parse_requested_hours("We need ten hours per week of testing"), 10)
        self.assertEqual(ai_skill_matcher.parse_requested_hours("We need a developer full time"), 0)

    @patch("app.services.ai_skill_matcher.employee_repository")
    @patch("app.services.ai_skill_matcher.allocation_repository")
    @patch("app.services.ai_skill_matcher.get_llm_adapter")
    def test_find_best_matches_success(self, mock_get_adapter, mock_alloc_repo, mock_emp_repo):
        # Mock employee
        mock_emp = MagicMock()
        mock_emp.id = 1
        mock_emp.user.full_name = "Alice Smith"
        mock_emp.skills = []
        mock_emp_repo.get_employees_by_manager.return_value = [mock_emp]

        # Allocation checks -> fully free
        mock_alloc_repo.get_active_allocations_for_employee.return_value = []

        mock_llm = MagicMock()
        mock_llm.complete.return_value = '[{"name": "Alice Smith", "reason": "Good match.", "suggested_allocation_pct": 50}]'
        mock_get_adapter.return_value = mock_llm

        res = ai_skill_matcher.find_best_matches(self.db, "Need Python dev 10 hrs/week", 5)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "Alice Smith")
        self.assertEqual(res[0]["suggested_allocation_pct"], 50)


if __name__ == "__main__":
    unittest.main()
