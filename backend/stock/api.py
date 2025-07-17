"""JSON API for the Stock app."""

from collections import OrderedDict
from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

import common.models
import common.settings
import InvenTree.helpers
import stock.serializers as StockSerializers
from build.models import Build
from build.serializers import BuildSerializer
from company.models import Company, SupplierPart
from company.serializers import CompanySerializer
from generic.states.api import StatusView
from importer.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import (
    ORDER_FILTER_ALIAS,
    SEARCH_ORDER_FILTER,
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
)
from InvenTree.helpers import (
    extract_serial_numbers,
    generateTestKey,
    is_ajax,
    isNull,
    str2bool,
)
from InvenTree.mixins import (
    CreateAPI,
    CustomRetrieveUpdateDestroyAPI,
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateDestroyAPI,
)
from order.models import PurchaseOrder, ReturnOrder, SalesOrder
from order.serializers import (
    PurchaseOrderSerializer,
    ReturnOrderSerializer,
    SalesOrderSerializer,
)
from part.models import BomItem, Part, PartCategory
from part.serializers import PartBriefSerializer
from stock.generators import generate_batch_code, generate_serial_number
from stock.models import (
    StockItem,
    StockItemTestResult,
    StockItemTracking,
    StockLocation,
    StockLocationType,
)
from stock.status_codes import StockHistoryCode, StockStatus

stock_api_urls = [
    path(
        'location/',
        include([
            path('tree/', StockLocationTree.as_view(), name='api-location-tree'),
            # Stock location detail endpoints
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': StockLocation},
                        name='api-location-metadata',
                    ),
                    path('', LocationDetail.as_view(), name='api-location-detail'),
                ]),
            ),
            path('', StockLocationList.as_view(), name='api-location-list'),
        ]),
    ),
    # Stock location type endpoints
    path(
        'location-type/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': StockLocationType},
                        name='api-location-type-metadata',
                    ),
                    path(
                        '',
                        StockLocationTypeDetail.as_view(),
                        name='api-location-type-detail',
                    ),
                ]),
            ),
            path('', StockLocationTypeList.as_view(), name='api-location-type-list'),
        ]),
    ),
    # Endpoints for bulk stock adjustment actions
    path('count/', StockCount.as_view(), name='api-stock-count'),
    path('add/', StockAdd.as_view(), name='api-stock-add'),
    path('remove/', StockRemove.as_view(), name='api-stock-remove'),
    path('transfer/', StockTransfer.as_view(), name='api-stock-transfer'),
    path('assign/', StockAssign.as_view(), name='api-stock-assign'),
    path('merge/', StockMerge.as_view(), name='api-stock-merge'),
    path('change_status/', StockChangeStatus.as_view(), name='api-stock-change-status'),
    # StockItemTestResult API endpoints
    path(
        'test/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': StockItemTestResult},
                        name='api-stock-test-result-metadata',
                    ),
                    path(
                        '',
                        StockItemTestResultDetail.as_view(),
                        name='api-stock-test-result-detail',
                    ),
                ]),
            ),
            path(
                '', StockItemTestResultList.as_view(), name='api-stock-test-result-list'
            ),
        ]),
    ),
    # StockItemTracking API endpoints
    path(
        'track/',
        include([
            path(
                '<int:pk>/',
                StockTrackingDetail.as_view(),
                name='api-stock-tracking-detail',
            ),
            # Stock tracking status code information
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: StockHistoryCode},
                name='api-stock-tracking-status-codes',
            ),
            path('', StockTrackingList.as_view(), name='api-stock-tracking-list'),
        ]),
    ),
    # Detail views for a single stock item
    path(
        '<int:pk>/',
        include([
            path('convert/', StockItemConvert.as_view(), name='api-stock-item-convert'),
            path('install/', StockItemInstall.as_view(), name='api-stock-item-install'),
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': StockItem},
                name='api-stock-item-metadata',
            ),
            path('return/', StockItemReturn.as_view(), name='api-stock-item-return'),
            path(
                'serialize/',
                StockItemSerialize.as_view(),
                name='api-stock-item-serialize',
            ),
            path(
                'uninstall/',
                StockItemUninstall.as_view(),
                name='api-stock-item-uninstall',
            ),
            path('', StockDetail.as_view(), name='api-stock-detail'),
        ]),
    ),
    # Stock item status code information
    path(
        'status/',
        StatusView.as_view(),
        {StatusView.MODEL_REF: StockStatus},
        name='api-stock-status-codes',
    ),
    # Anything else
    path('', StockList.as_view(), name='api-stock-list'),
]
