import { ActionIcon, Indicator } from '@mantine/core';
import { IconShoppingCart } from '@tabler/icons-react';
import { useCart } from '../contexts/CartContext';
import { useNavigate } from 'react-router-dom';

export function CartIcon() {
  const { cart } = useCart();
  const navigate = useNavigate();
  const total = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <Indicator label={total} size={16} disabled={total === 0}>
      <ActionIcon size="lg" onClick={() => navigate('/cart')}>
        <IconShoppingCart />
      </ActionIcon>
    </Indicator>
  );
}
