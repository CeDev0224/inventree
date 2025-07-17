import { Trans } from '@lingui/macro';
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  Image,
  Text,
  Group,
  Button,
  Loader,
  Stack,
} from '@mantine/core';
import { useCart } from '../../contexts/CartContext';
import { CartIcon } from '../../components/CartIcon';

export default function ProductPage() {
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const [quantities, setQuantities] = React.useState<{ [pk: number]: number }>({});

  // Fetch products without authentication
  const { data: products, isLoading } = useQuery({
    queryKey: ['public-products'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.product_list), {
          headers: { Authorization: '' }, // Remove auth header for public access
        })
        .then((res) => res.data),
  });

  if (isLoading) {
    return (
      <Container size="md" py="xl">
        <Group>
          <Loader />
          <Text>Loading products...</Text>
        </Group>
      </Container>
    );
  }

  return (
    <Container size="lg" py="xl">
      <Group justify="space-between" mb="lg">
        <Text size="xl">
          <Trans>Our Products</Trans>
        </Text>
        <Group>
          <Button variant="outline" onClick={() => navigate('/login')}>
            <Trans>Login</Trans>
          </Button>
          <CartIcon />
        </Group>
      </Group>
      <Grid columns={4}>
        {products?.map((product: any) => (
          <Grid.Col key={product.pk} span={1} >
            <Card
              shadow="sm"
              padding="lg"
              radius="md"
              withBorder
              style={{
                cursor: 'pointer',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
              title={product.name}
            >
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
              </Stack>              
              <Group mt="md">
                <Button
                  variant="default"
                  onClick={e => {
                    e.stopPropagation();
                    setQuantities(q => ({ ...q, [product.pk]: Math.max(1, (q[product.pk] || 1) - 1) }));
                  }}
                >
                  -
                </Button>
                <Text>{quantities[product.pk] || 1}</Text>
                <Button
                  variant="default"
                  onClick={e => {
                    e.stopPropagation();
                    setQuantities(q => ({ ...q, [product.pk]: (q[product.pk] || 1) + 1 }));
                  }}
                >
                  +
                </Button>
                <Button
                  variant="filled"
                  color="blue"
                  onClick={e => {
                    e.stopPropagation();
                    addToCart(product, quantities[product.pk] || 1);
                  }}
                >
                  <Trans>Add to Cart</Trans>
                </Button>
              </Group>
            </Card>
          </Grid.Col>
        ))}
      </Grid>
    </Container>
  );
}