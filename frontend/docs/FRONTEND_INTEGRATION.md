# Frontend Integration Guide

## Overview

This guide explains how to integrate AjaxSecurFlow's plan-based access control into frontend applications. It covers the permission utilities, React components, API client configuration, and UI/UX patterns for restricted features.

---

## Table of Contents

1. [Permission Utilities](#permission-utilities)
2. [React Components](#react-components)
3. [API Client Configuration](#api-client-configuration)
4. [Error Handling](#error-handling)
5. [State Management](#state-management)
6. [UI/UX Patterns](#uiux-patterns)

---

## Permission Utilities

### `permissions.ts`

Location: `frontend/src/shared/utils/permissions.ts`

This utility provides functions to check feature access based on the user's subscription plan.

#### Core Function: `canAccessFeature`

```typescript
export function canAccessFeature(
  userPlan: SubscriptionPlan,
  feature: Feature
): boolean {
  const permissions: Record<SubscriptionPlan, Feature[]> = {
    free: ['list_hubs'],
    basic: ['list_hubs', 'read_devices', 'read_rooms', 'read_groups', 'read_logs'],
    pro: ['list_hubs', 'read_devices', 'read_rooms', 'read_groups', 'read_logs', 'send_commands'],
    premium: ['list_hubs', 'read_devices', 'read_rooms', 'read_groups', 'read_logs', 'send_commands', 'access_proxy']
  }
  
  return permissions[userPlan]?.includes(feature) ?? false
}
```

#### Usage Example

```typescript
import { canAccessFeature } from '@/shared/utils/permissions'

function DeviceList({ userPlan }: { userPlan: SubscriptionPlan }) {
  if (!canAccessFeature(userPlan, 'read_devices')) {
    return <UpgradePrompt feature="Devices" requiredPlan="basic" currentPlan={userPlan} />
  }
  
  return <DeviceListContent />
}
```

#### Helper Functions

```typescript
// Check if user can send commands (Pro+)
export function canSendCommands(userPlan: SubscriptionPlan): boolean {
  return canAccessFeature(userPlan, 'send_commands')
}

// Check if user can access proxy (Premium only)
export function canAccessProxy(userPlan: SubscriptionPlan): boolean {
  return canAccessFeature(userPlan, 'access_proxy')
}

// Get required plan for a feature
export function getRequiredPlan(feature: Feature): SubscriptionPlan {
  if (feature === 'list_hubs') return 'free'
  if (['read_devices', 'read_rooms', 'read_groups', 'read_logs'].includes(feature)) return 'basic'
  if (feature === 'send_commands') return 'pro'
  if (feature === 'access_proxy') return 'premium'
  return 'free'
}
```

---

## React Components

### PlanBadge Component

Location: `frontend/src/shared/components/PlanBadge.tsx`

Visual indicator for subscription plans.

#### Props

```typescript
interface PlanBadgeProps {
  plan: SubscriptionPlan
  size?: 'sm' | 'md' | 'lg'
  className?: string
}
```

#### Usage

```typescript
import { PlanBadge } from '@/shared/components/PlanBadge'

function UserProfile({ user }: { user: User }) {
  return (
    <div>
      <h2>{user.email}</h2>
      <PlanBadge plan={user.subscription_plan} size="md" />
    </div>
  )
}
```

#### Styling

The component automatically applies plan-specific colors:
- **Free**: Gray (`bg-gray-500/10 text-gray-400`)
- **Basic**: Blue (`bg-blue-500/10 text-blue-400`)
- **Pro**: Purple (`bg-purple-500/10 text-purple-400`)
- **Premium**: Gold (`bg-amber-500/10 text-amber-400`)

---

### UpgradePrompt Component

Location: `frontend/src/shared/components/UpgradePrompt.tsx`

Overlay component for locked features with upgrade call-to-action.

#### Props

```typescript
interface UpgradePromptProps {
  feature: string              // Feature name (e.g., "Devices", "Commands")
  requiredPlan: SubscriptionPlan  // Minimum required plan
  currentPlan: SubscriptionPlan   // User's current plan
  className?: string
}
```

#### Usage

```typescript
import { UpgradePrompt } from '@/shared/components/UpgradePrompt'

function DeviceTelemetry({ userPlan }: { userPlan: SubscriptionPlan }) {
  if (!canAccessFeature(userPlan, 'read_devices')) {
    return (
      <div className="relative min-h-[400px]">
        <UpgradePrompt
          feature="Device Telemetry"
          requiredPlan="basic"
          currentPlan={userPlan}
        />
      </div>
    )
  }
  
  return <TelemetryTable />
}
```

#### Features

- **Gradient background** with blur effect
- **Lock icon** visual indicator
- **Plan comparison** showing what's included
- **Upgrade button** linking to `/billing`
- **Responsive design** for mobile/desktop

---

## API Client Configuration

### `api-client.ts`

Location: `frontend/src/infrastructure/api-client.ts`

Centralized API client with automatic token management and error handling.

#### Configuration

```typescript
import axios, { AxiosInstance } from 'axios'

const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor: Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: Handle errors
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export { apiClient }
```

#### Usage

```typescript
import { apiClient } from '@/infrastructure/api-client'

// GET request
const hubs = await apiClient.get('/api/v1/ajax/hubs')

// POST request
const result = await apiClient.post('/api/v1/ajax/hubs/00022777/arm-state', {
  armState: 1
})
```

---

## Error Handling

### Handling 403 Forbidden Errors

When a user tries to access a feature their plan doesn't include, the API returns 403 Forbidden.

#### Pattern 1: Try-Catch with User Feedback

```typescript
async function loadDevices(hubId: string) {
  try {
    const devices = await apiClient.get(`/api/v1/ajax/hubs/${hubId}/devices`)
    setDevices(devices)
  } catch (error) {
    if (error.response?.status === 403) {
      // Show upgrade prompt
      setShowUpgradeModal(true)
      setUpgradeMessage(error.response.data.detail)
    } else {
      // Handle other errors
      console.error('Failed to load devices:', error)
    }
  }
}
```

#### Pattern 2: Preemptive Check (Recommended)

```typescript
function DeviceList({ userPlan, hubId }: Props) {
  // Check permission BEFORE making API call
  if (!canAccessFeature(userPlan, 'read_devices')) {
    return <UpgradePrompt feature="Devices" requiredPlan="basic" currentPlan={userPlan} />
  }
  
  // Only fetch if user has access
  const { data: devices } = useDevices(hubId)
  return <DeviceTable devices={devices} />
}
```

### Error Toast Notifications

```typescript
import { toast } from 'react-hot-toast'

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 403) {
      toast.error(
        `${error.response.data.detail}. Upgrade to access this feature.`,
        {
          duration: 5000,
          action: {
            label: 'Upgrade',
            onClick: () => router.push('/billing')
          }
        }
      )
    }
    return Promise.reject(error)
  }
)
```

---

## State Management

### User Subscription State

#### Using React Context

```typescript
// contexts/SubscriptionContext.tsx
import { createContext, useContext, useState, useEffect } from 'react'

interface SubscriptionContextType {
  plan: SubscriptionPlan
  status: SubscriptionStatus
  expiresAt: string | null
  isLoading: boolean
  refreshSubscription: () => Promise<void>
}

const SubscriptionContext = createContext<SubscriptionContextType | null>(null)

export function SubscriptionProvider({ children }: { children: React.ReactNode }) {
  const [subscription, setSubscription] = useState<SubscriptionContextType>({
    plan: 'free',
    status: 'inactive',
    expiresAt: null,
    isLoading: true,
    refreshSubscription: async () => {}
  })
  
  useEffect(() => {
    fetchSubscription()
  }, [])
  
  async function fetchSubscription() {
    try {
      const user = await apiClient.get('/api/v1/auth/me')
      setSubscription({
        plan: user.subscription_plan,
        status: user.subscription_status,
        expiresAt: user.subscription_expires_at,
        isLoading: false,
        refreshSubscription: fetchSubscription
      })
    } catch (error) {
      console.error('Failed to fetch subscription:', error)
      setSubscription(prev => ({ ...prev, isLoading: false }))
    }
  }
  
  return (
    <SubscriptionContext.Provider value={subscription}>
      {children}
    </SubscriptionContext.Provider>
  )
}

export function useSubscription() {
  const context = useContext(SubscriptionContext)
  if (!context) {
    throw new Error('useSubscription must be used within SubscriptionProvider')
  }
  return context
}
```

#### Usage

```typescript
function Dashboard() {
  const { plan, status, isLoading } = useSubscription()
  
  if (isLoading) return <LoadingSpinner />
  
  return (
    <div>
      <h1>Dashboard</h1>
      <PlanBadge plan={plan} />
      {canAccessFeature(plan, 'read_devices') ? (
        <DeviceList />
      ) : (
        <UpgradePrompt feature="Devices" requiredPlan="basic" currentPlan={plan} />
      )}
    </div>
  )
}
```

### Refreshing Subscription After Upgrade

```typescript
function BillingPage() {
  const { refreshSubscription } = useSubscription()
  
  async function handleVoucherRedeem(code: string) {
    try {
      await apiClient.post('/api/v1/billing/redeem', { code })
      
      // Refresh subscription state
      await refreshSubscription()
      
      toast.success('Voucher redeemed successfully!')
      router.push('/dashboard')
    } catch (error) {
      toast.error('Failed to redeem voucher')
    }
  }
  
  return <VoucherForm onSubmit={handleVoucherRedeem} />
}
```

---

## UI/UX Patterns

### Pattern 1: Disabled Buttons with Tooltips

For features requiring higher plans, show disabled buttons with upgrade tooltips.

```typescript
import { Tooltip } from '@/shared/components/Tooltip'

function ArmButton({ userPlan, hubId }: Props) {
  const canArm = canAccessFeature(userPlan, 'send_commands')
  
  return (
    <Tooltip
      content={canArm ? '' : 'Upgrade to Pro to send commands'}
      disabled={canArm}
    >
      <button
        disabled={!canArm}
        onClick={() => armSystem(hubId)}
        className={`
          px-4 py-2 rounded-lg font-bold
          ${canArm 
            ? 'bg-blue-500 hover:bg-blue-600 text-white cursor-pointer' 
            : 'bg-gray-500/20 text-gray-600 cursor-not-allowed'
          }
        `}
      >
        🛡️ Arm System
        {!canArm && <span className="ml-2 text-xs">(Pro)</span>}
      </button>
    </Tooltip>
  )
}
```

### Pattern 2: Blurred Content with Overlay

Show a preview of locked content with a blur effect and upgrade prompt.

```typescript
function DeviceTelemetry({ userPlan }: Props) {
  const hasAccess = canAccessFeature(userPlan, 'read_devices')
  
  return (
    <div className="relative">
      {/* Content (blurred if no access) */}
      <div className={hasAccess ? '' : 'filter blur-sm pointer-events-none'}>
        <TelemetryChart />
      </div>
      
      {/* Overlay if no access */}
      {!hasAccess && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <UpgradePrompt
            feature="Device Telemetry"
            requiredPlan="basic"
            currentPlan={userPlan}
          />
        </div>
      )}
    </div>
  )
}
```

### Pattern 3: Progressive Disclosure

Show basic info to all users, detailed info only to subscribers.

```typescript
function HubCard({ hub, userPlan }: Props) {
  const canViewDetails = canAccessFeature(userPlan, 'read_devices')
  
  return (
    <div className="border rounded-lg p-4">
      {/* Basic info (Free+) */}
      <h3>{hub.name}</h3>
      <p>Status: {hub.status}</p>
      
      {/* Detailed info (Basic+) */}
      {canViewDetails ? (
        <>
          <p>Devices: {hub.deviceCount}</p>
          <p>Battery: {hub.batteryLevel}%</p>
          <p>Signal: {hub.signalStrength}</p>
        </>
      ) : (
        <div className="mt-4 p-3 bg-blue-500/10 rounded border border-blue-500/20">
          <p className="text-xs text-blue-400">
            📊 Upgrade to Basic to see device details
          </p>
        </div>
      )}
    </div>
  )
}
```

### Pattern 4: Plan Comparison Table

Help users understand what they're missing.

```typescript
function PlanComparison({ currentPlan }: Props) {
  const features = [
    { name: 'Hub Listing', free: true, basic: true, pro: true, premium: true },
    { name: 'Device Details', free: false, basic: true, pro: true, premium: true },
    { name: 'Event Logs', free: false, basic: true, pro: true, premium: true },
    { name: 'Send Commands', free: false, basic: false, pro: true, premium: true },
    { name: 'API Proxy', free: false, basic: false, pro: false, premium: true },
  ]
  
  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>Feature</th>
          <th>Free</th>
          <th>Basic</th>
          <th>Pro</th>
          <th>Premium</th>
        </tr>
      </thead>
      <tbody>
        {features.map(feature => (
          <tr key={feature.name}>
            <td>{feature.name}</td>
            <td>{feature.free ? '✅' : '❌'}</td>
            <td>{feature.basic ? '✅' : '❌'}</td>
            <td>{feature.pro ? '✅' : '❌'}</td>
            <td>{feature.premium ? '✅' : '❌'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

---

## Complete Example: Dashboard Integration

```typescript
// DashboardComponent.tsx
import { useState, useEffect } from 'react'
import { useSubscription } from '@/contexts/SubscriptionContext'
import { canAccessFeature } from '@/shared/utils/permissions'
import { UpgradePrompt } from '@/shared/components/UpgradePrompt'
import { PlanBadge } from '@/shared/components/PlanBadge'

export function DashboardComponent() {
  const { plan, isLoading } = useSubscription()
  const [selectedHub, setSelectedHub] = useState<Hub | null>(null)
  
  if (isLoading) return <LoadingSpinner />
  
  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Left: Hub List (Free+) */}
      <div className="col-span-4">
        <HubList onSelectHub={setSelectedHub} />
      </div>
      
      {/* Center: Device Telemetry (Basic+) */}
      <div className="col-span-4">
        {selectedHub && (
          canAccessFeature(plan, 'read_devices') ? (
            <DeviceTelemetry hubId={selectedHub.id} />
          ) : (
            <UpgradePrompt
              feature="Device Telemetry"
              requiredPlan="basic"
              currentPlan={plan}
            />
          )
        )}
      </div>
      
      {/* Right: Event Feed (Basic+) */}
      <div className="col-span-4">
        {selectedHub && (
          canAccessFeature(plan, 'read_logs') ? (
            <EventFeed hubId={selectedHub.id} />
          ) : (
            <UpgradePrompt
              feature="Event Logs"
              requiredPlan="basic"
              currentPlan={plan}
            />
          )
        )}
      </div>
      
      {/* Bottom: Control Panel (Pro+) */}
      <div className="col-span-12">
        {selectedHub && (
          canAccessFeature(plan, 'send_commands') ? (
            <ControlPanel hubId={selectedHub.id} />
          ) : (
            <div className="p-6 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <p className="text-purple-400 font-bold">
                🎮 Upgrade to Pro to control your system remotely
              </p>
            </div>
          )
        )}
      </div>
    </div>
  )
}
```

---

## Related Documentation

- [API Permissions](../../backend/docs/API_PERMISSIONS.md) - Backend permission matrix
- [Integration Examples](../../backend/docs/INTEGRATION_EXAMPLES.md) - API usage examples
- [Plan Migration Guide](../../backend/docs/PLAN_MIGRATION_GUIDE.md) - Subscription management
