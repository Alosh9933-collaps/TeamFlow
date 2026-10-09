from django.test import TestCase

from rest_framework.test import APIClient

from apps.accounts.models import User

from apps.activity.models import ActivityLog
from apps.activity.services import log_activity

from apps.projects.models import Project
from apps.projects.models import ProjectMembership

from apps.teams.models import (
    Team,
    TeamMembership,
)

class ActivityLogServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="ali",
            password="password123",
        )

        self.team = Team.objects.create(
            name="Backend Team",
        )

        self.project = Project.objects.create(
            team=self.team,
            name="TeamFlow API",
            description="Backend project",
            created_by=self.user,
        )

    def test_log_activity_creates_activity(self):

        activity = log_activity(
            actor=self.user,
            action=ActivityLog.Action.CREATED,
            target=self.project,
        )

        self.assertIsNotNone(
            activity.pk
        )

        self.assertEqual(
            activity.actor,
            self.user,
        )

        self.assertEqual(
            activity.action,
            ActivityLog.Action.CREATED,
        )

        self.assertEqual(
            activity.target,
            self.project,
        )

        self.assertEqual(
            activity.object_id,
            self.project.id,
        )

class ProjectActivityListTests(TestCase):

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
            description="Backend",
            created_by=self.ali,
        )

        ProjectMembership.objects.create(
            user=self.ali,
            project=self.project,
            role=ProjectMembership.Role.MANAGER,
        )

        log_activity(
            actor=self.ali,
            action=ActivityLog.Action.CREATED,
            target=self.project,
        )

    def test_team_member_can_view_project_activity(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.get(
            f"/api/projects/{self.project.id}/activity/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "results",
            response.data,
        )

    def test_project_activity_contains_created_event(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.get(
            f"/api/projects/{self.project.id}/activity/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        activities = response.data["results"]

        self.assertTrue(
            any(
                activity["action"]
                == ActivityLog.Action.CREATED
                for activity in activities
            )
        )

    def test_outsider_cannot_view_project_activity(self):

        self.client.force_authenticate(
            user=self.outsider
        )

        response = self.client.get(
            f"/api/projects/{self.project.id}/activity/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )
