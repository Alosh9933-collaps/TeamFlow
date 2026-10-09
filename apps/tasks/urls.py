from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.tasks.views import (
    TaskClaimView,
    TaskCompleteView,
    TaskUnclaimView,
    TaskViewSet,
)

router = DefaultRouter()
router.register(
    "tasks",
    TaskViewSet,
    basename="task",
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "tasks/<int:task_id>/claim/",
        TaskClaimView.as_view(),
        name="task-claim",
    ),
    path(
        "tasks/<int:task_id>/unclaim/",
        TaskUnclaimView.as_view(),
        name="task-unclaim",
    ),
    path(
        "tasks/<int:task_id>/complete/",
        TaskCompleteView.as_view(),
        name="task-complete",
    ),
]
