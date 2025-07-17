"""Admin classes."""

from django.contrib import admin
from django.db.models.fields import CharField
from django.http.request import HttpRequest

from djmoney.contrib.exchange.admin import RateAdmin
from djmoney.contrib.exchange.models import Rate
from import_export.exceptions import ImportExportError
from import_export.resources import ModelResource


class InvenTreeResource(ModelResource):
    MAX_IMPORT_ROWS = 1000
    MAX_IMPORT_COLS = 100

    # List of fields which should be converted to empty strings if they are null
    CONVERT_NULL_FIELDS = []

    def import_data_inner(
        self,
        dataset,
        dry_run,
        raise_errors,
        using_transactions,
        collect_failed_rows,
        rollback_on_validation_errors=None,
        **kwargs,
    ):
        return super().import_data_inner(
            dataset,
            dry_run,
            raise_errors,
            using_transactions,
            collect_failed_rows,
            rollback_on_validation_errors=rollback_on_validation_errors,
            **kwargs,
        )

    def export_resource(self, obj):
        row = super().export_resource(obj)

        return row

    def get_fields(self, **kwargs):
        """Return fields, with some common exclusions."""
        fields = super().get_fields(**kwargs)

        fields_to_exclude = ['metadata', 'lft', 'rght', 'tree_id', 'level']

        return [f for f in fields if f.column_name not in fields_to_exclude]

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """Run custom code before importing data.

        - Determine the list of fields which need to be converted to empty strings
        """
        # Construct a map of field names
        db_fields = {field.name: field for field in self.Meta.model._meta.fields}

        return super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def before_import_row(self, row, row_number=None, **kwargs):
        for field in self.CONVERT_NULL_FIELDS:
            if field in row and row[field] is None:
                row[field] = ''

        return super().before_import_row(row, row_number, **kwargs)


class CustomRateAdmin(RateAdmin):
    """Admin interface for the Rate class."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable the 'add' permission for Rate objects."""
        return False


admin.site.unregister(Rate)
admin.site.register(Rate, CustomRateAdmin)
