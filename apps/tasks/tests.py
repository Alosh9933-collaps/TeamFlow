from django.test import TestCase

from rest_framework.test import APIClient

from apps.activity.models import ActivityLog

from apps.notifications.models import Notification

from apps.accounts.models import User
from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Tag, Task, TaskClaim
from apps.tasks.services import (
    claim_task,
    complete_task,
    unclaim_task,
)
from apps.teams.models import Team, TeamMembership


class ClaimTaskTests(TestCase):
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

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project,
            role=ProjectMembership.Role.MEMBER,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Implement authentication",
            description="Build authentication system",
            priority=Task.Priority.HIGH,
            created_by=self.ali,
        )

    def test_project_member_can_claim_task(self):
        claim = claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        self.assertEqual(
            claim.user,
            self.ali,
        )

        self.assertEqual(
            claim.task,
            self.task,
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_non_project_member_cannot_claim_task(self):
        outsider = User.objects.create_user(
            username="outsider",
            password="password123",
        )

        with self.assertRaises(PermissionError):
            claim_task(
                task_id=self.task.id,
                user=outsider,
            )

    def test_user_cannot_claim_same_task_twice(self):
        claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        with self.assertRaises(ValueError):
            claim_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_multiple_project_members_can_claim_same_task(self):
        ali_claim = claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        ahmed_claim = claim_task(
            task_id=self.task.id,
            user=self.ahmed,
        )

        self.assertEqual(
            ali_claim.user,
            self.ali,
        )

        self.assertEqual(
            ahmed_claim.user,
            self.ahmed,
        )

        self.assertEqual(
            TaskClaim.objects.filter(task=self.task).count(),
            2,
        )

    def test_done_task_cannot_be_claimed(self):
        self.task.status = Task.Status.DONE
        self.task.save(update_fields=["status"])

        with self.assertRaises(ValueError):
            claim_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_user_can_unclaim_task(self):
        claim = claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        unclaim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        claim.refresh_from_db()
        self.task.refresh_from_db()

        self.assertIsNotNone(
            claim.released_at,
        )

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_user_cannot_unclaim_without_active_claim(self):
        with self.assertRaises(ValueError):
            unclaim_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_done_task_cannot_be_unclaimed(self):
        claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        self.task.status = Task.Status.DONE
        self.task.save(update_fields=["status"])

        with self.assertRaises(ValueError):
            unclaim_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_user_can_complete_claimed_task(self):
        claim = claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        complete_task(
            task_id=self.task.id,
            user=self.ali,
        )

        claim.refresh_from_db()
        self.task.refresh_from_db()

        self.assertIsNotNone(
            claim.completed_at,
        )

        self.assertEqual(
            self.task.status,
            Task.Status.DONE,
        )

        activity = ActivityLog.objects.get(
            actor=self.ali,
            action=ActivityLog.Action.COMPLETED,
            object_id=self.task.id,
        )

        self.assertEqual(
            activity.target,
            self.task,
        )

        self.assertEqual(
            activity.metadata["task_id"],
            self.task.id,
        )

        notification = Notification.objects.get(
            recipient=self.ali,
            actor=self.ali,
            notification_type=Notification.NotificationType.TASK_COMPLETED,
            object_id=self.task.id,
        )

        self.assertEqual(notification.metadata["task_id"], self.task.id)
        self.assertEqual(notification.metadata["task_title"], self.task.title)
        self.assertIsNone(notification.read_at)

    def test_user_without_claim_cannot_complete_task(self):
        with self.assertRaises(PermissionError):
            complete_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_other_claimant_cannot_complete_after_task_is_done(self):
        claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        claim_task(
            task_id=self.task.id,
            user=self.ahmed,
        )

        complete_task(
            task_id=self.task.id,
            user=self.ali,
        )

        with self.assertRaises(ValueError):
            complete_task(
                task_id=self.task.id,
                user=self.ahmed,
            )

    def test_released_claim_cannot_complete_task(self):
        claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        unclaim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        with self.assertRaises(PermissionError):
            complete_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_completed_task_cannot_be_completed_again(self):
        claim_task(
            task_id=self.task.id,
            user=self.ali,
        )

        complete_task(
            task_id=self.task.id,
            user=self.ali,
        )

        with self.assertRaises(ValueError):
            complete_task(
                task_id=self.task.id,
                user=self.ali,
            )

    def test_project_member_can_claim_task_through_api(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["user"],
            self.ali.id,
        )

        self.assertEqual(
            response.data["task"],
            self.task.id,
        )

        self.assertIsNone(
            response.data["completed_at"],
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_non_project_member_cannot_claim_task_through_api(self):
        outsider = User.objects.create_user(
            username="outsider",
            password="password123",
        )

        self.client.force_authenticate(user=outsider)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_user_cannot_claim_same_task_twice_through_api(self):
        self.client.force_authenticate(user=self.ali)

        first_response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

    def test_user_can_unclaim_task_through_api(self):
        self.client.force_authenticate(user=self.ali)

        claim_response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            claim_response.status_code,
            201,
        )

        unclaim_response = self.client.post(
            f"/api/tasks/{self.task.id}/unclaim/"
        )

        self.assertEqual(
            unclaim_response.status_code,
            200,
        )

        self.assertIsNotNone(
            unclaim_response.data["released_at"],
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.TODO,
        )

    def test_unclaim_does_not_reset_task_when_another_claim_is_active(self):
        self.client.force_authenticate(user=self.ali)

        self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.client.force_authenticate(user=self.ahmed)

        self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/unclaim/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_user_cannot_unclaim_without_active_claim_through_api(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/unclaim/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_user_can_complete_task_through_api(self):
        self.client.force_authenticate(user=self.ali)

        claim_response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            claim_response.status_code,
            201,
        )

        complete_response = self.client.post(
            f"/api/tasks/{self.task.id}/complete/"
        )

        self.assertEqual(
            complete_response.status_code,
            200,
        )

        self.assertIsNotNone(
            complete_response.data["completed_at"],
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.DONE,
        )

    def test_user_without_claim_cannot_complete_task_through_api(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/complete/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_only_first_claimant_can_complete_task_through_api(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.client.force_authenticate(user=self.ahmed)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/complete/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.client.force_authenticate(user=self.ahmed)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/complete/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.DONE,
        )

    def test_user_who_unclaimed_cannot_complete_task_through_api(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.post(
            f"/api/tasks/{self.task.id}/claim/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        response = self.client.post(
            f"/api/tasks/{self.task.id}/unclaim/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response = self.client.post(
            f"/api/tasks/{self.task.id}/complete/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )


class TaskViewSetTests(TestCase):
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

        self.viewer = User.objects.create_user(
            username="viewer",
            password="password123",
        )

        self.team_a = Team.objects.create(
            name="Team A",
        )

        self.team_b = Team.objects.create(
            name="Team B",
        )

        TeamMembership.objects.create(
            user=self.ali,
            team=self.team_a,
            role=TeamMembership.Role.OWNER,
        )

        TeamMembership.objects.create(
            user=self.ahmed,
            team=self.team_a,
            role=TeamMembership.Role.MEMBER,
        )

        TeamMembership.objects.create(
            user=self.sara,
            team=self.team_b,
            role=TeamMembership.Role.MEMBER,
        )

        self.project_a = Project.objects.create(
            team=self.team_a,
            name="Project A",
            description="Project A",
            created_by=self.ali,
        )

        self.project_b = Project.objects.create(
            team=self.team_b,
            name="Project B",
            description="Project B",
            created_by=self.sara,
        )

        ProjectMembership.objects.create(
            user=self.ali,
            project=self.project_a,
            role=ProjectMembership.Role.MANAGER,
        )

        ProjectMembership.objects.create(
            user=self.ahmed,
            project=self.project_a,
            role=ProjectMembership.Role.MEMBER,
        )

        ProjectMembership.objects.create(
            user=self.viewer,
            project=self.project_a,
            role=ProjectMembership.Role.VIEWER,
        )

        ProjectMembership.objects.create(
            user=self.sara,
            project=self.project_b,
            role=ProjectMembership.Role.MEMBER,
        )

        self.task_a = Task.objects.create(
            project=self.project_a,
            title="Task A",
            description="Task A description",
            created_by=self.ali,
        )

        self.task_b = Task.objects.create(
            project=self.project_b,
            title="Task B",
            description="Task B description",
            created_by=self.sara,
        )

    def test_member_can_see_tasks_from_their_project(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.get("/api/tasks/")

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.task_a.id,
            task_ids,
        )

    def test_member_cannot_see_tasks_from_another_project(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.get("/api/tasks/")

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertNotIn(
            self.task_b.id,
            task_ids,
        )

    def test_member_cannot_access_task_from_another_project(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            f"/api/tasks/{self.task_b.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_project_member_can_create_task(self):
        self.client.force_authenticate(user=self.ahmed)

        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project_a.id,
                "title": "New Task",
                "description": "New Task description",
                "priority": Task.Priority.HIGH,
                "due_date": None,
                "tags": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["created_by"],
            self.ahmed.id,
        )

    def test_project_member_cannot_create_task_in_another_project(self):
        self.client.force_authenticate(user=self.sara)

        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project_a.id,
                "title": "Unauthorized Task",
                "description": "Should fail",
                "priority": Task.Priority.MEDIUM,
                "due_date": None,
                "tags": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )


    def test_non_project_member_cannot_create_task(self):

        outsider = User.objects.create_user(
            username="outsider",
            password="password123",
        )

        self.client.force_authenticate(
            user=outsider
        )

        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project_a.id,
                "title": "Unauthorized Task",
                "description": "Should fail",
                "priority": Task.Priority.MEDIUM,
                "due_date": None,
                "tags": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            Task.objects.filter(
                title="Unauthorized Task"
            ).exists()
        )

    def test_delete_task_is_soft_delete(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.delete(
            f"/api/tasks/{self.task_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.task_a.refresh_from_db()

        self.assertTrue(
            self.task_a.is_deleted,
        )

        self.assertIsNotNone(
            self.task_a.deleted_at,
        )

    def test_soft_deleted_task_is_not_visible(self):
        self.task_a.is_deleted = True
        self.task_a.save(
            update_fields=["is_deleted"]
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            f"/api/tasks/{self.task_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_tasks_can_be_filtered_by_status(self):
        task_c = Task.objects.create(
            project=self.project_a,
            title="Pending Task",
            description="Pending Task description",
            status=Task.Status.PENDING,
            priority=Task.Priority.LOW,
            created_by=self.ali,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?status=PENDING"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            task_c.id,
            task_ids,
        )

        self.assertNotIn(
            self.task_a.id,
            task_ids,
        )

    def test_tasks_can_be_filtered_by_priority(self):
        task_c = Task.objects.create(
            project=self.project_a,
            title="Urgent Task",
            description="Urgent Task description",
            priority=Task.Priority.URGENT,
            created_by=self.ali,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?priority=URGENT"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            task_c.id,
            task_ids,
        )

        self.assertNotIn(
            self.task_a.id,
            task_ids,
        )

    def test_tasks_can_be_filtered_by_project(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            f"/api/tasks/?project={self.project_a.id}"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.task_a.id,
            task_ids,
        )

        self.assertNotIn(
            self.task_b.id,
            task_ids,
        )

    def test_tasks_can_be_searched_by_title(self):
        task = Task.objects.create(
            project=self.project_a,
            title="Fix authentication bug",
            description="Security issue",
            priority=Task.Priority.HIGH,
            created_by=self.ali,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?search=authentication"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            task.id,
            task_ids,
        )

    def test_tasks_can_be_searched_by_description(self):
        task = Task.objects.create(
            project=self.project_a,
            title="Backend Task",
            description="Implement JWT authentication",
            priority=Task.Priority.MEDIUM,
            created_by=self.ali,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?search=JWT"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            task.id,
            task_ids,
        )

    def test_tasks_can_be_searched_by_tag(self):
        tag = Tag.objects.create(
            team=self.team_a,
            name="Security",
        )

        task = Task.objects.create(
            project=self.project_a,
            title="Review endpoint",
            description="Review API permissions",
            priority=Task.Priority.HIGH,
            created_by=self.ali,
        )

        task.tags.add(tag)

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?search=Security"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            task.id,
            task_ids,
        )

    def test_search_does_not_expose_tasks_from_other_projects(self):
        self.task_b.title = "Secret authentication task"
        self.task_b.save(
            update_fields=["title"]
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?search=authentication"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertNotIn(
            self.task_b.id,
            task_ids,
        )

    def test_tasks_can_be_ordered_by_title(self):
        task_c = Task.objects.create(
            project=self.project_a,
            title="AAA Task",
            description="First",
            priority=Task.Priority.MEDIUM,
            created_by=self.ali,
        )

        task_d = Task.objects.create(
            project=self.project_a,
            title="ZZZ Task",
            description="Second",
            priority=Task.Priority.MEDIUM,
            created_by=self.ali,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?ordering=title"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        returned_titles = [
            item["title"]
            for item in response.data["results"]
        ]

        self.assertLess(
            returned_titles.index(task_c.title),
            returned_titles.index(task_d.title),
        )

    def test_tasks_can_be_ordered_descending_by_title(self):
        task_c = Task.objects.create(
            project=self.project_a,
            title="AAA Task",
            description="First",
            priority=Task.Priority.MEDIUM,
            created_by=self.ali,
        )

        task_d = Task.objects.create(
            project=self.project_a,
            title="ZZZ Task",
            description="Second",
            priority=Task.Priority.MEDIUM,
            created_by=self.ali,
        )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?ordering=-title"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        returned_titles = [
            item["title"]
            for item in response.data["results"]
        ]

        self.assertLess(
            returned_titles.index(task_d.title),
            returned_titles.index(task_c.title),
        )

    def test_tasks_ignore_unsupported_ordering_field(self):
        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?ordering=password"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_tasks_are_paginated(self):
        for index in range(8):
            Task.objects.create(
                project=self.project_a,
                title=f"Pagination Task {index}",
                description="Pagination test",
                priority=Task.Priority.MEDIUM,
                created_by=self.ali,
            )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?page=1"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "count",
            response.data,
        )

        self.assertIn(
            "results",
            response.data,
        )

        self.assertEqual(
            len(response.data["results"]),
            5,
        )

    def test_tasks_can_be_paginated_by_page_number(self):
        for index in range(8):
            Task.objects.create(
                project=self.project_a,
                title=f"Pagination Task {index}",
                description="Pagination test",
                priority=Task.Priority.MEDIUM,
                created_by=self.ali,
            )

        self.client.force_authenticate(user=self.ali)

        response = self.client.get(
            "/api/tasks/?page=2"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertGreater(
            len(response.data["results"]),
            0,
        )

        self.assertIsNotNone(
            response.data["previous"],
        )

    def test_jwt_user_can_access_task_api(self):
        token_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "ali",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(
            token_response.status_code,
            200,
        )

        access_token = token_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/tasks/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        task_ids = [
            item["id"]
            for item in response.data["results"]
        ]

        self.assertIn(
            self.task_a.id,
            task_ids,
        )

    def test_invalid_jwt_cannot_access_task_api(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token"
        )

        response = self.client.get(
            "/api/tasks/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_anonymous_user_cannot_access_task_api(self):
        response = self.client.get(
            "/api/tasks/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_viewer_can_read_task(self):
        self.client.force_authenticate(
            user=self.viewer
        )

        response = self.client.get(
            f"/api/tasks/{self.task_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_viewer_cannot_create_task(self):
        self.client.force_authenticate(
            user=self.viewer
        )

        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project_a.id,
                "title": "Viewer Task",
                "description": "Should fail",
                "priority": Task.Priority.MEDIUM,
                "due_date": None,
                "tags": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_project_member_can_update_task(self):
        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.patch(
            f"/api/tasks/{self.task_a.id}/",
            {
                "title": "Updated by Ahmed",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.task_a.refresh_from_db()

        self.assertEqual(
            self.task_a.title,
            "Updated by Ahmed",
        )

    def test_project_member_cannot_delete_task(self):
        self.client.force_authenticate(
            user=self.ahmed
        )

        response = self.client.delete(
            f"/api/tasks/{self.task_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.task_a.refresh_from_db()

        self.assertFalse(
            self.task_a.is_deleted,
        )

    def test_project_manager_can_delete_task(self):
        self.client.force_authenticate(
            user=self.ali
        )

        response = self.client.delete(
            f"/api/tasks/{self.task_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.task_a.refresh_from_db()

        self.assertTrue(
            self.task_a.is_deleted,
        )

        self.assertIsNotNone(
            self.task_a.deleted_at,
        )

    def test_viewer_cannot_update_task(self):
        self.client.force_authenticate(
            user=self.viewer
        )

        response = self.client.patch(
            f"/api/tasks/{self.task_a.id}/",
            {
                "title": "Unauthorized Update",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )
