from django.urls import path

from apps.activity.views import ProjectActivityListView


urlpatterns = [
    path(
        "projects/<int:project_id>/activity/",
        ProjectActivityListView.as_view(),
        name="project-activity",
    ),
]
