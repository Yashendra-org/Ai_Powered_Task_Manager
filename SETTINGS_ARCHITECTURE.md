# Enterprise Settings Architecture & UI Specification (SETTINGS_ARCHITECTURE.md)

**Document Version:** 1.0  
**Author:** Yashendra Kumar (Lead Architect)  
**Target Platform:** My Habit Tracker Enterprise Edition  

---

## Executive Summary

This specification outlines the end-to-end design for the **Enterprise Settings & Workspace Hub**, structured into two primary left-hand navigation modules:
1. **Personal Settings**: Identity, Notifications, Accessibility/Power-User Controls, and Session Security.
2. **Workspace & Organization Settings**: Subscription & Metered Billing, Team RBAC, Developer APIs & Webhooks, and Compliance Audit Logs.

---

## 1. Clean UI Microcopy & Form Labels

### 1.1 Billing, Subscription & Usage Meters
| UI Element | Label (Header / Title) | Placeholder / State | Helper Copy / Contextual Microcopy |
| :--- | :--- | :--- | :--- |
| **Plan Overview Card** | `Subscription Tier` | `Pro Plan (Annual)` | "Billed annually at ₹799/month. Next auto-renewal scheduled for December 26, 2026." |
| **Tier Action CTA** | `Upgrade to Enterprise` | Button | "Unlock unlimited team seats, SAML 2.0 SSO, and custom domain routing." |
| **Storage Meter** | `Coursework & Media Storage` | `4.2 GB of 10 GB used` | "Includes homework PDFs, code problem archives, and note attachments. 5.8 GB free." |
| **Seat Allocation Meter**| `Active Team Seats` | `8 of 10 seats assigned` | "80% of workspace seat capacity allocated. 2 seats remaining before tier limit." |
| **API Quota Meter** | `Monthly API Invocations` | `48,200 of 100,000 calls` | "Sliding monthly quota. Resets automatically on the 1st of next month." |
| **Primary Payment Method**| `Default Payment Method` | `Visa ending in 4242` | "Expires 08/2028. Primary card charged for monthly subscription renewals and add-ons." |
| **Add Payment Card** | `Add Credit or Debit Card` | Modal CTA | "All payment details are tokenized securely with PCI-DSS Level 1 compliance." |
| **Tax Identification** | `Company Tax ID (GSTIN / VAT / EIN)`| `e.g. 07AAAAA0000A1Z5` | "Rendered automatically on all downloadable tax invoices and monthly receipts." |
| **Billing Notification** | `Billing Notification Email` | `finance@college.edu` | "Monthly receipts and payment failure notices are delivered to this address." |

### 1.2 Team & Workspace Management (Multi-User RBAC)
| UI Element | Label (Header / Title) | Placeholder / State | Helper Copy / Contextual Microcopy |
| :--- | :--- | :--- | :--- |
| **Custom Subdomain** | `Workspace Subdomain` | `collegelabs` | "Accessible at `https://collegelabs.myhabittracker.com`. Max 32 alphanumeric characters." |
| **Brand Accent Color** | `Brand Primary Color` | Color Swatch (`#2563EB`) | "Customizes the primary button and navigation highlights for all workspace members." |
| **Workspace Logo** | `Organization Logo` | Drag & Drop Dropzone | "Recommended 256×256px SVG or PNG. Appears in navigation headers and invite emails." |
| **Member Directory** | `Workspace Members` | Search by name or email | "Manage team privileges, invited collaborator statuses, and seat assignments." |
| **Role Selector** | `Access Role` | Dropdown | `Owner`: Full billing & deletion control; `Admin`: Member & API management; `Editor`: Create/complete tasks; `Viewer`: Read-only. |
| **Bulk Email Invite** | `Invite Colleagues by Email` | `peer@college.edu, team@lab.org` | "Enter one or multiple comma-separated email addresses to dispatch invitations." |
| **Shareable Invite Link**| `Shareable Join Link` | `https://app.myhabittracker.com/join/w-8f92z` | "Anyone with a verified domain email can join. Links expire after 7 days by default." |

