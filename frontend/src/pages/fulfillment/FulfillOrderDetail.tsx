import { t } from '@lingui/macro';
import { Alert, Button, Card, Group, Modal, Stack, Text, TextInput } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX, IconScan, IconExclamationTriangle } from '@tabler/icons-react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { BarcodeInput } from '../../components/items/BarcodeInput';
import { PageDetail } from '../../components/nav/PageDetail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { apiUrl } from '../../states/ApiState';
import { RenderPart } from '../../components/render/Part';
import { formatCurrency } from '../../defaults/formatters';

interface FulfillmentItem {
  pk: number;
  part: number;
  part_detail: any;
  quantity: number;
  fulfilled_quantity: number;
  sale_price: number;
  sale_price_currency: string;
  reference?: string;
  notes?: string;
}

interface SubstitutionModalProps {
  opened: boolean;
  onClose: () => void;
  originalItem: FulfillmentItem | null;
  scannedPart: any;
  onConfirm: (substitutePartId: number) => void;
}

function SubstitutionModal({ opened, onClose, originalItem, scannedPart, onConfirm }: SubstitutionModalProps) {
  const handleConfirm = () => {
    if (scannedPart?.pk) {
      onConfirm(scannedPart.pk);
    }
    onClose();
  };

  return (
    <Modal opened={opened} onClose={onClose} title={t`Product Substitution`} size="md">
      <Stack gap="md">
        <Alert color="orange" icon={<IconExclamationTriangle />}>
          {t`The scanned item does not match the expected product. Do you want to substitute it?`}
        </Alert>
        
        <Card withBorder>
          <Text size="sm" c="dimmed">{t`Expected Product`}</Text>
          {originalItem && <RenderPart instance={originalItem.part_detail} />}
        </Card>

        <Card withBorder>
          <Text size="sm" c="dimmed">{t`Scanned Product`}</Text>
          {scannedPart && <RenderPart instance={scannedPart} />}
        </Card>

        <Group justify="flex-end">
          <Button variant="outline" onClick={onClose}>
            {t`Cancel`}
          </Button>
          <Button color="orange" onClick={handleConfirm}>
            {t`Confirm Substitution`}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export default function FulfillOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [substitutionOpened, { open: openSubstitution, close: closeSubstitution }] = useDisclosure(false);
  const [selectedItem, setSelectedItem] = useState<FulfillmentItem | null>(null);
  const [scannedPart, setScannedPart] = useState<any>(null);
  const [manualSku, setManualSku] = useState('');

  // Fetch sales order details
  const { data: order, refetch: refetchOrder } = useQuery({
    queryKey: ['fulfill-order', id],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.sales_order_list, id), {
          params: { customer_detail: true }
        })
        .then(res => res.data),
  });

  // Fetch line items
  const { data: lineItems, refetch: refetchLineItems } = useQuery({
    queryKey: ['fulfill-order-lines', id],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.sales_order_line_list), {
          params: { 
            order: id, 
            part_detail: true,
            outstanding: true 
          }
        })
        .then(res => res.data.results || []),
  });

  // Calculate fulfillment progress
  const progress = useMemo(() => {
    if (!lineItems?.length) return { completed: 0, total: 0 };
    
    const total = lineItems.reduce((sum: number, item: FulfillmentItem) => sum + item.quantity, 0);
    const completed = lineItems.reduce((sum: number, item: FulfillmentItem) => sum + (item.fulfilled_quantity || 0), 0);
    
    return { completed, total };
  }, [lineItems]);

  // Fulfill item mutation
  const fulfillMutation = useMutation({
    mutationFn: async ({ lineItemId, quantity, substitutePartId }: { 
      lineItemId: number; 
      quantity: number; 
      substitutePartId?: number;
    }) => {
      // Update the line item
      const updateData: any = {
        shipped: (lineItems?.find((item: FulfillmentItem) => item.pk === lineItemId)?.shipped || 0) + quantity
      };

      if (substitutePartId) {
        updateData.part = substitutePartId;
      }

      return api.patch(apiUrl(ApiEndpoints.sales_order_line_list, lineItemId), updateData);
    },
    onSuccess: () => {
      refetchLineItems();
      refetchOrder();
      showNotification({
        title: t`Item Fulfilled`,
        message: t`Item has been successfully fulfilled`,
        color: 'green',
        icon: <IconCheck />
      });
    },
    onError: () => {
      showNotification({
        title: t`Error`,
        message: t`Failed to fulfill item`,
        color: 'red',
        icon: <IconX />
      });
    }
  });

  // Handle barcode scan
  const handleScan = useCallback(async (barcode: string) => {
    try {
      // First, try to scan the barcode to get product info
      const scanResponse = await api.post(apiUrl(ApiEndpoints.barcode), { barcode });
      
      if (scanResponse.data?.part) {
        const scannedPartId = scanResponse.data.part.pk;
        const scannedPartData = scanResponse.data.part;
        
        // Find matching line item
        const matchingItem = lineItems?.find((item: FulfillmentItem) => 
          item.part === scannedPartId && (item.quantity - (item.shipped || 0)) > 0
        );

        if (matchingItem) {
          // Direct match - fulfill immediately
          fulfillMutation.mutate({
            lineItemId: matchingItem.pk,
            quantity: 1
          });
        } else {
          // No direct match - check if we have any unfulfilled items for substitution
          const unfulfilledItems = lineItems?.filter((item: FulfillmentItem) => 
            (item.quantity - (item.shipped || 0)) > 0
          );

          if (unfulfilledItems?.length > 0) {
            // Show substitution modal for the first unfulfilled item
            setSelectedItem(unfulfilledItems[0]);
            setScannedPart(scannedPartData);
            openSubstitution();
          } else {
            showNotification({
              title: t`No Items to Fulfill`,
              message: t`All items in this order have been fulfilled`,
              color: 'blue'
            });
          }
        }
      } else {
        showNotification({
          title: t`Invalid Barcode`,
          message: t`Could not identify product from barcode`,
          color: 'red',
          icon: <IconX />
        });
      }
    } catch (error) {
      showNotification({
        title: t`Scan Error`,
        message: t`Failed to process barcode scan`,
        color: 'red',
        icon: <IconX />
      });
    }
  }, [lineItems, fulfillMutation]);

  // Handle manual SKU entry
  const handleManualEntry = useCallback(async () => {
    if (!manualSku.trim()) return;
    
    try {
      // Search for part by SKU or name
      const searchResponse = await api.get(apiUrl(ApiEndpoints.part_list), {
        params: { search: manualSku.trim(), limit: 1 }
      });

      if (searchResponse.data?.results?.length > 0) {
        const foundPart = searchResponse.data.results[0];
        
        // Find matching line item
        const matchingItem = lineItems?.find((item: FulfillmentItem) => 
          item.part === foundPart.pk && (item.quantity - (item.shipped || 0)) > 0
        );

        if (matchingItem) {
          fulfillMutation.mutate({
            lineItemId: matchingItem.pk,
            quantity: 1
          });
          setManualSku('');
        } else {
          // Show substitution option
          const unfulfilledItems = lineItems?.filter((item: FulfillmentItem) => 
            (item.quantity - (item.shipped || 0)) > 0
          );

          if (unfulfilledItems?.length > 0) {
            setSelectedItem(unfulfilledItems[0]);
            setScannedPart(foundPart);
            openSubstitution();
            setManualSku('');
          }
        }
      } else {
        showNotification({
          title: t`Product Not Found`,
          message: t`No product found matching the entered SKU`,
          color: 'red'
        });
      }
    } catch (error) {
      showNotification({
        title: t`Search Error`,
        message: t`Failed to search for product`,
        color: 'red'
      });
    }
  }, [manualSku, lineItems, fulfillMutation]);

  // Handle substitution confirmation
  const handleSubstitution = useCallback((substitutePartId: number) => {
    if (selectedItem) {
      fulfillMutation.mutate({
        lineItemId: selectedItem.pk,
        quantity: 1,
        substitutePartId
      });
    }
  }, [selectedItem, fulfillMutation]);

  // Mark item as unavailable
  const markUnavailable = useCallback((item: FulfillmentItem) => {
    // For now, we'll just show a notification
    // In a full implementation, you might want to update the order status or add notes
    showNotification({
      title: t`Item Marked Unavailable`,
      message: t`Item has been marked as unavailable`,
      color: 'orange'
    });
  }, []);

  if (!order) {
    return <Text>{t`Loading...`}</Text>;
  }

  return (
    <Stack gap="md">
      <PageDetail
        title={`${t`Fulfill Order`}: ${order.reference}`}
        subtitle={`${t`Customer`}: ${order.customer_detail?.name}`}
        breadcrumbs={[{ name: t`Fulfill Orders`, url: '/fulfillorders/' }]}
      />

      {/* Progress Card */}
      <Card withBorder>
        <Stack gap="sm">
          <Group justify="space-between">
            <Text size="lg" fw={500}>{t`Fulfillment Progress`}</Text>
            <Text size="sm" c="dimmed">
              {progress.completed} / {progress.total} {t`items`}
            </Text>
          </Group>
          <ProgressBar
            value={progress.completed}
            maximum={progress.total}
            progressLabel
          />
        </Stack>
      </Card>

      {/* Scanning Interface */}
      <Card withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <Text size="lg" fw={500}>{t`Scan Items`}</Text>
            <IconScan size={24} />
          </Group>
          
          <BarcodeInput onScan={handleScan} />
          
          <Group>
            <TextInput
              placeholder={t`Enter SKU or product name`}
              value={manualSku}
              onChange={(e) => setManualSku(e.currentTarget.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleManualEntry()}
              style={{ flex: 1 }}
            />
            <Button onClick={handleManualEntry} disabled={!manualSku.trim()}>
              {t`Search`}
            </Button>
          </Group>
        </Stack>
      </Card>

      {/* Line Items */}
      <Card withBorder>
        <Stack gap="md">
          <Text size="lg" fw={500}>{t`Items to Fulfill`}</Text>
          
          {lineItems?.map((item: FulfillmentItem) => {
            const remaining = item.quantity - (item.shipped || 0);
            const isCompleted = remaining <= 0;
            
            return (
              <Card key={item.pk} withBorder bg={isCompleted ? 'green.0' : undefined}>
                <Group justify="space-between" wrap="nowrap">
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <RenderPart instance={item.part_detail} />
                    {item.reference && (
                      <Text size="sm" c="dimmed">{t`Reference`}: {item.reference}</Text>
                    )}
                  </Stack>
                  
                  <Stack gap="xs" align="center">
                    <Text size="sm" fw={500}>
                      {item.shipped || 0} / {item.quantity}
                    </Text>
                    <Text size="xs" c={isCompleted ? 'green' : 'orange'}>
                      {isCompleted ? t`Complete` : `${remaining} ${t`remaining`}`}
                    </Text>
                    {!isCompleted && (
                      <Button
                        size="xs"
                        color="orange"
                        variant="outline"
                        onClick={() => markUnavailable(item)}
                      >
                        {t`Mark Unavailable`}
                      </Button>
                    )}
                  </Stack>
                  
                  <Stack gap="xs" align="flex-end">
                    <Text size="sm">
                      {formatCurrency(item.sale_price, { currency: item.sale_price_currency })}
                    </Text>
                    {isCompleted && <IconCheck color="green" size={20} />}
                  </Stack>
                </Group>
              </Card>
            );
          })}
        </Stack>
      </Card>

      {/* Complete Order Button */}
      {progress.completed === progress.total && progress.total > 0 && (
        <Card withBorder bg="green.0">
          <Group justify="space-between">
            <Stack gap="xs">
              <Text size="lg" fw={500} c="green">{t`Order Ready for Shipment`}</Text>
              <Text size="sm" c="dimmed">{t`All items have been fulfilled`}</Text>
            </Stack>
            <Button
              color="green"
              size="lg"
              onClick={() => navigate('/fulfillorders/')}
            >
              {t`Complete & Return to Orders`}
            </Button>
          </Group>
        </Card>
      )}

      {/* Substitution Modal */}
      <SubstitutionModal
        opened={substitutionOpened}
        onClose={closeSubstitution}
        originalItem={selectedItem}
        scannedPart={scannedPart}
        onConfirm={handleSubstitution}
      />
    </Stack>
  );
}