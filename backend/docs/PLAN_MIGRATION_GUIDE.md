# Plan Migration Guide

## Overview

This guide explains how to migrate between AjaxSecurFlow subscription plans, including upgrades, downgrades, voucher redemption, and trial conversions.

## Quick Reference

| Migration Type         | Takes Effect          | Billing Impact       | Feature Access                          |
| ---------------------- | --------------------- | -------------------- | --------------------------------------- |
| **Upgrade**            | Immediately           | Prorated charge      | Instant access to new features          |
| **Downgrade**          | End of billing period | No refund            | Keep current features until period ends |
| **Voucher Redemption** | Immediately           | Extends subscription | Based on voucher plan                   |
| **Trial to Paid**      | Immediately           | Full charge          | No interruption                         |
| **Trial Expiration**   | At trial end          | No charge            | Downgrade to Free                       |

---

## Upgrade Scenarios

### Upgrading from Free to Basic

**What Changes:**
- ✅ Access to devices, rooms, and groups
- ✅ Event logs and telemetry data
- ✅ Real-time monitoring

**Billing:**
- Charged according to the standard Basic rate
- First charge is immediate
- Subsequent charges on the same day each month

**Process:**
1. Navigate to `/billing` in the dashboard
2. Click "Subscribe" on the Basic plan card
3. Complete Stripe checkout
4. Access granted immediately upon successful payment

**API Impact:**
```bash
# Before upgrade (Free)
GET /api/v1/ajax/hubs/{hub_id}/devices
# Response: 403 {"detail": "Device access not included in your plan"}

# After upgrade (Basic)
GET /api/v1/ajax/hubs/{hub_id}/devices
# Response: 200 [{"id": "device1", "name": "Motion Detector", ...}]
```

---

### Upgrading from Basic to Pro

**What Changes:**
- ✅ All Basic features
- ✅ Send commands (arm/disarm)
- ✅ Remote system control

**Billing:**
- Prorated credit for unused Basic time
- Charged the difference between the two plan tiers
- Example: Upgrade 15 days into Basic billing cycle
  - Basic unused credit is applied
  - Pro charge: Immediate charge for the calculated difference
  - Next full charge: Standard Pro rate on renewal date

**Process:**
1. Go to `/billing`
2. Click "Subscribe" on Pro plan
3. Stripe calculates prorated amount
4. Confirm payment
5. Command access enabled immediately

**API Impact:**
```bash
# Before upgrade (Basic)
POST /api/v1/ajax/hubs/{hub_id}/arm-state
# Response: 403 {"detail": "Command execution not included in your plan"}

# After upgrade (Pro)
POST /api/v1/ajax/hubs/{hub_id}/arm-state
# Response: 200 {"success": true, "armState": 1}
```

---

### Upgrading from Pro to Premium

**What Changes:**
- ✅ All Pro features
- ✅ Full Ajax API proxy access
- ✅ Custom integrations

**Billing:**
- Prorated credit for unused Pro time
- Charged the difference between the two plan tiers
- Same prorating logic as Basic → Pro

**Process:**
1. Navigate to `/billing`
2. Select Premium plan
3. Confirm prorated charge
4. Proxy access enabled immediately

**API Impact:**
```bash
# Before upgrade (Pro)
GET /api/v1/ajax/custom-endpoint
# Response: 403 {"detail": "PREMIUM subscription required to access Proxy API"}

# After upgrade (Premium)
GET /api/v1/ajax/custom-endpoint
# Response: 200 {...} (full Ajax API access)
```

---

## Downgrade Scenarios

### Downgrading from Premium to Pro

**What Changes:**
- ❌ Lose proxy API access
- ✅ Keep all Pro features (commands, monitoring, devices)

**Billing:**
- No immediate refund
- Premium access continues until current period ends
- Pro billing starts at next renewal date
- Saves the difference in tier pricing going forward

**Process:**
1. Go to `/billing`
2. Click "Manage Subscription" → Opens Stripe portal
3. Select "Update plan" → Choose Pro
4. Confirm downgrade
5. See confirmation: "Your plan will change to Pro on [renewal date]"

**Timeline Example:**
```
Today (Feb 1): Request downgrade to Pro
Current period ends: Feb 28
Feb 1-28: Still have Premium access
Feb 28: Automatically downgrade to Pro
Mar 1: First Pro billing (Standard rate)
```