### 1.3 Enterprise Security & Compliance
| UI Element | Label (Header / Title) | Placeholder / State | Helper Copy / Contextual Microcopy |
| :--- | :--- | :--- | :--- |
| **SAML / OAuth SSO** | `Enterprise Single Sign-On (SSO)`| Provider Cards | "Enforce organization-wide identity authentication via Google Workspace, Microsoft Entra ID, or Okta." |
| **Corporate IP Allowlist**| `Corporate CIDR IP Allowlist` | `192.168.1.0/24, 203.0.113.50` | "Restrict login access exclusively to corporate VPNs or static campus IP ranges. Leave empty to allow any network." |
| **Audit Ledger** | `Real-Time Audit Ledger` | Searchable History Table | "Immutable log of security-sensitive events including credential changes, exports, and permission updates." |
| **Active Sessions** | `Active Device Sessions` | Browser & Device Table | "Review all currently authenticated web and mobile sessions. Select 'Revoke' to terminate stale logins." |

### 1.4 Developer & Data Controls
| UI Element | Label (Header / Title) | Placeholder / State | Helper Copy / Contextual Microcopy |
| :--- | :--- | :--- | :--- |
| **API Keys** | `Personal Access Tokens` | Masked Token (`mht_live_...`) | "API keys grant full programmatic access to your tasks and analytics. Keep them secret." |
| **Generate API Key** | `Create New Secret Key` | Name Input | "Set an expiration timestamp (30 days, 90 days, or Never) to reduce credential exposure." |
| **Webhook Endpoint** | `Webhook Delivery URL` | `https://api.mycollege.edu/events` | "We will send an HTTP POST JSON payload whenever selected workspace events trigger." |
| **Webhook Test** | `Test Webhook Trigger` | Button | "Dispatches a simulated `ping` event to verify HTTP 200 OK receipt and response latency." |
| **Workspace Export** | `Full Backup Download` | Export JSON / CSV | "Download a complete machine-readable archive containing tasks, habits, notes, and audit logs." |
| **Retention Policy** | `Ephemeral Data Retention` | Dropdown | "Automatically purge items in Recently Deleted trash and ephemeral event logs after 30, 90, or 365 days." |

### 1.5 Accessibility & Power-User Preferences
| UI Element | Label (Header / Title) | Placeholder / State | Helper Copy / Contextual Microcopy |
| :--- | :--- | :--- | :--- |
| **Keyboard Shortcuts** | `Enable Global Keyboard Hotkeys`| Toggle Switch | "Navigate rapidly across views using single-key shortcuts (`N` for new task, `T` for My Day, `/` to search)." |
| **High Contrast Mode** | `High Contrast Display Mode` | Toggle Switch | "Enhance border definition and color contrast ratios for improved accessibility (WCAG AAA)." |
| **Reduced Motion** | `Reduced Motion (Minimal Animations)`| Toggle Switch | "Disables checkmark celebratory pop animations, floating zooms, and modal transitions." |
| **Default Landing View** | `Default Landing View Upon Sign-In`| Dropdown Selector | "Choose whether authentication redirects to Executive Dashboard, My Day, All Tasks, or Analytics." |

---

## 2. JSON Schema & Database Architecture

