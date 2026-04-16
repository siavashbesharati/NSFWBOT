# TON Testnet Setup Guide for Users

## 🧪 How to Test TON Payments on Testnet (Sandbox)

### Step 1: Get a Testnet Wallet

#### Option A: Tonkeeper (Recommended)
1. **Install Tonkeeper**: Download from App Store/Google Play
2. **Enable Developer Mode**:
   - Open Tonkeeper
   - Go to Settings ⚙️
   - Scroll down and tap "Advanced"
   - Enable "Developer Mode"
3. **Switch to Testnet**:
   - Go back to main screen
   - Tap the network indicator at top
   - Select "Testnet" 🧪
4. **Get Testnet Address**:
   - Your wallet now shows testnet address
   - Copy this address for bot configuration

#### Option B: TON Wallet (Browser Extension)
1. **Install TON Wallet**: Add extension to Chrome/Firefox
2. **Create Testnet Wallet**:
   - Open extension
   - Click settings
   - Switch to "Testnet"
   - Create new wallet

### Step 2: Get Free Test TON

#### Method 1: TON Testnet Faucet
1. **Visit**: https://testnet.tonscan.org/faucet
2. **Enter Address**: Paste your testnet wallet address
3. **Request TON**: Get 5-10 free test TON
4. **Wait**: Usually takes 1-2 minutes

#### Method 2: Telegram Faucet Bot
1. **Message**: @testgiver_ton_bot on Telegram
2. **Send Address**: Send your testnet wallet address
3. **Receive TON**: Bot sends test TON automatically

#### Method 3: Developer Faucet
1. **Visit**: https://faucet.tonwhales.com/
2. **Connect Wallet**: Connect your testnet wallet
3. **Claim TON**: Get free test tokens

### Step 3: Configure Bot for Testing

#### Admin Dashboard Configuration:
```
Bot Configuration:
✅ Bot Active
❌ Simulation Mode (Sandbox Payments)    <- IMPORTANT: Uncheck this!

Payment Configuration:
✅ Enable TON Payments
✅ TON Testnet Mode (Sandbox)             <- IMPORTANT: Check this!
TON Wallet Address: [Your testnet address]
```

### Step 4: Test Payment Flow

#### As a User:
1. **Start Bot**: Send `/start` to your bot
2. **Check Packages**: Send `/packages`
3. **Select Package**: Choose any package with TON payment
4. **Click TON Payment**: Select "💎 Pay with TON"
5. **See Instructions**: Bot shows testnet payment instructions
6. **Payment URL**: Click "Open in Tonkeeper" link
7. **Confirm Payment**: Approve transaction in wallet
8. **Wait for Verification**: Bot checks blockchain and awards credits

### Step 5: What You'll See

#### Bot Payment Message (Testnet):
```
💎 TON Payment Instructions 🧪 TESTNET

📦 Package: Premium Package
💰 Amount: 0.5 TON
🏦 Address: EQD_your_testnet_wallet_address
💬 Comment: Payment_123

📱 Quick Payment:
[Open in Tonkeeper](tonkeeper://transfer/...)

⏰ Your payment will be verified automatically within a few minutes.

🧪 Note: This is TESTNET - you will receive test TON only!
```

#### Tonkeeper Payment Screen:
- Shows testnet network indicator 🧪
- Amount in test TON (not real value)
- Your testnet wallet address as recipient
- Payment comment for verification

### Step 6: Verification Process

#### What Happens:
1. **User Sends Payment**: Via Tonkeeper/wallet
2. **Transaction on Blockchain**: Real testnet transaction
3. **Bot Monitors**: Checks testnet blockchain every 5 minutes
4. **Verification**: Matches amount and comment
5. **Credits Added**: User receives message credits
6. **Confirmation**: Bot sends success message

#### Success Message:
```
✅ Payment successful! Your credits have been added to your account.

Use /dashboard to check your updated balance.
```

## 🔍 Testing Checklist

### Before Testing:
- [ ] Testnet wallet set up and funded
- [ ] Bot configured for testnet mode
- [ ] Simulation mode disabled
- [ ] Testnet wallet address in bot settings

### During Testing:
- [ ] Payment instructions show "🧪 TESTNET"
- [ ] Tonkeeper shows testnet network
- [ ] Transaction uses test TON (no real value)
- [ ] Payment comment matches transaction ID

### After Testing:
- [ ] Payment verified within 5-10 minutes
- [ ] Credits added to user account
- [ ] Transaction shows as completed in admin dashboard
- [ ] No real money was spent

## 🚨 Important Notes

### Safety Features:
- **No Real Money**: Testnet uses worthless test tokens
- **Real Blockchain**: Tests actual payment verification
- **Network Warnings**: Clear testnet indicators everywhere
- **Reversible**: Can switch back to simulation mode anytime

### Common Issues:
1. **Payment Not Verified**: Check testnet wallet address in settings
2. **No Test TON**: Use faucet to get more test tokens
3. **Wrong Network**: Ensure wallet is on testnet mode
4. **API Errors**: Check if TON API is accessible

### Troubleshooting:
```bash
# Check bot logs for verification attempts
# Verify testnet transaction on: https://testnet.tonscan.org
# Ensure wallet address format is correct
# Wait up to 10 minutes for verification
```

## 🎓 Educational Value

This testnet testing teaches:
- **Real Payment Flow**: Exactly like production
- **Blockchain Interaction**: Real transaction verification
- **User Experience**: Complete payment journey
- **Error Handling**: What happens when payments fail
- **Timing**: How long verification takes

Perfect for understanding the complete payment system before going live! 🚀