**API Impact:**
```bash
# Feb 1-28 (still Premium)
GET /api/v1/ajax/custom-endpoint
# Response: 200 {...}

# Mar 1+ (now Pro)
GET /api/v1/ajax/custom-endpoint
# Response: 403 {"detail": "PREMIUM subscription required to access Proxy API"}
```

---

### Downgrading from Pro to Basic

**What Changes:**
- ❌ Lose command execution (arm/disarm)
- ✅ Keep monitoring, devices, logs

**Billing:**
- No refund for unused Pro time
- Pro access until period ends
- Basic billing starts at renewal
- Saves the tier price difference

**Process:**
Same as Premium → Pro downgrade via Stripe portal

---

### Downgrading from Basic to Free

**What Changes:**
- ❌ Lose device details
- ❌ Lose event logs
- ❌ Lose telemetry
- ✅ Keep hub listing

**Billing:**
- No refund
- Basic access until period ends
- No charges after downgrade
- Can re-subscribe anytime

**Process:**
1. Stripe portal → Cancel subscription
2. Confirm cancellation
3. Basic access until period ends
4. Auto-downgrade to Free

---

## Voucher Redemption

### How Vouchers Work

Vouchers extend your subscription by a fixed duration (typically 30 days) and can upgrade your plan.

**Voucher Types:**
- **Basic Voucher**: 30 days of Basic plan
- **Pro Voucher**: 30 days of Pro plan  
- **Premium Voucher**: 30 days of Premium plan

### Redeeming a Voucher

**Process:**
1. Go to `/billing`
2. Find "Redeem Voucher" section
3. Enter voucher code (e.g., `AJAX-TEST-BASIC-2026`)
4. Click "Redeem and Apply"
5. Confirmation message appears
6. Plan updated immediately

**Voucher Code Format:**
```
AJAX-[PLAN]-[IDENTIFIER]
Example: AJAX-TEST-PRO-2026
```

### Voucher Scenarios

#### Scenario 1: Free User Redeems Basic Voucher

```
Before: Free plan
Action: Redeem AJAX-TEST-BASIC-2026
After: Basic plan for 30 days
Expires: 30 days from redemption
```

**API Impact:**
```bash
# Before redemption
GET /api/v1/ajax/hubs/{hub_id}/devices
# Response: 403

# After redemption
GET /api/v1/ajax/hubs/{hub_id}/devices
# Response: 200 [...]
```

#### Scenario 2: Basic User Redeems Pro Voucher

```
Before: Basic plan (paid, renews monthly)
Action: Redeem AJAX-TEST-PRO-2026
After: Pro plan for 30 days
Billing: Paid Basic subscription paused
Expires: 30 days from redemption
Then: Returns to paid Basic subscription
```

**Important:** Voucher takes precedence over paid subscription during voucher period.

#### Scenario 3: Pro User Redeems Basic Voucher

```
Before: Pro plan (paid)
Action: Redeem AJAX-TEST-BASIC-2026
Result: ERROR - Cannot downgrade via voucher
```

**Rule:** Vouchers cannot downgrade an active paid subscription. Cancel paid subscription first, then redeem lower-tier voucher.

---

## Trial Period

### New User Trial

**Benefits:**
- 🎁 14-day Premium trial
- ✅ Full access to all features
- 💳 No credit card required to start
- 🔄 Auto-downgrade to Free if no payment added

**Timeline:**
```
Day 0: Sign up → Premium trial starts
Day 1-13: Full Premium access
Day 14: Trial expires
  - If payment method added: Convert to paid Premium
  - If no payment: Downgrade to Free
```

### Converting Trial to Paid

**Process:**
1. During trial, go to `/billing`
2. Click "Subscribe" on any plan
3. Add payment method via Stripe
4. Trial converts to paid subscription
5. First charge on trial expiration date

**Example:**
```
Feb 1: Start trial (14 days Premium)
Feb 10: Add payment, select Pro plan
Feb 15: Trial ends, Pro subscription starts (Standard rate charged)
```

---

## Billing Cycle Impact

### Understanding Billing Cycles

**Monthly Subscriptions:**
- Charged on the same day each month
- Example: Subscribe on Feb 5 → Renews Mar 5, Apr 5, etc.

- Charged once per year
- Discounted rate for annual commitment
- Example: Annual Basic vs Monthly Basic total

### Mid-Cycle Changes

**Upgrades:**
- Prorated immediately
- New billing cycle starts on original renewal date
- Example:
  ```
  Basic subscription: Renews 15th of each month
  Upgrade to Pro on 5th: Pay prorated difference
  Next full Pro charge: 15th (original renewal date)
  ```

