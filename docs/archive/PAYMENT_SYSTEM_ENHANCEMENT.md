# Payment System Enhancement: Sandbox vs Mainnet Selection

## Overview

This update improves the TON payment configuration by replacing the simple "testnet mode" checkbox with a clean dropdown selection and separate wallet address fields for testnet and mainnet.

## Changes Made

### 1. Admin Dashboard UI (`templates/settings.html`)

**Before:**
- Single TON wallet address field
- Checkbox for "TON Testnet Mode (Sandbox)"

**After:**
- Dropdown selection: "Sandbox (Testnet)" or "Mainnet"
- Separate wallet address fields for testnet and mainnet
- Cleaner, more intuitive interface

### 2. Backend Configuration (`admin_dashboard.py`)

**New Settings:**
- `ton_network_mode`: 'sandbox' or 'mainnet'
- `ton_mainnet_wallet_address`: Wallet for real TON transactions
- `ton_testnet_wallet_address`: Wallet for sandbox testing

**Removed Settings:**
- `ton_testnet_mode` (boolean) - replaced with dropdown
- `ton_wallet_address` - split into mainnet/testnet specific fields

### 3. Payment Handler (`payment_handler.py`)

**New Features:**
- `get_ton_wallet_address()` method automatically selects correct wallet based on network mode
- Dynamic API endpoint selection based on network mode
- Maintains backward compatibility with existing payment flows

## Configuration Guide

### Network Modes

#### 🧪 Sandbox (Testnet)
- **Purpose**: Safe testing with fake TON tokens
- **API**: `https://testnet.toncenter.com/api/v2/`
- **Wallet**: Uses testnet wallet address
- **URL**: Includes `testnet=true` parameter for Tonkeeper

#### 💎 Mainnet
- **Purpose**: Real TON transactions with actual value
- **API**: `https://toncenter.com/api/v2/`
- **Wallet**: Uses mainnet wallet address
- **URL**: Standard Tonkeeper transfer link

### Wallet Address Setup

1. **Same Address for Both Networks**: You can use the same wallet address for both testnet and mainnet - TON addresses work on both networks.

2. **Separate Addresses**: For better organization, you can use different addresses for testing and production.

3. **Address Formats**: Both UQ and EQ address formats are supported and equivalent.

## Migration

### Automatic Migration

The system automatically migrates existing settings:

```bash
python migrate_payment_settings.py
```

**Migration Process:**
1. Checks for existing `ton_wallet_address`
2. Copies it to both `ton_mainnet_wallet_address` and `ton_testnet_wallet_address`
3. Converts `ton_testnet_mode` boolean to `ton_network_mode` dropdown value
4. Preserves all existing functionality

### Manual Migration

If you need to update settings manually:

```python
from database import Database

db = Database()
db.update_setting('ton_mainnet_wallet_address', 'your_mainnet_address')
db.update_setting('ton_testnet_wallet_address', 'your_testnet_address')
db.update_setting('ton_network_mode', 'sandbox')  # or 'mainnet'
```

## Testing

### Test Network Selection

```bash
python test_payment_handler.py
```

This script tests:
- Correct API endpoint selection
- Proper wallet address retrieval
- Payment URL generation
- Network mode switching

### Test Migration

```bash
python test_migration.py
```

This script tests:
- Settings migration from old to new format
- Backward compatibility
- Database integrity

## Usage Examples

### Admin Dashboard
1. Open admin dashboard at `http://localhost:5000`
2. Navigate to Settings
3. In "Payment Configuration" section:
   - Select network mode from dropdown
   - Enter appropriate wallet addresses
   - Save settings

### Programmatic Access

```python
from payment_handler import PaymentHandler
from database import Database

db = Database()
payment_handler = PaymentHandler(db)

# Get current configuration
print(f"Network mode: {payment_handler.ton_network_mode}")
print(f"Wallet address: {payment_handler.get_ton_wallet_address()}")

# Create payment (automatically uses correct network/wallet)
result = await payment_handler.create_ton_payment(
    user_id=123,
    package_id=1,
    amount=5.0
)
```

## Benefits

1. **Clearer Interface**: Dropdown is more intuitive than checkbox
2. **Better Organization**: Separate fields for different network wallets
3. **Flexibility**: Easy switching between sandbox and mainnet
4. **Safety**: Clear distinction between testing and production
5. **Backward Compatibility**: Existing setups continue to work

## Files Modified

- `templates/settings.html` - Updated payment configuration UI
- `admin_dashboard.py` - Added new settings handling
- `payment_handler.py` - Enhanced with network mode selection
- `migrate_payment_settings.py` - Migration script for existing installations
- `test_payment_handler.py` - Testing script for new functionality

## Troubleshooting

### Payment URLs Not Working
- Check that the correct wallet address is set for the selected network
- Verify network mode matches your intended testing/production environment

### Migration Issues
- Run `python test_migration.py` to check current settings
- Manually set new settings if migration script fails
- Check database permissions

### API Errors
- Verify TON API key is set if experiencing rate limits
- Check network connectivity to TON APIs
- Ensure wallet addresses are in correct format (UQ/EQ)