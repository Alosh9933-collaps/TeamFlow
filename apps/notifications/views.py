from django.shortcuts import get_object_or_404

from rest_framework import status, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
)

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import (
    get_user_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)

class NotificationListView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        responses=NotificationSerializer(many=True),
    )

    def get(self, request):

        unread_only = request.query_params.get(
            "unread"
        ) == "true"

        notifications = get_user_notifications(
            user=request.user,
            unread_only=unread_only,
        )

        paginator = PageNumberPagination()

        page = paginator.paginate_queryset(
            notifications,
            request,
            view=self,
        )

        serializer = NotificationSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

class NotificationMarkReadView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        request=None,
        responses=NotificationSerializer,
    )

    def post(self, request, notification_id):

        notification = get_object_or_404(
            Notification,
            id=notification_id,
        )

        try:
            notification = mark_notification_as_read(
                notification=notification,
                user=request.user,
            )

        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NotificationSerializer(
            notification
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class NotificationMarkAllReadView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="NotificationMarkAllReadResponse",
                fields={
                    "detail": serializers.CharField(),
                    "updated_count": serializers.IntegerField(),
                },
            ),
        },
    )

    def post(self, request):

        updated_count = mark_all_notifications_as_read(
            user=request.user,
        )

        return Response(
            {
                "detail": "All notifications marked as read.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )
