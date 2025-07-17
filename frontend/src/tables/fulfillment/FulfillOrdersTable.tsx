import { t } from '@lingui/macro';
import { Badge, Group } from '@mantine/core';
import { IconTruck } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { Thumbnail } from '../../components/images/Thumbnail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { TableColumn } from '../Column';
import {
  CreationDateColumn,
  DescriptionColumn,
  ReferenceColumn,
  StatusColumn,
  TargetDateColumn
} from '../ColumnRenderers';
import { StatusFilterOptions, type TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function FulfillOrdersTable() {
  const table = useTable('fulfill-orders');
  const navigate = useNavigate();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'status',
        label: t`Status`,
        description: t`Filter by order status`,
        choiceFunction: StatusFilterOptions(ModelType.salesorder)
      },
      {
        name: 'overdue',
        label: t`Overdue`,
        description: t`Show overdue orders`
      }
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'reference',
        switchable: false
      }),
      {
        accessor: 'customer__name',
        title: t`Customer`,
        sortable: true,
        switchable: false,
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
      DescriptionColumn({}),
      {
        accessor: 'line_items',
        title: t`Items Progress`,
        sortable: true,
        render: (record: any) => (
          <ProgressBar
            progressLabel={true}
            value={record.shipped_lines || 0}
            maximum={record.line_items || 0}
          />
        )
      },
      StatusColumn({ 
        model: ModelType.salesorder,
        accessor: 'status_custom_key'
      }),
      TargetDateColumn({}),
      CreationDateColumn({}),
      {
        accessor: 'priority',
        title: t`Priority`,
        sortable: false,
        render: (record: any) => {
          // Simple priority logic based on target date and status
          const isOverdue = record.overdue;
          const isUrgent = record.target_date && new Date(record.target_date) <= new Date(Date.now() + 24 * 60 * 60 * 1000);
          
          if (isOverdue) {
            return <Badge color="red" size="sm">{t`Overdue`}</Badge>;
          } else if (isUrgent) {
            return <Badge color="orange" size="sm">{t`Urgent`}</Badge>;
          } else {
            return <Badge color="blue" size="sm">{t`Normal`}</Badge>;
          }
        }
      }
    ];
  }, []);

  const handleRowClick = (record: any) => {
    navigate(`/fulfillorders/order/${record.pk}/`);
  };

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.sales_order_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          customer_detail: true,
          outstanding: true, // Only show orders that need fulfillment
          status_in: '15,20' // IN_PROGRESS and SHIPPED statuses
        },
        tableFilters: tableFilters,
        onRowClick: handleRowClick,
        modelType: ModelType.salesorder,
        enableSelection: false,
        enableDownload: true,
        noRecordsText: t`No orders require fulfillment`
      }}
    />
  );
}