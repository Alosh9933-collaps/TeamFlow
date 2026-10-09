from django.test import TestCase

from apps.notifications.models import Notification
from rest_framework.test import APIClient
from apps.activity.models import ActivityLog
from apps.accounts.models import User
from apps.teams.models import (
    Team,
    TeamMembership,
)


class TeamViewSetTests(TestCase):

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

        self.admin = User.objects.create_user(
            username="admin",
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

        TeamMembership.objects.create(
            user=self.admin,
            team=self.team,
            role=TeamMembership.Role.ADMIN,
        )

    def test_authenticated_user_can_create_team(self):
        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            "/api/teams/",
            {
                "name": "New Team",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        team = Team.objects.get(
            name="New Team"
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.ali,
                team=team,
                role=TeamMembership.Role.OWNER,
            ).exists()
        )

        self.assertTrue(
            ActivityLog.objects.filter(
                actor=self.ali,
                action=ActivityLog.Action.CREATED,
                object_id=team.id,
            ).exists()
        )

    def test_user_can_see_his_teams(self):
        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.get(
            "/api/teams/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        team_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.team.id,
            team_ids,
        )

    def test_user_cannot_see_other_teams(self):
        other_team = Team.objects.create(
            name="Secret Team",
        )

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.get(
            "/api/teams/"
        )

        team_ids = [
            item["id"]
            for item in response.data["results"]
        ]


        self.assertNotIn(
            other_team.id,
            team_ids,
        )

    def test_owner_can_update_team(self):
        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.patch(
            f"/api/teams/{self.team.id}/",
            {
                "name": "Updated Team",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.team.refresh_from_db()

        self.assertEqual(
            self.team.name,
            "Updated Team",
        )

    def test_member_cannot_update_team(self):
        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.patch(
            f"/api/teams/{self.team.id}/",
            {
                "name": "Hack Attempt",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_owner_can_delete_team(self):
        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.delete(
            f"/api/teams/{self.team.id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            Team.objects.filter(
                id=self.team.id
            ).exists()
        )

    def test_member_cannot_delete_team(self):
        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.delete(
            f"/api/teams/{self.team.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_owner_can_add_member(self):

        new_user = User.objects.create_user(
            username="mohamed",
            password="password123",
        )

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            f"/api/teams/{self.team.id}/members/",
            {
                "username": "mohamed",
                "role": "MEMBER",
            },
                format="json",
            )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=new_user,
                team=self.team,
                role=TeamMembership.Role.MEMBER,
            ).exists()
        )

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.ADDED,
            object_id=self.team.id,
        )

        self.assertEqual(
            activity.target,
            self.team,
        )

        self.assertEqual(
            activity.metadata["member_id"],
            new_user.id,
        )

        self.assertEqual(
            activity.metadata["username"],
            "mohamed",
        )

        self.assertEqual(
            activity.metadata["role"],
            TeamMembership.Role.MEMBER,
        )

        notification = Notification.objects.get(
            recipient=new_user,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType.MEMBER_ADDED
            ),
            object_id=self.team.id,
        )

        self.assertEqual(
            notification.target,
            self.team,
        )

        self.assertEqual(
            notification.metadata["team_id"],
            self.team.id,
        )

        self.assertEqual(
            notification.metadata["team_name"],
            self.team.name,
        )

        self.assertEqual(
            notification.metadata["role"],
            TeamMembership.Role.MEMBER,
        )

        self.assertIsNone(
            notification.read_at,
        )

    def test_owner_can_add_admin(self):

        new_user = User.objects.create_user(
            username="mohamed",
            password="password123",
        )

        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.post(
            f"/api/teams/{self.team.id}/members/",
            {
                "username": "mohamed",
                "role": "ADMIN",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        membership = TeamMembership.objects.get(
            user=new_user,
            team=self.team,
        )

        self.assertEqual(
            membership.role,
            TeamMembership.Role.ADMIN,
        )

    def test_admin_cannot_add_admin(self):

        new_user = User.objects.create_user(
            username="mohamed",
            password="password123",
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/teams/{self.team.id}/members/",
            {
                "username": "mohamed",
                "role": "ADMIN",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_owner_can_change_member_role(self):

        self.client.force_authenticate(
            user=self.ali
        )

        membership = TeamMembership.objects.get(
            user=self.ahmed,
            team=self.team,
        )

        response = self.client.patch(
            f"/api/teams/{self.team.id}/members/{membership.id}/role/",
            {
                "role": "ADMIN",
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
            TeamMembership.Role.ADMIN,
        )

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.ROLE_CHANGED,
            object_id=self.team.id,
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
            TeamMembership.Role.MEMBER,
        )

        self.assertEqual(
            activity.metadata["new_role"],
            TeamMembership.Role.ADMIN,
        )

        notification = Notification.objects.get(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType.ROLE_CHANGED
            ),
            object_id=self.team.id,
        )

        self.assertEqual(
            notification.target,
            self.team,
        )

        self.assertEqual(
            notification.metadata["team_id"],
            self.team.id,
        )

        self.assertEqual(
            notification.metadata["team_name"],
            self.team.name,
        )

        self.assertEqual(
            notification.metadata["old_role"],
            TeamMembership.Role.MEMBER,
        )

        self.assertEqual(
            notification.metadata["new_role"],
            TeamMembership.Role.ADMIN,
        )

        self.assertIsNone(
            notification.read_at,
        )

    def test_member_cannot_change_role(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        membership = TeamMembership.objects.get(
            user=self.ahmed,
            team=self.team,
        )

        response = self.client.patch(
            f"/api/teams/{self.team.id}/members/{membership.id}/role/",
            {
                "role": "ADMIN",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_owner_can_remove_member(self):

        self.client.force_authenticate(
            user=self.ali
        )

        membership = TeamMembership.objects.get(
            user=self.ahmed,
            team=self.team,
        )

        response = self.client.delete(
            f"/api/teams/{self.team.id}/members/{membership.id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                id=membership.id
            ).exists()
        )

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.REMOVED,
            object_id=self.team.id,
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
            TeamMembership.Role.MEMBER,
        )

    def test_admin_can_not_delete_owner(self):

        self.client.force_authenticate(
            user=self.admin
        )

        membership = TeamMembership.objects.get(
            user=self.ali,
            team=self.team,
        )

        response = self.client.delete(
            f"/api/teams/{self.team.id}/members/{membership.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                id=membership.id
            ).exists()
        )
