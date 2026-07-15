# Account, Data, and Migration Governance

Status: Prepared for review  
Canonical authority: Notion `28 Account, Data & Portfolio Governance v0.1` and Pulda OS Operating Model  
Target repository path: `docs/governance/ACCOUNT-DATA-MIGRATION.md`

## Purpose

This document defines the public-safe implementation rules for mapping accounts and historical assets before any migration action. It contains no real account identifiers, private filenames, customer data, contract amounts, credentials, or non-public paths.

## Account classes

- `ACT-PERSONAL`: personal, family, and historical archive boundary.
- `ACT-PULDA`: current business operating and control boundary.
- `ACT-PARISH`: parish administration, volunteer, and collaborator boundary.

The business control account may register relationships and locations without owning or automatically receiving personal or parish data.

## External service identity classes

Platform-specific identities are registered separately from the three core
Google account boundaries.

- `EXT-COMMUNICATION`: messaging, channel, and portal identity.
- `EXT-COMMERCE`: store, place, merchant, and transaction identity.
- `EXT-SITE-OWNERSHIP`: webmaster, search-console, domain, and site-verification identity.

One external identity may serve several classes. The private registry records
the real provider and login identity; public Git stores only synthetic examples
and field definitions. External identities do not replace or merge the core
account records.

## Required private registry fields

The operational registry belongs in the authorized private control plane, not public Git.

- stable account ID
- verified identity and account owner
- provider and account type
- intended use and forbidden use
- sensitivity class
- connected tools and billing responsibility
- service roles such as communication, commerce, place, or site ownership
- authentication dependency and recovery responsibility
- allowed and prohibited transfer boundaries
- verification source, date, and reviewer
- status and revision history

## Migration First

Historical assets enter Pulda through:

Discovery → AI interpretation → human correction → relationship linking → operational adoption

Discovery and interpretation do not authorize file movement or content analysis.

## Inventory boundary

The first inventory is metadata-only and limited to a human-approved account and top-level folder scope.

Allowed metadata:

- internal opaque item identifier
- item type
- parent relationship
- modified-time band
- size band or item-count estimate when available
- sharing-state category without person identifiers
- candidate asset or project category
- classification confidence and rationale

Prohibited without separate approval:

- file-content reads or extraction
- real filenames in public Git
- bulk search beyond the approved scope
- move, copy, delete, rename, or archive actions
- sharing or permission changes
- cross-account transfers
- customer, collaborator, financial, contract, or personal identifiers

## Virtual Asset Map

The private As-Is map uses:

`Account → Service or repository → approved top-level location → asset/project candidate`

Every classification proposal records its evidence class, confidence, sensitivity, and human-review state. The default migration state is `Link` or `Review`, never `Move`.

## Review Queue

Human review is mandatory for:

- ambiguous account ownership or purpose
- personal, parish, contract, subcontract, financial, or client-confidential material
- low-confidence classification
- duplicate or version uncertainty
- any proposed irreversible action
- any cross-boundary transfer

Human corrections are stored separately from AI interpretations and must be tested on the next comparable classification before becoming a reusable rule.

## Public Git boundary

Public Git may contain schemas, enumerations, procedures, safeguards, synthetic examples, acceptance criteria, and reproducible Builder instructions.

Public Git must never contain:

- real emails, account IDs, tokens, passwords, or recovery data
- real file or folder names from private storage
- customer, collaborator, or family information
- contract values, billing records, or private project economics
- private URLs, storage paths, exports, backups, inventories, or databases

Fixtures and tests use synthetic identifiers only.

## Evidence and status

- `Prepared`: document exists for review but has no verified remote commit.
- `Implemented`: remote commit and applicable automated policy checks are verified.
- `User Verified`: the user confirms the process on an approved real scope.
- `Closed`: Notion, Git, and operational evidence are reconciled.

Only the user may set `User Verified` or `Closed`.

## Succession Registry

Succession identities are separate from connected operating accounts.

Public-safe object definitions:

- `SuccessionPlan`: owner reference, lifecycle state, policy versions, and review dates.
- `SuccessorRecord`: synthetic successor ID, priority order, allowed package levels, verification state, and revocation state.
- `CheckInPolicy`: inactivity observation, user reminders, grace period, successor response window, escalation, and cancellation rules.
- `SuccessionPackage`: approved disclosure level, inclusions, exclusions, expiry, integrity evidence, and approval state.
- `TriggerCase`: observed signals, attempts, current state, next action, and audit references.

Lifecycle:

`Active → CheckInDue → GracePeriod → PrimaryNotice → SecondaryNotice if needed → LimitedAccess → separately verified transition or cancellation`

Safety requirements:

- New plans are inactive and new successors are unverified.
- Inactivity alone never proves death or incapacity and never grants unrestricted access.
- Successors use separate restricted identities.
- Access URLs and one-time codes use separate channels where possible.
- Tokens are single-use, short-lived, and revocable.
- User return immediately cancels escalation.
- Passwords, recovery codes, API keys, active sessions, financial authority, private messages, medical data, unreviewed customer material, parish personal data, and third-party confidential information are excluded from automatic disclosure.
- Real successor identity, contact data, delivery history, and verification evidence remain outside public Git.
- Runtime notification remains prohibited until threat-model, key-custody, cancellation, recovery, audit, and security acceptance criteria are approved.

## First acceptance criteria

1. The connected provider identity and accessible drive classes are verified without listing files.
2. All three account records have explicit purpose, forbidden use, sensitivity, and transfer boundaries; unknown identities remain marked unverified.
3. External service identities are related without collapsing them into a core account.
4. One account and top-level folder scope is explicitly approved before listing it.
5. The returned As-Is map and Review Queue remain private and metadata-only.
6. No file content or mutation occurs.
7. Public Git output passes a review for prohibited identifiers and private paths.

Updated: 2026-07-15
