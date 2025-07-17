"""Provides a JSON API for the Part app."""

import functools
import re

from django.db.models import Count, F, Q
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

import order.models
import part.filters
from build.models import Build, BuildItem
from build.status_codes import BuildStatusGroups
from importer.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import (
    ORDER_FILTER,
    ORDER_FILTER_ALIAS,
    SEARCH_ORDER_FILTER,
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
    InvenTreeSearchFilter,
)
from InvenTree.helpers import isNull, str2bool
from InvenTree.mixins import (
    CreateAPI,
    CustomRetrieveUpdateDestroyAPI,
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
    UpdateAPI,
)
from InvenTree.permissions import RolePermission
from InvenTree.serializers import EmptySerializer
from order.status_codes import PurchaseOrderStatusGroups, SalesOrderStatusGroups
from stock.models import StockLocation

from . import serializers as part_serializers
from . import views
from .models import (
    BomItem,
    BomItemSubstitute,
    Part,
    PartCategory,
    PartCategoryParameterTemplate,
    PartInternalPriceBreak,
    PartParameter,
    PartParameterTemplate,
    PartRelated,
    PartSellPriceBreak,
    PartStocktake,
    PartStocktakeReport,
    PartTestTemplate,
)

part_api_urls = [
    # Base URL for PartCategory API endpoints
    path(
        'category/',
        include([
            path('tree/', CategoryTree.as_view(), name='api-part-category-tree'),
            path(
                'parameters/',
                include([
                    path(
                        '<int:pk>/',
                        include([
                            path(
                                'metadata/',
                                MetadataView.as_view(),
                                {'model': PartCategoryParameterTemplate},
                                name='api-part-category-parameter-metadata',
                            ),
                            path(
                                '',
                                CategoryParameterDetail.as_view(),
                                name='api-part-category-parameter-detail',
                            ),
                        ]),
                    ),
                    path(
                        '',
                        CategoryParameterList.as_view(),
                        name='api-part-category-parameter-list',
                    ),
                ]),
            ),
            # Category detail endpoints
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartCategory},
                        name='api-part-category-metadata',
                    ),
                    # PartCategory detail endpoint
                    path('', CategoryDetail.as_view(), name='api-part-category-detail'),
                ]),
            ),
            path('', CategoryList.as_view(), name='api-part-category-list'),
        ]),
    ),
    # Base URL for PartTestTemplate API endpoints
    path(
        'test-template/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartTestTemplate},
                        name='api-part-test-template-metadata',
                    ),
                    path(
                        '',
                        PartTestTemplateDetail.as_view(),
                        name='api-part-test-template-detail',
                    ),
                ]),
            ),
            path(
                '', PartTestTemplateList.as_view(), name='api-part-test-template-list'
            ),
        ]),
    ),
    # Base URL for part sale pricing
    path(
        'sale-price/',
        include([
            path(
                '<int:pk>/',
                PartSalePriceDetail.as_view(),
                name='api-part-sale-price-detail',
            ),
            path('', PartSalePriceList.as_view(), name='api-part-sale-price-list'),
        ]),
    ),
    # Base URL for part internal pricing
    path(
        'internal-price/',
        include([
            path(
                '<int:pk>/',
                PartInternalPriceDetail.as_view(),
                name='api-part-internal-price-detail',
            ),
            path(
                '', PartInternalPriceList.as_view(), name='api-part-internal-price-list'
            ),
        ]),
    ),
    # Base URL for PartRelated API endpoints
    path(
        'related/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartRelated},
                        name='api-part-related-metadata',
                    ),
                    path(
                        '', PartRelatedDetail.as_view(), name='api-part-related-detail'
                    ),
                ]),
            ),
            path('', PartRelatedList.as_view(), name='api-part-related-list'),
        ]),
    ),
    # Base URL for PartParameter API endpoints
    path(
        'parameter/',
        include([
            path(
                'template/',
                include([
                    path(
                        '<int:pk>/',
                        include([
                            path(
                                'metadata/',
                                MetadataView.as_view(),
                                {'model': PartParameterTemplate},
                                name='api-part-parameter-template-metadata',
                            ),
                            path(
                                '',
                                PartParameterTemplateDetail.as_view(),
                                name='api-part-parameter-template-detail',
                            ),
                        ]),
                    ),
                    path(
                        '',
                        PartParameterTemplateList.as_view(),
                        name='api-part-parameter-template-list',
                    ),
                ]),
            ),
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartParameter},
                        name='api-part-parameter-metadata',
                    ),
                    path(
                        '',
                        PartParameterDetail.as_view(),
                        name='api-part-parameter-detail',
                    ),
                ]),
            ),
            path('', PartParameterList.as_view(), name='api-part-parameter-list'),
        ]),
    ),
    # Part stocktake data
    path(
        'stocktake/',
        include([
            path(
                r'report/',
                include([
                    path(
                        'generate/',
                        PartStocktakeReportGenerate.as_view(),
                        name='api-part-stocktake-report-generate',
                    ),
                    path(
                        '<int:pk>/',
                        PartStocktakeReportDetail.as_view(),
                        name='api-part-stocktake-report-detail',
                    ),
                    path(
                        '',
                        PartStocktakeReportList.as_view(),
                        name='api-part-stocktake-report-list',
                    ),
                ]),
            ),
            path(
                '<int:pk>/',
                PartStocktakeDetail.as_view(),
                name='api-part-stocktake-detail',
            ),
            path('', PartStocktakeList.as_view(), name='api-part-stocktake-list'),
        ]),
    ),
    path(
        'thumbs/',
        include([
            path('', PartThumbs.as_view(), name='api-part-thumbs'),
            re_path(
                r'^(?P<pk>\d+)/?',
                PartThumbsUpdate.as_view(),
                name='api-part-thumbs-update',
            ),
        ]),
    ),
    # BOM template
    path(
        'bom_template/',
        views.BomUploadTemplate.as_view(),
        name='api-bom-upload-template',
    ),
    path(
        '<int:pk>/',
        include([
            # Endpoint for extra serial number information
            path(
                'serial-numbers/',
                PartSerialNumberDetail.as_view(),
                name='api-part-serial-number-detail',
            ),
            # Endpoint for future scheduling information
            path('scheduling/', PartScheduling.as_view(), name='api-part-scheduling'),
            path(
                'requirements/',
                PartRequirements.as_view(),
                name='api-part-requirements',
            ),
            # Endpoint for duplicating a BOM for the specific Part
            path('bom-copy/', PartCopyBOM.as_view(), name='api-part-bom-copy'),
            # Endpoint for validating a BOM for the specific Part
            path(
                'bom-validate/', PartValidateBOM.as_view(), name='api-part-bom-validate'
            ),
            # Part metadata
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': Part},
                name='api-part-metadata',
            ),
            # Part pricing
            path('pricing/', PartPricingDetail.as_view(), name='api-part-pricing'),
            # BOM download
            path('bom-download/', views.BomDownload.as_view(), name='api-bom-download'),
            # Old pricing endpoint
            path('pricing2/', views.PartPricing.as_view(), name='part-pricing'),
            # Part detail endpoint
            path('', PartDetail.as_view(), name='api-part-detail'),
        ]),
    ),
    path(
        'change_category/',
        PartChangeCategory.as_view(),
        name='api-part-change-category',
    ),

    path('product-list/', PartList2.as_view(), name='api-part-list2'),

    path('', PartList.as_view(), name='api-part-list'),

]

bom_api_urls = [
    path(
        'substitute/',
        include([
            # Detail view
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': BomItemSubstitute},
                        name='api-bom-substitute-metadata',
                    ),
                    path(
                        '',
                        BomItemSubstituteDetail.as_view(),
                        name='api-bom-substitute-detail',
                    ),
                ]),
            ),
            # Catch all
            path('', BomItemSubstituteList.as_view(), name='api-bom-substitute-list'),
        ]),
    ),
    # BOM Item Detail
    path(
        '<int:pk>/',
        include([
            path('validate/', BomItemValidate.as_view(), name='api-bom-item-validate'),
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': BomItem},
                name='api-bom-item-metadata',
            ),
            path('', BomDetail.as_view(), name='api-bom-item-detail'),
        ]),
    ),
    # API endpoint URLs for importing BOM data
    path('import/upload/', BomImportUpload.as_view(), name='api-bom-import-upload'),
    path('import/extract/', BomImportExtract.as_view(), name='api-bom-import-extract'),
    path('import/submit/', BomImportSubmit.as_view(), name='api-bom-import-submit'),
    # Catch-all
    path('', BomList.as_view(), name='api-bom-list'),
]
