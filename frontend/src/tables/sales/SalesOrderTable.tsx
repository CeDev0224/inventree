import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useSalesOrderFields } from '../../forms/SalesOrderForms';
import { useOwnerFilters, useProjectCodeFilters } from '../../hooks/UseFilter';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import {
  CreationDateColumn,
  DescriptionColumn,
  LineItemsProgressColumn,
  ProjectCodeColumn,
  ReferenceColumn,
  ResponsibleColumn,
  ShipmentDateColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  HasProjectCodeFilter,
  MaxDateFilter,
  MinDateFilter,
  OutstandingFilter,
  OverdueFilter,
  StatusFilterOptions,
  type TableFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter
} from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function SalesOrderTable({
  partId,
  customerId
}: Readonly<{
  partId?: number;
  customerId?: number;
}>) {
  const table = useTable(!!partId ? 'salesorder-part' : 'salesorder-index');
  const user = useUserState();

  const projectCodeFilters = useProjectCodeFilters();
  const responsibleFilters = useOwnerFilters();

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.salesorder)
      },
      OutstandingFilter(),
      OverdueFilter(),
      AssignedToMeFilter(),
      MinDateFilter(),
      MaxDateFilter(),
      CreatedBeforeFilter(),
      CreatedAfterFilter(),
      TargetDateBeforeFilter(),
      TargetDateAfterFilter(),
      CompletedBeforeFilter(),
      CompletedAfterFilter(),
      {
        name: 'project_code',
        label: t`Project Code`,
        description: t`Filter by project code`,
        choices: projectCodeFilters.choices
      },
      HasProjectCodeFilter(),
      {
        name: 'assigned_to',
        label: t`Responsible`,
        description: t`Filter by responsible owner`,
        choices: responsibleFilters.choices
      }
    ];

    if (!!partId) {
      filters.push({
        name: 'include_variants',
        type: 'boolean',
        label: t`Include Variants`,
        description: t`Include orders for product variants`
      });
    }

    return filters;
  }, [partId, projectCodeFilters.choices, responsibleFilters.choices]);

  const salesOrderFields = useSalesOrderFields({});

  const newSalesOrder = useCreateApiFormModal({
    url: ApiEndpoints.sales_order_list,
    title: t`Add Sales Order`,
    fields: salesOrderFields,
    initialData: {
      customer: customerId
    },
    follow: true,
    modelType: ModelType.salesorder
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-sales-order'
        tooltip={t`Add Sales Order`}
        onClick={() => newSalesOrder.open()}
        hidden={!user.hasAddRole(UserRoles.sales_order)}
      />
    ];
  }, [user]);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        render: (record: any) => {
          const customer = record.customer_detail ?? {};

          return (
            <Thumbnail
              src={customer?.image}
              alt={customer.name}
              text={customer.name}
            />
          );
        }
      },
      {
        accessor: 'customer_reference',
        title: t`Customer Reference`
      },
      DescriptionColumn({}),
      LineItemsProgressColumn(),
      {
        accessor: 'shipments_count',
        title: t`Shipments`,
        render: (record: any) => (
          <ProgressBar
            progressLabel
            value={record.completed_shipments_count}
            maximum={record.shipments_count}
          />
        )
      },
      StatusColumn({ model: ModelType.salesorder }),
      ProjectCodeColumn({}),
      CreationDateColumn({}),
      TargetDateColumn({}),
      ShipmentDateColumn({}),
      ResponsibleColumn({}),
      {
        accessor: 'total_price',
        title: t`Total Price`,
        sortable: true,
        render: (record: any) => {
          return formatCurrency(record.total_price, {
            currency: record.order_currency || record.customer_detail?.currency
          });
        }
      }
    ];
  }, []);

  return (
    <>
      {newSalesOrder.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.sales_order_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            customer_detail: true,
            part: partId,
            customer: customerId
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.salesorder,
          enableSelection: true,
          enableDownload: true,
          enableReports: true
        }}
      />
    </>
  );
}
