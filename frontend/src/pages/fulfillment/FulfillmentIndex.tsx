import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import { IconTruckDelivery } from '@tabler/icons-react';
import { useMemo } from 'react';

import PermissionDenied from '../../components/errors/PermissionDenied';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { UserRoles } from '../../enums/Roles';
import { useUserState } from '../../states/UserState';
import { FulfillmentOrderTable } from '../../tables/fulfillment/FulfillmentOrderTable';

export default function FulfillmentIndex() {
  const user = useUserState();

  const panels = useMemo(() => {
    return [
      {
        name: 'orders',
        label: t`Orders to Fulfill`,
        icon: <IconTruckDelivery />,
        content: <FulfillmentOrderTable />
      }
    ];
  }, []);

  if (!user.isLoggedIn() || !user.hasViewRole(UserRoles.sales_order)) {
    return <PermissionDenied />;
  }

  return (
    <Stack>
      <PageDetail title={t`Order Fulfillment`} />
      <PanelGroup
        pageKey='fulfillment-index'
        panels={panels}
        model={'fulfillment'}
        id={null}
      />
    </Stack>
  );
}