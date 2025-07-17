import { Trans } from '@lingui/macro';
import React, { useState, useEffect } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import {
    Container, Card, Image, Text, Group, Button, Stack, NumberInput, TextInput, Loader, Paper, Notification
} from '@mantine/core';

export default function OrderDetailPage() {
    const { productId } = useParams();
    const navigate = useNavigate();
    const [quantity, setQuantity] = useState(1);
    const [email, setEmail] = useState('');
    const [customer, setCustomer] = useState<any>(null);
    const [customerFields, setCustomerFields] = useState({
        name: '',
        description: '',
        website: '',
        phone: '',
        address: '',
        currency: '',
        email: '',
    });
    const [error, setError] = useState<string | null>(null);

    // Fetch product details
    const location = useLocation();
    const { product } = location.state || {};

    // Check if customer exists by email
    const { refetch: fetchCustomer } = useQuery({
        queryKey: ['customer', email],
        queryFn: () =>
            api
                .get(apiUrl(ApiEndpoints.public_company_list), { params: { email } })
                .then(res => res.data.length > 0 ? res.data[0] : null),
        enabled: false, // Only fetch when you call fetchCustomer()
    });

    // When you want to check the customer (e.g., onBlur of email input)
    const handleEmailBlur = async () => {
        if (email) {
            const { data } = await fetchCustomer();
            if (data) {
                setCustomer(data);
                setCustomerFields({
                    name: data.name,
                    description: data.description,
                    website: data.website,
                    phone: data.phone,
                    address: data.address,
                    currency: data.currency,
                    email: data.email,
                });
            } else {
                console.log('herere');
                setCustomer(null);
                setCustomerFields({
                    name: '',
                    description: '',
                    website: '',
                    phone: '',
                    address: '',
                    currency: '',
                    email: email, // keep the email the user typed
                });
            }
        }
    };

    const createOrder = useMutation({
        mutationFn: (orderData: any) =>
            api.post(apiUrl(ApiEndpoints.sales_order_create), orderData).then(res => res.data),
        onSuccess: (data) => {
            setError(null);
            console.log('success', data);
            navigate('/products');
        },
        onError: (err: any) => {
            setError(err?.response?.data?.detail || 'Order failed');
        },
    });

    // Prepare payload
    const getPayload = () => {
        if (customer?.pk) {
            // Existing customer
            return {
                product_id: productId,
                quantity,
                customer_id: customer.pk,
            };
        } else {
            // New customer
            return {
                product_id: productId,
                quantity,
                name: customerFields.name,
                email: customerFields.email,
                phone: customerFields.phone,
                address: customerFields.address,
                currency: customerFields.currency,
            };
        }
    };

    if (!product) {
        return <Text>No product data. Please go back to the products page.</Text>;
    }

    return (
        <Container size="sm" py="xl">
            <Card>
                <Group align="flex-start">
                    <Card.Section>
                        <Image
                            src={product.thumbnail || '/static/img/blank_image.png'}
                            alt={product.name}
                            height={180}
                            fit="cover"
                        />
                    </Card.Section>
                    <Stack mt="sm" style={{ flexGrow: 1 }}>
                        <Text size="lg">
                            {product.name}
                        </Text>
                        <Text color="dimmed" size="sm" lineClamp={2}>
                            {product.description}
                        </Text>
                        <Text size="xs" color="gray">
                            <Trans>Supplier:</Trans> {product.supplier_name || '-'}
                        </Text>
                        <Text size="xs" color="gray">
                            <Trans>SKU:</Trans> {product.supplier_sku || '-'}
                        </Text>
                        <Text size="xs" color="gray">
                            <Trans>UPC:</Trans> {product.upc_num || '-'}
                        </Text>
                    </Stack>
                    <Text size="lg">
                        {product.pricing_min != null
                            ? `$${Number(product.pricing_min).toFixed(2)}`
                            : <Text color="gray" size="sm"><Trans>Contact for price</Trans></Text>}
                    </Text>
                </Group>
                {/* Quantity input */}
                <Stack mt="lg" mb="md">
                    <NumberInput
                        label="Quantity"
                        value={quantity}
                        min={1}
                        onChange={val => setQuantity(parseInt(val.toString()) || 1)}
                        style={{ maxWidth: 200 }}
                        required
                    />
                </Stack>
                <Paper mt="lg" p="md" withBorder>
                    <Text size="md" mb="sm">Customer Details</Text>
                    <Stack>
                        <TextInput
                            label="Email"
                            value={email}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setEmail(value);
                            }}
                            onBlur={handleEmailBlur}
                            required
                        />
                        <TextInput
                            label="Name"
                            value={customerFields.name}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setCustomerFields(f => ({ ...f, name: value }));
                            }}
                            required
                            disabled={!!customer}
                        />
                        <TextInput
                            label="Description"
                            value={customerFields.description}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setCustomerFields(f => ({ ...f, description: value }));
                            }}
                            disabled={!!customer}
                        />
                        <TextInput
                            label="Website"
                            value={customerFields.website}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setCustomerFields(f => ({ ...f, website: value }));
                            }}
                            disabled={!!customer}
                        />
                        <TextInput
                            label="Phone"
                            value={customerFields.phone}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setCustomerFields(f => ({ ...f, phone: value }));
                            }}
                            disabled={!!customer}
                        />
                        <TextInput
                            label="Address"
                            value={customerFields.address}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setCustomerFields(f => ({ ...f, address: value }));
                            }}
                            disabled={!!customer}
                        />
                        <TextInput
                            label="Currency"
                            value={customerFields.currency}
                            onChange={e => {
                                const value = e.currentTarget.value;
                                setCustomerFields(f => ({ ...f, currency: value }));
                            }}
                            disabled={!!customer}
                        />
                    </Stack>
                </Paper>
                {error && <Notification color="red" mb="md">{error}</Notification>}
                <Button
                    fullWidth
                    onClick={() => createOrder.mutate(getPayload())}
                >
                    Confirm Order
                </Button>
            </Card>
        </Container>
    );
}