**Downgrades:**
- Take effect at end of current cycle
- No prorating
- Example:
  ```
  Premium subscription: Renews 20th
  Downgrade to Basic on 5th
  Premium access until 20th
  Basic billing starts 20th
  ```

---

## API Access Changes During Migration

### Immediate Changes (Upgrades & Vouchers)

When you upgrade or redeem a voucher, API access changes **immediately**:

```bash
# Check current plan
GET /api/v1/auth/me
Response: {
  "email": "user@example.com",
  "subscription_plan": "basic",
  "subscription_status": "active"
}

# Upgrade to Pro (via UI or voucher)

# Immediate API access
GET /api/v1/auth/me
Response: {
  "email": "user@example.com",
  "subscription_plan": "pro",  # Updated
  "subscription_status": "active"
}

POST /api/v1/ajax/hubs/{hub_id}/arm-state
# Now works (was 403 before)
```

### Delayed Changes (Downgrades)

Downgrades take effect at period end:

```bash
# Feb 1: Request downgrade from Pro to Basic
GET /api/v1/auth/me
Response: {
  "subscription_plan": "pro",  # Still Pro
  "subscription_status": "active",
  "subscription_expires_at": "2026-02-28T23:59:59Z"
}

# Feb 1-28: Pro access continues
POST /api/v1/ajax/hubs/{hub_id}/arm-state
# Still works

# Mar 1: Downgrade takes effect
GET /api/v1/auth/me
Response: {
  "subscription_plan": "basic",  # Now Basic
  "subscription_status": "active"
}

POST /api/v1/ajax/hubs/{hub_id}/arm-state
# Now returns 403
```

---

## Data Retention Policies

### Plan-Specific Data Retention

| Plan        | Event Logs      | Telemetry History | API Access Logs |
| ----------- | --------------- | ----------------- | --------------- |
| **Free**    | N/A (no access) | N/A               | 7 days          |
| **Basic**   | 30 days         | 30 days           | 30 days         |
| **Pro**     | 90 days         | 90 days           | 90 days         |
| **Premium** | 365 days        | 365 days          | 365 days        |

### What Happens When You Downgrade

**Example: Premium → Basic**

```
Before downgrade (Premium):
- Event logs: 365 days of history
- Telemetry: 365 days of data

After downgrade (Basic):
- Event logs: Only last 30 days accessible
- Telemetry: Only last 30 days accessible
- Older data: Archived (not deleted), restored if you upgrade again
```

**Data Recovery:**
- Data is **archived**, not deleted
- Re-upgrade within 90 days: Full history restored
- After 90 days: Archived data permanently deleted

---

## Troubleshooting

### Common Issues

#### Issue: "Voucher code invalid"

**Causes:**
- Typo in code
- Voucher already redeemed
- Voucher expired

**Solution:**
```bash
# Check voucher status (admin only)
GET /api/v1/billing/vouchers/{code}
Response: {
  "code": "AJAX-TEST-BASIC-2026",
  "is_redeemed": true,  # Already used
  "plan": "basic"
}
```

#### Issue: "Cannot redeem voucher - higher plan active"

**Cause:** Trying to redeem lower-tier voucher while on higher paid plan

**Solution:**
1. Cancel current subscription via Stripe portal
2. Wait for period to end
3. Redeem voucher

#### Issue: "Upgrade not taking effect"

**Causes:**
- Payment failed
- Browser cache
- API token not refreshed

**Solutions:**
1. Check Stripe payment status
2. Clear browser cache / hard refresh (Ctrl+Shift+R)
3. Re-login to get fresh API token
```bash
# Get new token
POST /api/v1/auth/token
{
  "username": "your-email@example.com",
  "password": "your-password"
}
```

#### Issue: "Downgrade happened immediately instead of at period end"

**Cause:** Cancelled subscription instead of downgrading

**Difference:**
- **Cancel**: Immediate loss of access
- **Downgrade**: Access until period ends

**Solution:**
- Contact support to restore access
- Re-subscribe if needed

---

## Support

For migration issues:
- 📧 Email: support@ajaxsecurflow.com
- 📱 Support Portal: `/support`
- 💬 Live Chat: Available for Pro+ users

## Related Documentation

- [API Permissions](./API_PERMISSIONS.md) - Feature access by plan
- [Integration Examples](./INTEGRATION_EXAMPLES.md) - Code examples per tier
- [Billing API Reference](../app/modules/billing/router.py) - Programmatic plan management
