# Calendar

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## CALENDAR-001 — CalDAV Calendar Synchronization & Account Setup

- **Domain**: `calendar`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: pending — Requires a controlled external CalDAV server.

### Purpose

Connects to remote CalDAV servers (Apple iCloud, Nextcloud, Google) to sync calendar event feeds.

### Evidence summary

- `routes/calendar_routes.py` — `setup_calendar_routes` — Exposes CalDAV setup and manual sync trigger routes.
- `src/caldav_sync.py` — `CalDavSync` — Fetches and parses remote iCalendar VEVENT objects.

### Unknowns

- Invalid SSL certificates on self-hosted CalDAV servers.

## CALENDAR-002 — Calendar Event Operations & iCalendar Parsing

- **Domain**: `calendar`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Creates, updates, deletes, and displays calendar events with timezone conversion and reminder notifications.

### Evidence summary

- `routes/calendar_routes.py` — `@router.get('/events')` — Fetches calendar events for requested date window.
- `src/tools/calendar.py` — `CalendarTool` — Agent tool for creating and modifying calendar entries.

### Unknowns

- Recurring RRULE event expansion calculation bugs across leap years.
