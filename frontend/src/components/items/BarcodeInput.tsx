import { t } from '@lingui/macro';
import { Button, Group, Stack, TextInput } from '@mantine/core';
import { IconScan } from '@tabler/icons-react';
import { useState, useCallback } from 'react';

interface BarcodeInputProps {
  onScan: (barcode: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function BarcodeInput({ onScan, placeholder, disabled }: BarcodeInputProps) {
  const [barcode, setBarcode] = useState('');

  const handleScan = useCallback(() => {
    if (barcode.trim()) {
      onScan(barcode.trim());
      setBarcode('');
    }
  }, [barcode, onScan]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleScan();
    }
  }, [handleScan]);

  return (
    <Stack gap="sm">
      <Group>
        <TextInput
          placeholder={placeholder || t`Scan or enter barcode`}
          value={barcode}
          onChange={(e) => setBarcode(e.currentTarget.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          style={{ flex: 1 }}
          leftSection={<IconScan size={16} />}
        />
        <Button 
          onClick={handleScan} 
          disabled={!barcode.trim() || disabled}
          leftSection={<IconScan size={16} />}
        >
          {t`Scan`}
        </Button>
      </Group>
    </Stack>
  );
}