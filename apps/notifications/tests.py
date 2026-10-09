from django.test import TestCase

from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import (
    create_notification,
    mark_notification_as_read,
    mark_all_notifications_as_read,
)
from apps.projects.models import Project
from apps.teams.models import Team



class NotificationServiceTests(TestCase):

    def setUp(self):
        self.ali = User.objects.create_user(
            username="ali",
            password="password123",
        )

        self.ahmed = User.objects.create_user(
            username="ahmed",
            password="password123",
        )

        self.team = Team.objects.create(
            name="Backend Team",
        )

        self.project = Project.objects.create(
            team=self.team,
            name="TeamFlow API",
            description="Backend project",
            created_by=self.ali,
        )

    def test_create_notification(self):

        notification = create_notification(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType
                .JOIN_REQUEST_APPROVED
            ),
            target=self.project,
        )

        self.assertIsNotNone(
            notification.pk
        )

        self.assertEqual(
            notification.recipient,
            self.ahmed,
        )

        self.assertEqual(
            notification.actor,
            self.ali,
        )

        self.assertEqual(
            notification.notification_type,
            Notification.NotificationType.JOIN_REQUEST_APPROVED,
        )

        self.assertEqual(
            notification.target,
            self.project,
        )

        self.assertEqual(
            notification.object_id,
            self.project.id,
        )

        self.assertIsNone(
            notification.read_at,
        )

    def test_user_can_mark_notification_as_read(self):

        notification = create_notification(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType
                .JOIN_REQUEST_APPROVED
            ),
            target=self.project,
        )

        self.assertIsNone(
            notification.read_at,
        )

        mark_notification_as_read(
            notification=notification,
            user=self.ahmed,
        )

        notification.refresh_from_db()

        self.assertIsNotNone(
            notification.read_at,
        )

    def test_user_cannot_mark_another_users_notification_as_read(self):

        notification = create_notification(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType
                .JOIN_REQUEST_APPROVED
            ),
            target=self.project,
        )

        with self.assertRaises(PermissionError):
            mark_notification_as_read(
                notification=notification,
                user=self.ali,
            )

class NotificationAPITests(TestCase):

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

        self.team = Team.objects.create(
            name="Backend Team",
        )

        self.project = Project.objects.create(
            team=self.team,
            name="TeamFlow API",
            description="Backend project",
            created_by=self.ali,
        )

        self.notification = create_notification(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType
                .JOIN_REQUEST_APPROVED
            ),
            target=self.project,
        )

    def test_user_can_list_own_notifications(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "results",
            response.data,
        )

        notification_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.notification.id,
            notification_ids,
        )

    def test_user_cannot_see_another_users_notifications(self):

        ali_notification = create_notification(
            recipient=self.ali,
            actor=self.ahmed,
            notification_type=(
                Notification.NotificationType.TASK_COMPLETED
            ),
            target=self.project,
        )

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.get(
            "/api/notifications/"
        )

        notification_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertNotIn(
            ali_notification.id,
            notification_ids,
        )

    def test_user_can_filter_unread_notifications(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.get(
            "/api/notifications/?unread=true"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        notification_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.notification.id,
            notification_ids,
        )

    def test_user_can_mark_notification_as_read(self):

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.post(
            f"/api/notifications/{self.notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.notification.refresh_from_db()

        self.assertIsNotNone(
            self.notification.read_at,
        )

    def test_user_cannot_mark_another_users_notification_as_read(self):

        ali_notification = create_notification(
            recipient=self.ali,
            actor=self.ahmed,
            notification_type=(
                Notification.NotificationType.TASK_COMPLETED
            ),
            target=self.project,
        )

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.post(
            f"/api/notifications/{ali_notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_can_mark_all_notifications_as_read(self):

        second_notification = create_notification(
            recipient=self.ahmed,
            actor=self.ali,
            notification_type=(
                Notification.NotificationType.TASK_COMPLETED
            ),
            target=self.project,
        )

        ali_notification = create_notification(
            recipient=self.ali,
            actor=self.ahmed,
            notification_type=(
                Notification.NotificationType.TASK_COMPLETED
            ),
            target=self.project,
        )

        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.post(
            "/api/notifications/read-all/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.notification.refresh_from_db()
        second_notification.refresh_from_db()

        ali_notification.refresh_from_db()

        self.assertIsNone(
            ali_notification.read_at,
        )

        self.assertIsNotNone(
            self.notification.read_at,
        )

        self.assertIsNotNone(
            second_notification.read_at,
        )
