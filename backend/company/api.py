"""Provides a JSON API for the Company app."""

from django.db.models import Q
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters

import part.models
from importer.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER, SEARCH_ORDER_FILTER_ALIAS
from InvenTree.helpers import str2bool
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    ManufacturerPartParameter,
    SupplierPart,
    SupplierPriceBreak,
)
from .serializers import (
    AddressSerializer,
    CompanySerializer,
    ContactSerializer,
    ManufacturerPartParameterSerializer,
    ManufacturerPartSerializer,
    SupplierPartSerializer,
    SupplierPriceBreakSerializer,
)


from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PublicCustomerRegisterSerializer


from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

manufacturer_part_api_urls = [
    path(
        'parameter/',
        include([
            path(
                '<int:pk>/',
                ManufacturerPartParameterDetail.as_view(),
                name='api-manufacturer-part-parameter-detail',
            ),
            # Catch anything else
            path(
                '',
                ManufacturerPartParameterList.as_view(),
                name='api-manufacturer-part-parameter-list',
            ),
        ]),
    ),
    re_path(
        r'^(?P<pk>\d+)/?',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': ManufacturerPart},
                name='api-manufacturer-part-metadata',
            ),
            path(
                '',
                ManufacturerPartDetail.as_view(),
                name='api-manufacturer-part-detail',
            ),
        ]),
    ),
    # Catch anything else
    path('', ManufacturerPartList.as_view(), name='api-manufacturer-part-list'),
]


supplier_part_api_urls = [
    re_path(
        r'^(?P<pk>\d+)/?',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': SupplierPart},
                name='api-supplier-part-metadata',
            ),
            path('', SupplierPartDetail.as_view(), name='api-supplier-part-detail'),
        ]),
    ),
    # Catch anything else
    path('', SupplierPartList.as_view(), name='api-supplier-part-list'),
]


company_api_urls = [

    path('register-customer', PublicCustomerRegisterView.as_view(), name='api-register-customer'),
    path('get-customers', PublicCompanyList.as_view(), name='api-get-customers'),


    path('part/manufacturer/', include(manufacturer_part_api_urls)),
    path('part/', include(supplier_part_api_urls)),
    # Supplier price breaks
    path(
        'price-break/',
        include([
            re_path(
                r'^(?P<pk>\d+)/?',
                SupplierPriceBreakDetail.as_view(),
                name='api-part-supplier-price-detail',
            ),
            path(
                '',
                SupplierPriceBreakList.as_view(),
                name='api-part-supplier-price-list',
            ),
        ]),
    ),
    re_path(
        r'^(?P<pk>\d+)/?',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': Company},
                name='api-company-metadata',
            ),
            path('', CompanyDetail.as_view(), name='api-company-detail'),
        ]),
    ),
    path(
        'contact/',
        include([
            re_path(
                r'^(?P<pk>\d+)/?',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': Contact},
                        name='api-contact-metadata',
                    ),
                    path('', ContactDetail.as_view(), name='api-contact-detail'),
                ]),
            ),
            path('', ContactList.as_view(), name='api-contact-list'),
        ]),
    ),
    path(
        'address/',
        include([
            path('<int:pk>/', AddressDetail.as_view(), name='api-address-detail'),
            path('', AddressList.as_view(), name='api-address-list'),
        ]),
    ),

    path('', CompanyList.as_view(), name='api-company-list'),
]
