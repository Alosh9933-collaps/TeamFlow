from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
)


urlpatterns = [
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "notifications/read-all/",
        NotificationMarkAllReadView.as_view(),
        name="notification-mark-all-read",
    ),
    path(
        "notifications/<int:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
]
