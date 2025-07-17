import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { useMemo } from 'react';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { FulfillOrdersTable } from '../../tables/fulfillment/FulfillOrdersTable';

export default function FulfillOrdersIndex() {
  const panels = useMemo(() => {
    return [
      {
        name: 'orders',
        label: t`Orders to Fulfill`,
        icon: null,
        content: <FulfillOrdersTable />
      }
    ];
  }, []);

  return (
    <Stack>
      <PageDetail title={t`Fulfill Orders`} />
      <PanelGroup
        pageKey='fulfill-orders-index'
        panels={panels}
        model={'fulfillorders'}
        id={null}
      />
    </Stack>
  );
}