### 2.1 Complete User & Workspace Preferences JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EnterpriseUserSettings",
  "type": "object",
  "required": ["profile", "notifications", "accessibility", "workspace"],
  "properties": {
    "profile": {
      "type": "object",
      "required": ["first_name", "last_name", "email", "timezone"],
      "properties": {
        "first_name": { "type": "string", "maxLength": 150 },
        "last_name": { "type": "string", "maxLength": 150 },
        "email": { "type": "string", "format": "email" },
        "timezone": { "type": "string", "default": "Asia/Kolkata" },
        "week_start_day": { "type": "string", "enum": ["monday", "sunday"], "default": "monday" }
      }
    },
    "notifications": {
      "type": "object",
      "required": ["email_notifications", "sound_effects", "morning_briefing_time", "daily_review_time"],
      "properties": {
        "email_notifications": { "type": "boolean", "default": true },
        "sound_effects": { "type": "boolean", "default": true },
        "morning_briefing_time": { "type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$", "default": "08:00" },
        "daily_review_time": { "type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$", "default": "21:30" }
      }
    },
    "accessibility": {
      "type": "object",
      "required": ["keyboard_shortcuts", "high_contrast", "reduced_motion", "default_landing_view"],
      "properties": {
        "keyboard_shortcuts": { "type": "boolean", "default": true },
        "high_contrast": { "type": "boolean", "default": false },
        "reduced_motion": { "type": "boolean", "default": false },
        "default_landing_view": {
          "type": "string",
          "enum": ["dashboard", "my_day", "all_tasks", "analytics"],
          "default": "dashboard"
        }
      }
    },
    "workspace": {
      "type": "object",
      "properties": {
        "workspace_id": { "type": "string", "format": "uuid" },
        "name": { "type": "string", "maxLength": 100 },
        "subdomain": { "type": "string", "pattern": "^[a-z0-9-]+$", "maxLength": 32 },
        "brand_color": { "type": "string", "pattern": "^#[0-9a-fA-F]{6}$", "default": "#2563EB" },
        "ip_allowlist": {
          "type": "array",
          "items": { "type": "string" }
        },
        "data_retention_days": { "type": "integer", "enum": [30, 90, 180, 365], "default": 30 }
      }
    }
  }
}
```

### 2.2 Relational Database Schema (Django ORM Models)

```python
import uuid
from django.db import models
from django.conf import settings

class Workspace(models.Model):
    """Multi-tenant enterprise workspace."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    subdomain = models.SlugField(max_length=32, unique=True)
    logo = models.ImageField(upload_to='workspaces/logos/', null=True, blank=True)
    brand_color = models.CharField(max_length=7, default='#2563EB')
    ip_allowlist = models.TextField(blank=True, help_text="Comma-separated CIDR blocks")
    trash_retention_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

class WorkspaceMember(models.Model):
    """Team membership and RBAC permissions."""
    ROLE_CHOICES = [
        ('owner', 'Workspace Owner'),
        ('admin', 'Workspace Admin'),
        ('editor', 'Editor / Collaborator'),
        ('viewer', 'Read-Only Viewer'),
    ]
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='editor')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')

class SubscriptionPlan(models.Model):
    """SaaS subscription tiers and resource quotas."""
    name = models.CharField(max_length=50)  # Free, Pro, Enterprise
    slug = models.SlugField(unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    storage_limit_bytes = models.BigIntegerField(default=10 * 1024 * 1024 * 1024)  # 10 GB
    max_team_seats = models.PositiveIntegerField(default=10)
    monthly_api_limit = models.PositiveIntegerField(default=100000)

class WorkspaceSubscription(models.Model):
    """Active subscription status and usage meters."""
    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default='active')  # active, past_due, canceled
    current_period_end = models.DateTimeField()
    storage_used_bytes = models.BigIntegerField(default=0)
    monthly_api_calls_used = models.PositiveIntegerField(default=0)
    company_tax_id = models.CharField(max_length=64, blank=True)
    billing_email = models.EmailField(blank=True)

class ApiKey(models.Model):
    """Developer personal access tokens."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='api_keys')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    key_prefix = models.CharField(max_length=8)  # e.g. "mht_live"
    hashed_secret = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

class AuditLog(models.Model):
    """Searchable security and compliance event ledger."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)  # e.g. "task.export_csv", "member.invite"
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
```

---

## 3. Wireframe Layout Architecture (HTML & Tailwind CSS)

The full interactive layout has been implemented in **[templates/accounts/settings.html](templates/accounts/settings.html)** featuring:
- **Left Sticky Sidebar (`col-span-3`)**: Grouped into Personal Settings (Profile, Notifications, Accessibility, Security) and Workspace Settings (Billing, Team RBAC, Developer, Audit Logs).
- **Tab Switching Engine (`switchSettingsTab`)**: Pure client-side zero-reload routing preserving browser URL hash state (`#billing`, `#team`, `#accessibility`, etc.).
- **Live Visual Components**:
  - Subscription Plan Cards & Tailwind Resource Usage Bars (`Storage: 4.2 / 10 GB`, `Seats: 8 / 10`).
  - Searchable Member Directory with RBAC dropdowns and invite link generator.
  - Downloadable invoice PDF receipts table.
  - Developer API key management and webhook testing console.
  - Interactive Keyboard Shortcut Cheat Sheet modal (`shortcutModal`).
