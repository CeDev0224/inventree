import React, { useState } from 'react';
import { Container, TextInput, Textarea, Button, Title, Group, Notification, Select } from '@mantine/core';
import { useForm } from '@mantine/form';
import { apiUrl } from '../../states/ApiState';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { api } from '../../App';
import { useNavigate } from 'react-router-dom';

// Example currency options, you may want to fetch these from your backend or settings
const currencyOptions = [
  { value: 'USD', label: 'USD - US Dollar' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'GBP', label: 'GBP - British Pound' },
  // ...add more as needed
];

export default function CustomerRegisterPage() {
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const form = useForm({
    initialValues: {
      name: '',
      description: '',
      website: '',
      email: '',
      phone: '',
      address: '',
      currency: '',
    },
    validate: {
      name: (value) => (value.length < 2 ? 'Name is too short' : null),
      email: (value) => (value && !/^\S+@\S+$/.test(value) ? 'Invalid email' : null),
      currency: (value) => (!value ? 'Currency is required' : null),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setError(null);
    setSuccess(false);
    try {
      await api.post(apiUrl(ApiEndpoints.customer_register), values);
      setSuccess(true);
      form.reset();
      navigate('/products'); 
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <Container size="sm" py="xl">
      <Title order={2} mb="md">Register as a Customer</Title>
      {success && <Notification color="green" mb="md">Registration successful!</Notification>}
      {error && <Notification color="red" mb="md">{error}</Notification>}
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <TextInput label="Name" required {...form.getInputProps('name')} mb="sm" />
        <Textarea label="Description" {...form.getInputProps('description')} mb="sm" />
        <TextInput label="Website" {...form.getInputProps('website')} mb="sm" />
        <TextInput label="Email" {...form.getInputProps('email')} mb="sm" />
        <TextInput label="Phone" {...form.getInputProps('phone')} mb="sm" />
        <Textarea label="Address" {...form.getInputProps('address')} mb="sm" />
        <Select
          label="Currency"
          placeholder="Select currency"
          data={currencyOptions}
          required
          {...form.getInputProps('currency')}
          mb="sm"
        />
        <Group>
          <Button type="submit">Register</Button>
        </Group>
      </form>
    </Container>
  );
}