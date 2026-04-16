# Enhanced TON Payment System Documentation

## Overview

The enhanced TON payment system now supports both **Testnet (Sandbox)** and **Mainnet** environments, with proper blockchain verification and integration with the TON API.

## 🎯 Payment Modes

### 1. **Simulation Mode** 
- **Purpose**: Development testing without any real transactions
- **Behavior**: Auto-approves all payments instantly
- **Cost**: No real money involved
- **Use Case**: Bot functionality testing

### 2. **TON Testnet Mode (Sandbox)**
- **Purpose**: Testing with real blockchain but fake tokens
- **Behavior**: Uses TON testnet with test tokens
- **Cost**: Free test tokens (no real value)
- **Use Case**: Payment flow testing before going live

### 3. **TON Mainnet Mode (Production)**
- **Purpose**: Real payments with real TON
- **Behavior**: Uses live TON blockchain
- **Cost**: Real TON tokens with real value
- **Use Case**: Production environment

## 🔧 Configuration

### Admin Settings (Dashboard)

#### Payment Configuration Section:
```
☑️ Enable Telegram Stars
☑️ Enable TON Payments  
☑️ TON Testnet Mode (Sandbox)    <- New option
```

#### TON API Configuration:
- **TON Wallet Address**: Your wallet address (testnet or mainnet)
- **TON API Key**: Optional for higher rate limits

#### Simulation Settings:
- **Simulation Mode**: For complete testing without blockchain

## 🏗️ Technical Implementation

### Network Selection
```python
# Automatic endpoint selection based on testnet mode
self.ton_api_endpoint = (
    "https://testnet.toncenter.com/api/v2/" if self.ton_testnet else 
    "https://toncenter.com/api/v2/"
)
```

### Payment URL Generation
```python
# Testnet payments include testnet parameter
if self.ton_testnet:
    payment_url = f"https://app.tonkeeper.com/transfer/{wallet}?amount={amount}&text={comment}&testnet=true"
else:
    payment_url = f"https://app.tonkeeper.com/transfer/{wallet}?amount={amount}&text={comment}"
```

### Blockchain Verification
```python
async def _check_ton_transaction(self, wallet_address, expected_amount, expected_comment, since_timestamp):
    # Real blockchain verification using TON API
    # Checks last 100 transactions for matching amount and comment
    # Supports both testnet and mainnet
```

## 🚀 Usage Workflow

### For Testing (Recommended Path):

1. **Start with Simulation Mode**:
   - ✅ Enable "Simulation Mode"
   - Test all bot functionality
   - No real transactions

2. **Move to TON Testnet**:
   - ✅ Keep "TON Testnet Mode" enabled
   - ❌ Disable "Simulation Mode"
   - Set testnet wallet address
   - Test with free test tokens

3. **Go to Production**:
   - ❌ Disable "TON Testnet Mode"
   - ❌ Keep "Simulation Mode" disabled
   - Set mainnet wallet address
   - Real payments with real TON

### Payment Verification Flow:

```
User initiates payment
        ↓
Transaction created in database
        ↓
Payment URL generated (testnet/mainnet)
        ↓
User sends TON via wallet
        ↓
Background task checks blockchain
        ↓
Transaction verified and completed
        ↓
Credits added to user account
```

## 🛠️ Setup Instructions

### 1. **Get TON Wallet Addresses**

#### For Testnet:
1. Install Tonkeeper wallet
2. Enable Developer Mode
3. Switch to Testnet
4. Get testnet wallet address
5. Get free test TON from faucet

#### For Mainnet:
1. Use your real TON wallet address
2. Ensure it can receive TON payments

### 2. **Configure API Access (Optional)**

#### Get TON API Key:
- Visit: https://toncenter.com
- Or message @tonapibot on Telegram
- Higher rate limits for payment verification

### 3. **Admin Dashboard Setup**

1. Go to: `http://localhost:5000/settings`
2. Configure **Payment Configuration**:
   - ✅ Enable TON Payments
   - ✅ TON Testnet Mode (for testing)
   - Add your TON wallet address
   - Add TON API key (optional)
3. Save settings

## 🧪 Testing Guide

### Test Scenarios:

#### 1. **Simulation Mode Testing**:
```bash
# Enable simulation mode
# All payments auto-complete
# No real blockchain interaction
```

#### 2. **Testnet Integration Testing**:
```bash
# Disable simulation, enable testnet
# Get test TON from faucet
# Test real payment flow with fake tokens
# Verify blockchain integration works
```

#### 3. **Mainnet Production Testing**:
```bash
# Disable both simulation and testnet
# Use small real TON amounts
# Verify real payments work
# Monitor transaction verification
```

## 🔍 Verification Process

### Automatic Verification:
```python
# Background task runs every 5 minutes
# Checks pending TON transactions
# Queries blockchain for payments
# Matches amount and comment
# Auto-completes verified transactions
```

### Manual Verification:
```python
# Admin can check transaction status
# View pending payments in dashboard
# Force verification if needed
```

## 📊 Monitoring & Debugging

### Log Messages:
```
INFO: TON payment verified and completed for transaction 123
ERROR: TON API error: 429 (rate limit)
ERROR: Error checking TON transaction: Network timeout
```

### Admin Dashboard:
- View all transactions (pending/completed)
- Monitor payment success rates
- Check user payment history
- Transaction status tracking

## 🚨 Important Notes

### Security Considerations:
- **Start with Testnet**: Always test thoroughly before mainnet
- **Wallet Security**: Keep wallet private keys secure
- **API Keys**: Store TON API keys securely
- **Rate Limits**: Monitor API usage

### Network Differences:
- **Testnet**: Free test tokens, safe testing environment
- **Mainnet**: Real money, production environment
- **API Endpoints**: Different URLs for testnet/mainnet

### User Experience:
- Clear network indication in payment messages
- Testnet warnings for users
- Automatic payment verification
- Status updates

## 🛡️ Error Handling

### Common Issues:
1. **API Rate Limits**: Use API key for higher limits
2. **Network Timeouts**: Retry mechanism implemented
3. **Invalid Transactions**: Proper validation and logging
4. **Wallet Connectivity**: Clear error messages

### Fallback Options:
- Manual transaction verification
- Admin override capabilities
- User support contact information

## 📈 Production Checklist

Before going live:
- [ ] Test extensively on testnet
- [ ] Verify wallet address is correct
- [ ] Set appropriate payment amounts
- [ ] Monitor initial transactions closely
- [ ] Have support procedures ready
- [ ] Document user payment instructions

## 🔮 Future Enhancements

Potential improvements:
- **Multi-wallet Support**: Support multiple receiving wallets
- **Payment Webhooks**: Real-time payment notifications
- **Refund System**: Automated refund processing
- **Analytics Dashboard**: Payment analytics and reporting
- **Mobile Wallets**: Direct integration with mobile wallets

## 📞 Support

For issues:
1. Check logs for error messages
2. Verify network settings (testnet/mainnet)
3. Ensure wallet address is correct
4. Check API key and rate limits
5. Monitor blockchain explorer for transactions

This enhanced system provides a complete testing and production pathway for TON payments! 🚀