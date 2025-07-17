"""Provides a JSON API for common components."""

import json
from typing import Type

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http.response import HttpResponse
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt

import django_q.models
from django_filters import rest_framework as rest_filters
from django_q.tasks import async_task
from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from drf_spectacular.utils import OpenApiResponse, extend_schema
from error_report.models import Error
from pint._typing import UnitLike
from rest_framework import permissions, serializers
from rest_framework.exceptions import NotAcceptable, NotFound, PermissionDenied
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

import common.models
import common.serializers
import InvenTree.conversion
from common.icons import get_icon_packs
from common.settings import get_global_setting
from generic.states.api import urlpattern as generic_states_api_urls
from importer.mixins import DataExportViewMixin
from InvenTree.api import BulkDeleteMixin, MetadataView
from InvenTree.config import CONFIG_LOOKUPS
from InvenTree.filters import ORDER_FILTER, SEARCH_ORDER_FILTER
from InvenTree.helpers import inheritors
from InvenTree.mixins import (
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
)
from InvenTree.permissions import IsStaffOrReadOnly, IsSuperuser
from plugin.models import NotificationUserSetting
from plugin.serializers import NotificationUserSettingSerializer


selection_urls = [
    path(
        '<int:pk>/',
        include([
            # Entries
            path(
                'entry/',
                include([
                    path(
                        '<int:entrypk>/',
                        include([
                            path(
                                '',
                                SelectionEntryDetail.as_view(),
                                name='api-selectionlistentry-detail',
                            )
                        ]),
                    ),
                    path(
                        '',
                        SelectionEntryList.as_view(),
                        name='api-selectionlistentry-list',
                    ),
                ]),
            ),
            path('', SelectionListDetail.as_view(), name='api-selectionlist-detail'),
        ]),
    ),
    path('', SelectionListList.as_view(), name='api-selectionlist-list'),
]

# API URL patterns
settings_api_urls = [
    # User settings
    path(
        'user/',
        include([
            # User Settings Detail
            re_path(
                r'^(?P<key>\w+)/',
                UserSettingsDetail.as_view(),
                name='api-user-setting-detail',
            ),
            # User Settings List
            path('', UserSettingsList.as_view(), name='api-user-setting-list'),
        ]),
    ),
    # Notification settings
    path(
        'notification/',
        include([
            # Notification Settings Detail
            path(
                '<int:pk>/',
                NotificationUserSettingsDetail.as_view(),
                name='api-notification-setting-detail',
            ),
            # Notification Settings List
            path(
                '',
                NotificationUserSettingsList.as_view(),
                name='api-notification-setting-list',
            ),
        ]),
    ),
    # Global settings
    path(
        'global/',
        include([
            # Global Settings Detail
            re_path(
                r'^(?P<key>\w+)/',
                GlobalSettingsDetail.as_view(),
                name='api-global-setting-detail',
            ),
            # Global Settings List
            path('', GlobalSettingsList.as_view(), name='api-global-setting-list'),
        ]),
    ),
]

common_api_urls = [
    # Webhooks
    path('webhook/<slug:endpoint>/', WebhookView.as_view(), name='api-webhook'),
    # Uploaded images for notes
    path('notes-image-upload/', NotesImageList.as_view(), name='api-notes-image-list'),
    # Background task information
    path(
        'background-task/',
        include([
            path('pending/', PendingTaskList.as_view(), name='api-pending-task-list'),
            path(
                'scheduled/',
                ScheduledTaskList.as_view(),
                name='api-scheduled-task-list',
            ),
            path('failed/', FailedTaskList.as_view(), name='api-failed-task-list'),
            path('', BackgroundTaskOverview.as_view(), name='api-task-overview'),
        ]),
    ),
    # Attachments
    path(
        'attachment/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': common.models.Attachment},
                        name='api-attachment-metadata',
                    ),
                    path('', AttachmentDetail.as_view(), name='api-attachment-detail'),
                ]),
            ),
            path('', AttachmentList.as_view(), name='api-attachment-list'),
        ]),
    ),
    path(
        'error-report/',
        include([
            path('<int:pk>/', ErrorMessageDetail.as_view(), name='api-error-detail'),
            path('', ErrorMessageList.as_view(), name='api-error-list'),
        ]),
    ),
    # Project codes
    path(
        'project-code/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': common.models.ProjectCode},
                        name='api-project-code-metadata',
                    ),
                    path(
                        '', ProjectCodeDetail.as_view(), name='api-project-code-detail'
                    ),
                ]),
            ),
            path('', ProjectCodeList.as_view(), name='api-project-code-list'),
        ]),
    ),
    # Custom physical units
    path(
        'units/',
        include([
            path(
                '<int:pk>/',
                include([
                    path('', CustomUnitDetail.as_view(), name='api-custom-unit-detail')
                ]),
            ),
            path('all/', AllUnitList.as_view(), name='api-all-unit-list'),
            path('', CustomUnitList.as_view(), name='api-custom-unit-list'),
        ]),
    ),
    # Currencies
    path(
        'currency/',
        include([
            path(
                'exchange/',
                CurrencyExchangeView.as_view(),
                name='api-currency-exchange',
            ),
            path(
                'refresh/', CurrencyRefreshView.as_view(), name='api-currency-refresh'
            ),
        ]),
    ),
    # Notifications
    path(
        'notifications/',
        include([
            # Individual purchase order detail URLs
            path(
                '<int:pk>/',
                include([
                    path(
                        '',
                        NotificationDetail.as_view(),
                        name='api-notifications-detail',
                    )
                ]),
            ),
            # Read all
            path(
                'readall/',
                NotificationReadAll.as_view(),
                name='api-notifications-readall',
            ),
            # Notification messages list
            path('', NotificationList.as_view(), name='api-notifications-list'),
        ]),
    ),
    # News
    path(
        'news/',
        include([
            path(
                '<int:pk>/',
                include([
                    path('', NewsFeedEntryDetail.as_view(), name='api-news-detail')
                ]),
            ),
            path('', NewsFeedEntryList.as_view(), name='api-news-list'),
        ]),
    ),
    # Flags
    path(
        'flags/',
        include([
            path('<str:key>/', FlagDetail.as_view(), name='api-flag-detail'),
            path('', FlagList.as_view(), name='api-flag-list'),
        ]),
    ),
    # Status
    path('generic/status/', include(generic_states_api_urls)),
    # Contenttype
    path(
        'contenttype/',
        include([
            path(
                '<int:pk>/', ContentTypeDetail.as_view(), name='api-contenttype-detail'
            ),
            path(
                'model/<str:model>/',
                ContentTypeModelDetail.as_view(),
                name='api-contenttype-detail-modelname',
            ),
            path('', ContentTypeList.as_view(), name='api-contenttype-list'),
        ]),
    ),
    # Icons
    path('icons/', IconList.as_view(), name='api-icon-list'),
    # Selection lists
    path('selection/', include(selection_urls)),
]

admin_api_urls = [
    # Admin
    path('config/', ConfigList.as_view(), name='api-config-list'),
    path('config/<str:key>/', ConfigDetail.as_view(), name='api-config-detail'),
]
