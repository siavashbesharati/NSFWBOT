# TON Payment Verification Process

## What the System Actually Checks

Based on your testnet transaction example:
```
https://testnet.tonviewer.com/transaction/aa3c37a1adf81f2689a53780fe183ab67c133da2efcd206681105ddc7742073f
```

### Transaction Details Being Verified:
- **From**: `0QDKgGqU…7UKEnfCP` (User's wallet)
- **To**: `0QBwmbT0…3_H3yEez` (Bot's wallet)
- **Amount**: `0.5 TON` (500000000 nanoTON)
- **Comment**: `Payment_26_328410861`
- **Status**: Confirmed ✅

## Current Verification Logic

### 1. **API Endpoint Used**
```python
# For testnet (sandbox mode)
self.ton_api_endpoint = "https://testnet.toncenter.com/api/v2/"

# For mainnet  
self.ton_api_endpoint = "https://toncenter.com/api/v2/"
```

### 2. **What Gets Checked**

#### A. **Transaction Timing**
```python
# Only check transactions after payment was created
since_unix = int(since_dt.timestamp())
if tx.get('utime', 0) < since_unix:
    continue  # Skip older transactions
```

#### B. **Incoming Messages**
```python
# Look for incoming messages to our wallet
in_msg = tx.get('in_msg', {})
if not in_msg:
    continue  # Skip outgoing transactions
```

#### C. **Amount Verification**
```python
# Convert from nanoTON to TON
value = int(in_msg.get('value', 0))        # Gets: 500000000
amount_ton = value / 1000000000            # Converts to: 0.5
  
# Check if amount matches (with tolerance for fees)
if abs(amount_ton - expected_amount) < 0.001:  # 0.5 ≈ 0.5 ✅
```

#### D. **Comment Verification**
```python
# Check if payment comment matches
message = in_msg.get('message', '')        # Gets: "Payment_26_328410861"
expected_comment = f"Payment_{transaction_id}_{user_id}"  # Expected: "Payment_26_328410861"

if expected_comment in message:            # ✅ Match found!
    return True
```

## Transaction Flow Verification

### Your Example Transaction Breakdown:
1. **User initiates**: 0.5 TON payment
2. **Deep link opens**: `amount=500000000` (nanoTON)
3. **User sends**: 0.5 TON with comment `Payment_26_328410861`
4. **Blockchain records**: 
   - Value: `500000000` nanoTON
   - Text Comment: `Payment_26_328410861`
   - Destination: Bot's wallet
5. **Bot verifies**:
   - ✅ Amount: 500000000 ÷ 1,000,000,000 = 0.5 TON
   - ✅ Comment: `Payment_26_328410861` matches
   - ✅ Received after payment creation time
   - ✅ Sent TO bot's wallet (incoming message)

## API Response Structure

The bot checks this data structure from TON API:
```json
{
  "ok": true,
  "result": [
    {
      "utime": 1728682162,           // Transaction timestamp
      "in_msg": {
        "value": "500000000",        // Amount in nanoTON ✅
        "message": "Payment_26_328410861",  // Comment ✅
        "source": "user_wallet_address",
        "destination": "bot_wallet_address"  // ✅
      }
    }
  ]
}
```

## Verification Success Criteria

All 4 conditions must be met:
1. **✅ Timing**: Transaction after payment creation
2. **✅ Direction**: Incoming to bot's wallet 
3. **✅ Amount**: Matches expected TON amount (±0.001 tolerance)
4. **✅ Comment**: Contains exact payment ID format

## Background Verification

- **Automatic Check**: Every 2 minutes for pending payments
- **Manual Check**: When user clicks "Check Payment Status"
- **API Limits**: 100 transactions per request
- **Timeout**: Checks transactions from last 5+ minutes

## Your Transaction Status: ✅ VERIFIED

Your example transaction would be verified because:
- ✅ **0.5 TON** sent (matches expected amount)
- ✅ **Payment_26_328410861** comment (matches format)
- ✅ **Incoming** to bot wallet (correct direction)
- ✅ **Recent** transaction (within timeframe)

The bot would automatically:
1. Mark transaction as `completed`
2. Add package credits to user account
3. Send success notification to user
4. Notify admin of successful payment