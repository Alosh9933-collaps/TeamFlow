from unittest.mock import patch
from rest_framework.test import APIClient
from django.test import TestCase
from django.test import SimpleTestCase
from apps.projects.ai_planner import generate_task_suggestions

from django.urls import reverse
from apps.notifications.models import Notification
from apps.activity.models import ActivityLog
from apps.accounts.models import User
from apps.projects.models import (
    Project,
    ProjectJoinRequest,
    ProjectMembership,
)
from apps.projects.services import (
    approve_project_join_request,
    create_project_join_request,
)
from apps.teams.models import (
    Team,
    TeamMembership,
)

class ApproveProjectJoinRequestTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        self.ali = User.objects.create_user(
            username="ali",
            password="password123",
        )

        self.ahmed = User.objects.create_user(
            username="ahmed",
            password="password123",
        )

        self.outsider = User.objects.create_user(
            username="outsider",
            password="password123",
        )

        self.team = Team.objects.create(
            name="Backend Team",
        )

        TeamMembership.objects.create(
            user=self.ali,
            team=self.team,
            role=TeamMembership.Role.OWNER,
        )

        TeamMembership.objects.create(
            user=self.ahmed,
            team=self.team,
            role=TeamMembership.Role.MEMBER,
        )

        self.project = Project.objects.create(
            team=self.team,
            name="TeamFlow API",
            description="Main backend project",
            created_by=self.ali,
        )

        ProjectMembership.objects.create(
            user=self.ali,
            project=self.project,
            role=ProjectMembership.Role.MANAGER,
        )

        self.join_request = ProjectJoinRequest.objects.create(
            user=self.ahmed,
            project=self.project,
        )

    def test_manager_can_approve_join_request(self):

        membership = approve_project_join_request(
            join_request_id=self.join_request.id,
            reviewer=self.ali,
        )

        self.assertEqual(
            membership.user,
            self.ahmed,
        )

        self.assertEqual(
            membership.project,
            self.project,
        )

        self.assertEqual(
            membership.role,
            ProjectMembership.Role.MEMBER,
        )

        self.join_request.refresh_from_db()

        self.assertEqual(
            self.join_request.status,
            ProjectJoinRequest.Status.APPROVED,
        )

        self.assertEqual(
            self.join_request.reviewed_by,
            self.ali,
        )

        self.assertIsNotNone(
            self.join_request.reviewed_at,
        )

        notification = Notification.objects.get(
            recipient=self.ahmed,
            notification_type=(
                Notification.NotificationType
                .JOIN_REQUEST_APPROVED
            ),
            object_id=self.project.id,
        )

        self.assertEqual(
            notification.actor,
            self.ali,
        )

        self.assertEqual(
            notification.target,
            self.project,
        )

        self.assertEqual(
            notification.metadata["project_id"],
            self.project.id,
        )

        self.assertEqual(
            notification.metadata["project_name"],
            self.project.name,
        )

        self.assertIsNone(
            notification.read_at,
        )

    def test_non_manager_cannot_approve_join_request(self):

        with self.assertRaises(PermissionError):
            approve_project_join_request(
                join_request_id=self.join_request.id,
                reviewer=self.ahmed,
            )

    def test_cannot_approve_non_pending_request(self):

        self.join_request.status = (
            ProjectJoinRequest.Status.REJECTED
        )

        self.join_request.save()

        with self.assertRaises(ValueError):
            approve_project_join_request(
                join_request_id=self.join_request.id,
                reviewer=self.ali,
            )

    def test_cannot_approve_when_user_is_already_project_member(self):

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        with self.assertRaises(ValueError):
            approve_project_join_request(
                join_request_id=self.join_request.id,
                reviewer=self.ali,
            )

    def test_approval_rolls_back_when_request_update_fails(self):

        with patch(
            "apps.projects.services.ProjectJoinRequest.save",
            side_effect=Exception("Database update failed"),
        ):

            with self.assertRaises(Exception):
                approve_project_join_request(
                    join_request_id=self.join_request.id,
                    reviewer=self.ali,
                )

        self.join_request.refresh_from_db()

        self.assertEqual(
            self.join_request.status,
            ProjectJoinRequest.Status.PENDING,
        )

        self.assertFalse(
            ProjectMembership.objects.filter(
                user=self.ahmed,
                project=self.project,
            ).exists()
        )

    def test_non_team_member_cannot_request_project_access(self):

        with self.assertRaises(PermissionError):
            create_project_join_request(
                user=self.outsider,
                project=self.project,
            )

    def test_team_member_can_request_project_access(self):

        sara = User.objects.create_user(
            username="sara",
            password="password123",
        )

        TeamMembership.objects.create(
            user=sara,
            team=self.team,
            role=TeamMembership.Role.MEMBER,
        )

        new_request = create_project_join_request(
            user=sara,
            project=self.project,
        )

        self.assertEqual(
            new_request.status,
            ProjectJoinRequest.Status.PENDING,
        )

    def test_project_member_cannot_request_again(self):

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        with self.assertRaises(ValueError):
            create_project_join_request(
                user=self.ahmed,
                project=self.project,
            )

    def test_team_member_can_create_join_request_through_api(self):

        sara = User.objects.create_user(
            username="sara",
            password="password123",
        )

        TeamMembership.objects.create(
            user=sara,
            team=self.team,
            role=TeamMembership.Role.MEMBER,
        )

        self.client.force_authenticate(
            user=sara
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/join-request/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["status"],
            ProjectJoinRequest.Status.PENDING,
        )

    def test_non_team_member_cannot_create_join_request_through_api(self):

        self.client.force_authenticate(
            user=self.outsider
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/join-request/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_can_approve_join_request_through_api(self):

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/join-request/"
            f"{self.join_request.id}/approve/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.join_request.refresh_from_db()

        self.assertEqual(
            self.join_request.status,
            ProjectJoinRequest.Status.APPROVED,
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                user=self.ahmed,
                project=self.project,
            ).exists()
        )

    def test_project_member_cannot_approve_join_request_through_api(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/join-request/"
            f"{self.join_request.id}/approve/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.join_request.refresh_from_db()

        self.assertEqual(
            self.join_request.status,
            ProjectJoinRequest.Status.PENDING,
        )

    def test_cannot_approve_join_request_from_another_project(self):

        other_project = Project.objects.create(
            team=self.team,
            name="Another Project",
            description="Another project",
            created_by=self.ali,
        )

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            f"/api/projects/{other_project.id}/join-request/"
            f"{self.join_request.id}/approve/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_team_owner_can_create_project(self):

        client = APIClient()

        client.force_authenticate(
            user=self.ali
        )

        response = client.post(
            "/api/projects/",
            {
                "team": self.team.id,
                "name": "New Project",
                "description": "Project description",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        project = Project.objects.get(
            name="New Project"
        )

        self.assertEqual(
            project.created_by,
            self.ali,
        )

        self.assertTrue(
            ProjectMembership.objects.filter(
                user=self.ali,
                project=project,
                role=ProjectMembership.Role.MANAGER,
            ).exists()
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                actor=self.ali,
                action=ActivityLog.Action.CREATED,
                object_id=project.id,
            ).exists()
        )

    def test_team_member_cannot_create_project(self):

        client = APIClient()

        client.force_authenticate(
            user=self.ahmed
        )

        response = client.post(
            "/api/projects/",
            {
                "team": self.team.id,
                "name": "Unauthorized Project",
                "description": "Should fail",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_outsider_cannot_create_project(self):

        client = APIClient()

        client.force_authenticate(
            user=self.outsider
        )

        response = client.post(
            "/api/projects/",
            {
                "team": self.team.id,
                "name": "Unauthorized Project",
                "description": "Should fail",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            Project.objects.filter(
                name="Unauthorized Project"
            ).exists()
        )

    def test_project_manager_can_update_project(self):

        client = APIClient()

        client.force_authenticate(
            user=self.ali
        )

        response = client.patch(
            f"/api/projects/{self.project.id}/",
            {
                "name": "Updated Project",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.project.refresh_from_db()

        self.assertEqual(
            self.project.name,
            "Updated Project",
        )

    def test_project_member_cannot_update_project(self):

        client = APIClient()

        client.force_authenticate(
            user=self.ahmed
        )

        response = client.patch(
            f"/api/projects/{self.project.id}/",
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_from_another_team_cannot_access_project(self):

        client = APIClient()

        client.force_authenticate(
            user=self.outsider
        )

        response = client.get(
            f"/api/projects/{self.project.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

class ProjectMemberManagementTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        self.ali = User.objects.create_user(
            username="ali",
            password="password123",
        )

        self.ahmed = User.objects.create_user(
            username="ahmed",
            password="password123",
        )

        self.sara = User.objects.create_user(
            username="sara",
            password="password123",
        )


        self.team = Team.objects.create(
            name="Backend Team",
        )


        TeamMembership.objects.create(
            user=self.ali,
            team=self.team,
            role=TeamMembership.Role.OWNER,
        )


        TeamMembership.objects.create(
            user=self.ahmed,
            team=self.team,
            role=TeamMembership.Role.MEMBER,
        )


        self.project = Project.objects.create(
            team=self.team,
            name="TeamFlow API",
            description="Backend",
            created_by=self.ali,
        )


        ProjectMembership.objects.create(
            user=self.ali,
            project=self.project,
            role=ProjectMembership.Role.MANAGER,
        )

    def test_manager_can_add_project_member(self):

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/members/",
            {
                "username": "ahmed",
                "role": "MEMBER",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.ADDED,
            object_id=self.project.id,
            )

        self.assertEqual(
            activity.target,
            self.project,
        )

        self.assertEqual(
            activity.metadata["member_id"],
            self.ahmed.id,
        )

        self.assertEqual(
            activity.metadata["username"],
            "ahmed",
        )

        self.assertEqual(
            activity.metadata["role"],
            ProjectMembership.Role.MEMBER,
        )

    def test_manager_can_add_viewer(self):

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/members/",
            {
                "username": "ahmed",
                "role": "VIEWER",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

    def test_member_cannot_add_project_member(self):

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/members/",
            {
                "username": "sara",
                "role": "MEMBER",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )


    def test_manager_can_change_project_member_role(self):

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.force_authenticate(
            user=self.ali
        )

        membership = ProjectMembership.objects.get(
            user=self.ahmed,
            project=self.project,
        )

        response = self.client.patch(
            f"/api/projects/{self.project.id}/members/{membership.id}/role/",
            {
                "role": "VIEWER",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.role,
            ProjectMembership.Role.VIEWER,
        )

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.ROLE_CHANGED,
            object_id=self.project.id,
        )

        notification = Notification.objects.get(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=Notification.NotificationType.ROLE_CHANGED,
            object_id=self.project.id,
        )

        self.assertEqual(notification.metadata["old_role"], "MEMBER")
        self.assertEqual(notification.metadata["new_role"], "VIEWER")
        self.assertIsNone(notification.read_at)

        self.assertEqual(
            activity.target,
            self.project,
        )

        self.assertEqual(
            activity.metadata["member_id"],
            self.ahmed.id,
        )

        self.assertEqual(
            activity.metadata["username"],
            "ahmed",
        )

        self.assertEqual(
            activity.metadata["old_role"],
            ProjectMembership.Role.MEMBER,
        )

        self.assertEqual(
            activity.metadata["new_role"],
            ProjectMembership.Role.VIEWER,
        )

    def test_team_admin_cannot_change_own_project_role(self):
        TeamMembership.objects.update_or_create(
            user=self.ali,
            team=self.project.team,
            defaults={
                "role": TeamMembership.Role.ADMIN,
            },
        )

        membership, _ = ProjectMembership.objects.update_or_create(
            user=self.ali,
            project=self.project,
            defaults={
                "role": ProjectMembership.Role.VIEWER,
            },
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.patch(
            f"/api/projects/{self.project.id}/members/{membership.id}/role/",
            {"role": "MEMBER"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        membership.refresh_from_db()

        self.assertEqual(
            membership.role,
            ProjectMembership.Role.VIEWER,
        )

    def test_member_cannot_change_project_member_role(self):

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        sara_membership = ProjectMembership.objects.create(
            user=self.sara,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.patch(
            f"/api/projects/{self.project.id}/members/{sara_membership.id}/role/",
            {
                "role": "VIEWER",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_can_remove_project_member(self):

        membership = ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.delete(
            f"/api/projects/{self.project.id}/members/{membership.id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            ProjectMembership.objects.filter(
                id=membership.id
            ).exists()
        )

        notification = Notification.objects.get(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=Notification.NotificationType.MEMBER_REMOVED,
            object_id=self.project.id,
        )

        self.assertEqual(
            notification.metadata["member_id"],
            self.ahmed.id,
        )

        self.assertEqual(
            notification.metadata["username"],
            "ahmed",
        )

        self.assertEqual(
            notification.metadata["role"],
            ProjectMembership.Role.MEMBER,
        )

        self.assertIsNone(notification.read_at)

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.REMOVED,
            object_id=self.project.id,
        )

        self.assertEqual(
            activity.target,
            self.project,
        )

        self.assertEqual(
            activity.metadata["member_id"],
            self.ahmed.id,
        )

        self.assertEqual(
            activity.metadata["username"],
            "ahmed",
        )

        self.assertEqual(
            activity.metadata["role"],
            ProjectMembership.Role.MEMBER,
        )

    def test_project_manager_cannot_be_removed(self):

        manager_membership = ProjectMembership.objects.get(
            user=self.ali,
            project=self.project,
        )

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.delete(
            f"/api/projects/{self.project.id}/members/{manager_membership.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )


class AITaskPlannerTests(SimpleTestCase):

    def test_returns_five_task_suggestions(self):
        tasks = generate_task_suggestions(
            description="Build a Django REST API"
        )

        self.assertEqual(len(tasks), 5)

    def test_each_task_has_required_fields(self):
        tasks = generate_task_suggestions(
            description="Build a Django REST API"
        )

        for task in tasks:
            with self.subTest(task=task["title"]):
                self.assertIn("title", task)
                self.assertIn("description", task)
                self.assertIn("priority", task)

    def test_description_is_included_in_first_task(self):
        description = "Build a Django REST API"

        tasks = generate_task_suggestions(
            description=description
        )

        self.assertIn(description, tasks[0]["description"])

    def test_empty_description_raises_value_error(self):
        with self.assertRaises(ValueError):
            generate_task_suggestions(description="   ")



class AITaskPlannerAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="planner_user",
            password="password123",
        )

        self.member = User.objects.create_user(
            username="planner_member",
            password="password123",
        )

        self.outsider = User.objects.create_user(
            username="outsider",
            password="password123",
        )

        self.team = Team.objects.create(
            name="Planner Team",
        )

        TeamMembership.objects.create(
            user=self.member,
            team=self.team,
            role=TeamMembership.Role.MEMBER,
        )

        TeamMembership.objects.create(
            user=self.user,
            team=self.team,
            role=TeamMembership.Role.OWNER,
        )

        self.project = Project.objects.create(
            team=self.team,
            name="Planner Project",
            description="Build a Django REST API",
            created_by=self.user,
        )

        ProjectMembership.objects.create(
            user=self.user,
            project=self.project,
            role=ProjectMembership.Role.MANAGER,
        )

        ProjectMembership.objects.create(
            user=self.member,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_manager_can_generate_task_suggestions(self):
        response = self.client.post(
            f"/api/projects/{self.project.id}/ai-task-planner/",
            {
                "description": "Build a Django REST API",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["project_id"],
            self.project.id,
        )

        self.assertEqual(
            len(response.data["suggestions"]),
            5,
        )

    def test_empty_description_returns_400(self):
        response = self.client.post(
            f"/api/projects/{self.project.id}/ai-task-planner/",
            {
                "description": "   ",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    
    def test_non_team_member_cannot_access_task_planner(self):
        self.client.force_authenticate(
            user=self.outsider
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/ai-task-planner/",
            {
                "description": "Build a Django REST API",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)


        
    def test_project_member_can_generate_task_suggestions(self):
        self.client.force_authenticate(
            user=self.member
        )

        response = self.client.post(
            f"/api/projects/{self.project.id}/ai-task-planner/",
            {
                "description": "Build a Django REST API",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["suggestions"]), 5)
