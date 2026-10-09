from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.projects.views import (
    ProjectJoinRequestApproveView,
    ProjectJoinRequestCreateView,
    ProjectViewSet,
)

router = DefaultRouter()

router.register(
    "projects",
    ProjectViewSet,
    basename="project",
)

urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "projects/<int:project_id>/join-request/",
        ProjectJoinRequestCreateView.as_view(),
        name="project-join-request",
    ),
    path(
        "projects/<int:project_id>/join-request/<int:request_id>/approve/",
        ProjectJoinRequestApproveView.as_view(),
        name="project-join-request-approve",
    ),
]
