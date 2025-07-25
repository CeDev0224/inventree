import { Trans, t } from '@lingui/macro';
import { openContextModal } from '@mantine/modals';

import type { MenuLinkItem } from '../components/items/MenuLinks';
import { StylishText } from '../components/items/StylishText';
import { UserRoles } from '../enums/Roles';

export const navTabs = [
  { text: <Trans>Dashboard</Trans>, name: 'home' },
  { text: <Trans>Products</Trans>, name: 'part', role: UserRoles.part },
  { text: <Trans>Stock</Trans>, name: 'stock', role: UserRoles.stock },
  { text: <Trans>Fulfill Orders</Trans>, name: 'fulfillorders', role: UserRoles.sales_order },
  {
    text: <Trans>Manufacturing</Trans>,
    name: 'manufacturing',
    role: UserRoles.build
  },
  {
    text: <Trans>Purchasing</Trans>,
    name: 'purchasing',
    role: UserRoles.purchase_order
  },
  { text: <Trans>Sales</Trans>, name: 'sales', role: UserRoles.sales_order }
];

export const docLinks = {
  app: 'https://docs.inventree.org/app/',
  getting_started: 'https://docs.inventree.org/en/latest/start/intro/',
  api: 'https://docs.inventree.org/en/latest/api/api/',
  developer: 'https://docs.inventree.org/en/latest/develop/contributing/',
  faq: 'https://docs.inventree.org/en/latest/faq/',
  github: 'https://github.com/inventree/inventree'
};

export function DocumentationLinks(): MenuLinkItem[] {
  return [
    {
      id: 'gettin-started',
      title: t`Getting Started`,
      link: docLinks.getting_started,
      external: true,
      description: t`Getting started with InvenTree`
    },
    {
      id: 'api',
      title: t`API`,
      link: docLinks.api,
      external: true,
      description: t`InvenTree API documentation`
    },
    {
      id: 'developer',
      title: t`Developer Manual`,
      link: docLinks.developer,
      external: true,
      description: t`InvenTree developer manual`
    },
    {
      id: 'faq',
      title: t`FAQ`,
      link: docLinks.faq,
      external: true,
      description: t`Frequently asked questions`
    },
    {
      id: 'github',
      title: t`GitHub Repository`,
      link: docLinks.github,
      external: true,
      description: t`InvenTree source code on GitHub`
    }
  ];
}

export function serverInfo() {
  return openContextModal({
    modal: 'info',
    title: (
      <StylishText size='xl'>
        <Trans>System Information</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function aboutInvenTree() {
  return openContextModal({
    modal: 'about',
    title: (
      <StylishText size='xl'>
        <Trans>About InvenTree</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function licenseInfo() {
  return openContextModal({
    modal: 'license',
    title: (
      <StylishText size='xl'>
        <Trans>License Information</Trans>
      </StylishText>
    ),
    size: 'xl',
    innerProps: {}
  });
}

export function AboutLinks(): MenuLinkItem[] {
  return [
    {
      id: 'instance',
      title: t`System Information`,
      description: t`About this InvenTree instance`,
      icon: 'info',
      action: serverInfo
    },
    {
      id: 'about',
      title: t`About InvenTree`,
      description: t`About the InvenTree Project`,
      icon: 'info',
      action: aboutInvenTree
    },
    {
      id: 'licenses',
      title: t`License Information`,
      description: t`Licenses for dependencies of the InvenTree software`,
      icon: 'license',
      action: licenseInfo
    }
  ];
}
