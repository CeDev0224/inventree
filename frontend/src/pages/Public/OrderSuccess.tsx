import { Text, Button, Container, Paper, Center, Stack } from '@mantine/core';
import { IconCheck } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

export default function OrderSuccessPage() {
  const navigate = useNavigate();
  return (
    <Container size="xs" py="xl">
      <Center>
        <Paper p="xl" radius="md" withBorder shadow="md" style={{ width: '100%' }}>
          <Center mb="md">
            <IconCheck size={48} color="green" />
          </Center>
          <Stack align="center" gap={0}>
            <Text size="xl" fw={700} mb="sm">Order Placed!</Text>
            <Text mb="md" c="dimmed">Thank you for your order. We have received your request and will process it soon.</Text>
            <Button mt="md" onClick={() => navigate('/products')} size="md">
              Back to Shop
            </Button>
          </Stack>
        </Paper>
      </Center>
    </Container>
  );
}
