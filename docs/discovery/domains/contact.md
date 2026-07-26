# Contact

Features in this document are generated from [`../feature-catalog.json`](../feature-catalog.json), the canonical inventory.

## CONTACT-001 — CardDAV Contact Management & Address Book Integration

- **Domain**: `contact`
- **Status**: `verified`
- **Evidence Maturity**: `E0`
- **Commit Verified**: `d8a2059df8e53bc7275c45339849d14c8651e73c`
- **Runtime Validation**: not-required — No separate environment-dependent runtime validation was identified during this documentation pass.

### Purpose

Connects to CardDAV servers, imports VCard contacts, and provides contact lookup for email/calendar autocomplete.

### Evidence summary

- `routes/contacts/contacts_routes.py` — `@router.get('/list')` — Returns contact list filtered by search query.
- `src/tools/contacts.py` — `ContactsTool` — Agent tool for querying user address book contacts.

### Unknowns

- VCard 3.0 vs 4.0 property parsing mismatches.
