"""API for the plugin app."""

from typing import Optional

from django.core.exceptions import ValidationError
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

import plugin.serializers as PluginSerializers
from common.api import GlobalSettingsPermissions
from InvenTree.api import MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (
    CreateAPI,
    ListAPI,
    RetrieveAPI,
    RetrieveDestroyAPI,
    RetrieveUpdateAPI,
    UpdateAPI,
)
from InvenTree.permissions import IsSuperuser, IsSuperuserOrReadOnly
from plugin import registry
from plugin.base.action.api import ActionPluginView
from plugin.base.barcodes.api import barcode_api_urls
from plugin.base.locate.api import LocatePluginView
from plugin.base.ui.api import ui_plugins_api_urls
from plugin.models import PluginConfig, PluginSetting
from plugin.plugin import InvenTreePlugin

plugin_api_urls = [
    path('action/', ActionPluginView.as_view(), name='api-action-plugin'),
    path('barcode/', include(barcode_api_urls)),
    path('locate/', LocatePluginView.as_view(), name='api-locate-plugin'),
    path(
        'plugins/',
        include([
            # UI plugins
            path('ui/', include(ui_plugins_api_urls)),
            # Plugin management
            path('reload/', PluginReload.as_view(), name='api-plugin-reload'),
            path('install/', PluginInstall.as_view(), name='api-plugin-install'),
            # Registry status
            path(
                'status/',
                RegistryStatusView.as_view(),
                name='api-plugin-registry-status',
            ),
            path(
                'settings/',
                include([
                    path(
                        '', PluginSettingList.as_view(), name='api-plugin-setting-list'
                    )
                ]),
            ),
            # Lookup for individual plugins (based on 'plugin', not 'pk')
            path(
                '<str:plugin>/',
                include([
                    path(
                        'settings/',
                        include([
                            re_path(
                                r'^(?P<key>\w+)/',
                                PluginSettingDetail.as_view(),
                                name='api-plugin-setting-detail',
                            ),
                            path(
                                '',
                                PluginAllSettingList.as_view(),
                                name='api-plugin-settings',
                            ),
                        ]),
                    ),
                    path(
                        'metadata/',
                        PluginMetadataView.as_view(),
                        {'model': PluginConfig, 'lookup_field': 'key'},
                        name='api-plugin-metadata',
                    ),
                    path(
                        'activate/',
                        PluginActivate.as_view(),
                        name='api-plugin-detail-activate',
                    ),
                    path(
                        'uninstall/',
                        PluginUninstall.as_view(),
                        name='api-plugin-uninstall',
                    ),
                    path(
                        'admin/', PluginAdminDetail.as_view(), name='api-plugin-admin'
                    ),
                    path('', PluginDetail.as_view(), name='api-plugin-detail'),
                ]),
            ),
            path('', PluginList.as_view(), name='api-plugin-list'),
        ]),
    ),
]
