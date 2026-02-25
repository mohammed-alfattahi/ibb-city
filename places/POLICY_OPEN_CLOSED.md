# Establishment Open/Closed Status Policy

## Overview
Partners can manually control the "Open/Closed" status of their establishments in real-time. This status is displayed to tourists on the public establishment page as a badge (e.g., "Open Now" or "Closed Now").

## Ownership Rules
1. **Owner Authority**: Only the **approved owner** of an establishment can toggle its status.
2. **Co-Owners/Managers**: Currently, strict ownership is enforced (`establishment.owner == user`).
3. **Admin/Superuser**: Administrators have override capability to toggle status for moderation purposes.
4. **Tourists**: Have **read-only** access to the status.

## Toggle Behavior
- **Immediate Effect**: Changes are reflected instantly on the public page without requiring Tourism Office approval.
- **Audit Logging**: Every status change is recorded in the system `AuditLog` with:
  - Timestamp
  - Actor (User who changed it)
  - Previous Status vs. New Status
  - IP Address
- **Notifications**:
  - The Tourism Office is notified immediately of any status change (`OPEN_STATUS_CHANGED` event) to monitor activity.

## Working Hours vs. Manual Status
- **Manual Override**: The manual toggle (`is_open_now`) takes precedence over scheduled working hours for the "Status Badge".
- **Working Hours**: Partners should simply set their typical working hours for informational purposes, but use the Manual Toggle for ad-hoc closures (e.g., emergencies, holidays) or extending hours.

## Usage
- **Partner Dashboard**: Click the "Power" icon on the establishment card.
- **Public Page**: Click the "Change Status" button on the floating status card (visible only to logged-in owner).
