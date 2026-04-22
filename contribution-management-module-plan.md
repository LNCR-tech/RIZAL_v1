# Contribution Management Module — Aura System
**Version 1.0 | Module Design Specification**

---

## 1. Purpose

The Contribution Management Module enables governance units — **SSG**, **SG**, and **ORG** — to create and manage event-linked financial contributions. It is designed to handle money, student records, sanctions, and receipts, which makes correctness and auditability non-negotiable requirements alongside standard feature delivery.

This document covers: scope, roles and permissions, data model, payment workflows, exemptions, sanctions, receipts, reporting, notifications, security, and a phased delivery plan.

---

## 2. Core Design Principle

Contribution is treated as a **separate financial object** linked to an event — not a field inside the event record. This keeps financial data cleanly separated from event logistics and makes the contribution lifecycle independently manageable.

Each event may have **zero or one active contribution setup**. A contribution has its own amount, due date, visibility rules, exemption policy, sanctions configuration, delegation settings, payment records, and receipts.

---

## 3. Contribution Types

| Type | Description | Examples |
|------|-------------|---------|
| **None** | Event exists; no payment required | Seminar, orientation, general meeting |
| **Optional** | Students may contribute; no sanction if unpaid | Donation drive, shirt fund, outreach support |
| **Mandatory** | Payment required unless exempted; overdue triggers sanction workflow | Departmental fee, membership contribution, approved activity fee |

---

## 4. Roles and Permissions

### Campus Admin
Oversight and reconciliation only. Can view collection status, totals by department and program, exemption and sanction statistics, and export filtered reports. **Cannot** collect payments or alter contributions created by governance units.

### SSG
Full authority over campus-wide contributions. Can create events with any contribution type, view all payment statuses, delegate collection to SG, define exemptions, set due dates and sanction policies, manage collection windows, and export campus-wide or filtered reports.

### SG
Authority limited to their assigned department. Can create department-scoped contributions, view paid/unpaid students within their department, collect for their own contributions, collect for SSG contributions **only if SSG explicitly grants permission**, manage department-level exemptions, and export department-scoped reports. Cannot access other departments' data.

### ORG
Authority limited to their assigned program. Can create contributions for program members, collect for their own contributions, collect for SG contributions **only if SG explicitly grants permission**, and export program-scoped reports. Cannot access students outside their program.

### Student
Read-only access to their own data. Can view contribution details (event name, amount, due date, status, exemption status, sanction risk), payment history, downloadable PDF receipts, and overdue reminders. Cannot see collector identity beyond what is relevant or any internal admin data.

---

## 5. Delegated Collection

A contribution creator may authorize subordinate roles to collect payments on their behalf. Delegation must be **explicit, revocable, scope-limited, and time-bounded**.

| Creator | May delegate to |
|---------|----------------|
| SSG | SG (specified department, specified date range) |
| SG | ORG (specified program, specified date range) |
| ORG | No delegation allowed |

**Example:** SSG allows SG College of Engineering to collect only for Engineering students from April 20–30, 2026.

Delegation grants must be stored and checked server-side on every collection action. Revocation takes immediate effect.

---

## 6. Payment Status Model

A richer status model is required to support partial payments, exemptions, and sanctions without ambiguity.

| Status | Meaning |
|--------|---------|
| `NOT_REQUIRED` | Contribution type is None or Optional and student has not paid |
| `OPTIONAL_UNPAID` | Optional contribution; no sanction risk |
| `PENDING` | Mandatory contribution assigned; awaiting payment |
| `PARTIALLY_PAID` | Some amount received; balance outstanding |
| `PAID` | Fully settled |
| `OVERDUE` | Past due date; not yet in sanction grace period |
| `EXEMPT_FULL` | Approved full exemption; no payment required |
| `EXEMPT_PARTIAL` | Approved partial exemption; reduced balance due |
| `SANCTION_PENDING` | Grace period expired; sanction under review |
| `SANCTION_APPLIED` | Sanction formally recorded against student |
| `REFUNDED` | Payment reversed |
| `VOIDED` | Record administratively voided with reason |

---

## 7. Payment Collection

### Collection Modes

**On-site Manual Collection** — Collector records payment in real time.
Required fields: amount received, date/time, payment method, collector identity, remarks.

**Proof-Based / Pending Verification** — Student submits proof; governance verifies before payment is confirmed.
Required fields: reference number, file attachment, submission timestamp, verified-by, verification status.

### Accepted Payment Methods
Cash · GCash · Maya · Bank transfer · School cashier · Other approved channel

Each payment record stores the method used. Every finalized payment record is **immutable** — corrections are handled through void or refund entries, never direct edits.

---

## 8. Exemptions

Exemptions apply only to contribution obligations, not to event attendance.

**Valid exemption categories:**
- Officer duty compensation
- Volunteered labor or service in lieu of payment
- Scholarship-based waiver
- Approved financial hardship
- Reward or incentive granted by governance
- Replacement of monetary contribution with an approved task

**Each exemption record must capture:**

| Field | Description |
|-------|-------------|
| `student_id` | Exempted student |
| `contribution_id` | Contribution this applies to |
| `type` | Full or Partial |
| `amount_reduced` | Exact peso value waived |
| `reason` | Descriptive justification |
| `approved_by` | Governance officer who approved |
| `approved_at` | Approval timestamp |
| `supporting_note` | Optional document reference |

An exempted student must never trigger automatic sanction. The system must check exemption status before any sanction action — automated or manual.

---

## 9. Sanctions Workflow

### Lifecycle

```
Contribution created
→ Students assigned obligation
→ Reminder sent N days before due date
→ [Due date passes]
→ Status → OVERDUE
→ [Grace period expires]
→ Status → SANCTION_PENDING
→ Review (manual by default; auto if policy explicitly permits)
→ Status → SANCTION_APPLIED
```

### Per-Contribution Sanction Configuration

| Setting | Options |
|---------|---------|
| Sanctions enabled | Yes / No |
| Grace period | N days after due date |
| Sanction type | Clearance hold, enrollment flag, etc. |
| Sanction description | Shown to student |
| Application mode | Manual review (default) / Auto-apply |
| Appeal allowed | Yes / No |

**Required safeguards before any sanction runs:**
- Exempted students must be excluded
- Partially paid students must be checked against remaining balance
- Grace period must have elapsed
- Appeal window must be respected

Auto-sanction is only appropriate when your institutional policy explicitly authorizes it. **Manual review is the recommended default.**

---

## 10. Receipt System

Every recorded payment generates a permanent receipt stored in the database. PDFs are generated from canonical data and are reproducible on demand — do not generate a receipt only at email time.

### Receipt Contents

- School branding and receipt number (format: `AURA-2026-ENG-000124`)
- Payment date and time
- Student name, ID, department, program
- Event name and contribution title
- Amount paid, payment method
- Remaining balance (if partial)
- Exemption adjustment (if applicable)
- Collector name and role
- System verification code / scannable QR
- Disclaimer: *System-generated receipt*

### Delivery
- Emailed to student automatically upon payment confirmation
- Stored and accessible from student dashboard
- Re-downloadable at any time
- Admin can resend (rate-limited)

---

## 11. Reports

### Report Types

| Report | Audience | Contents |
|--------|----------|----------|
| **Summary** | Admin / SSG | Expected total, collected, unpaid, exempted, partially paid, collection rate, sanction count |
| **Student-Level** | SSG / SG / ORG | Per-student: amount due, paid, balance, exemption status, last payment date |
| **Collector Performance** | SSG / SG | Payments received per collector, total collected, method breakdown |
| **Aging** | Admin / SSG | Current, due soon, overdue, sanction pending, sanctioned |
| **Exemption** | SSG / SG | Exempted students, type, approver, total value exempted |

### Export Scope by Role

| Role | Exportable Scope |
|------|-----------------|
| Campus Admin | Any filter: department, program, event, governance level |
| SSG | Campus-wide or filtered by department/program |
| SG | Their department only |
| ORG | Their program only |

### Export Formats
- **CSV / Excel** — for administrative work and reconciliation
- **PDF** — for presentations and official submissions

---

## 12. Notifications

### Student Notifications
Contribution created · Due date approaching · Payment recorded · Receipt ready · Exemption approved · Contribution overdue · Sanction pending · Sanction applied

### Governance Notifications
Collection rate below target · Overdue count rising · Payment proof awaiting verification · Sanction batch about to run

All notifications are delivered via **in-app** and **email**. Reminders should be configurable per contribution.

---

## 13. Database Schema

### Core Tables

**`event_contributions`** — One per event, stores the contribution configuration.
`id, event_id, title, description, contribution_type, amount, mandatory_flag, due_date, grace_period_days, sanction_enabled, sanction_mode, created_by, governance_scope_type, governance_scope_id, status`

**`contribution_assignments`** — Obligation per student.
`id, contribution_id, student_id, assigned_amount, adjusted_amount, outstanding_balance, status`

**`contribution_payments`** — Individual payment transactions.
`id, contribution_id, student_id, collector_id, amount_paid, payment_method, reference_number, verified_status, paid_at, receipt_number, remarks`

**`contribution_exemptions`** — Approved exemption records.
`id, contribution_id, student_id, exemption_type, amount_reduced, description, approved_by, approved_at`

**`contribution_delegations`** — Collection authority grants.
`id, contribution_id, granted_role, granted_scope_id, allowed_program_id, valid_from, valid_until, granted_by, active`

**`contribution_sanctions`** — Sanction lifecycle.
`id, contribution_id, student_id, status, created_at, applied_at, reason, reviewed_by`

**`payment_receipts`** — Receipt metadata.
`id, payment_id, receipt_number, storage_key, emailed_at, viewed_at, verification_code`

**`contribution_audit_logs`** — Immutable event log for all sensitive actions.
`actor, role, action, target_type, target_id, old_value, new_value, ip, timestamp`

---

## 14. Security Requirements

Because this module handles money, student identity, sanctions, and official receipts, it requires stronger controls than standard CRUD.

### Access Control
Every request must pass three checks in sequence: **role check → scope check (campus/department/program) → delegation check → action permission**. Frontend filtering is never sufficient; all checks run on the backend.

### Audit Logging
Every sensitive action must be logged with full context: contribution created/modified, amount or due date changed, delegation granted or revoked, exemption added/edited/removed, payment recorded/voided/refunded, sanction created/applied/removed, receipt regenerated or resent.

### Payment Integrity
- Payment ledger entries are immutable after finalization
- Corrections are made via void or refund records, never direct edits
- Receipt numbers and reference numbers must be unique
- Collector identity and timestamp are always stored

### Approval Requirements (Maker-Checker)
The following actions require a second approver:
- Editing contribution amount after payments have been recorded
- Bulk exemption grants
- Mass sanction application
- Payment void or refund
- Due date change after notices have been sent

### Anti-Abuse Controls
- Rate limits on receipt resend and payment verification actions
- Duplicate payment detection
- File type validation and virus scanning for uploaded proof documents
- Suspicious activity flags for anomalous collection patterns

### Data Protection
- Money operations remain in the main backend; do not route through the assistant boundary
- Student financial data exposure is minimized in exports
- Receipt PDFs are served via signed URLs or authenticated download endpoints
- Sensitive storage paths are not exposed in API responses

---

## 15. Trust and Credibility Features

### Official Receipt Numbering
Format: `AURA-{YEAR}-{SCOPE}-{SEQUENCE}` (e.g., `AURA-2026-ENG-000124`)

### Receipt Verification
Each receipt carries a system-generated verification code. A public verification page allows anyone to confirm a receipt's authenticity by entering the code.

### Reconciliation Dashboard
Side-by-side view of expected vs. received vs. exempted vs. overdue vs. sanctioned amounts per contribution. Supports handover confirmation when cash is transferred from collectors to treasurers.

### Maker-Checker Workflow
High-risk actions (voids, refunds, bulk exemptions) require one user to initiate and a second to approve. This applies at SSG and SG levels.

### Student Transparency
Students see, in plain language: what the payment is for, whether it is required, why they are exempted (if applicable), and why a sanction was applied (if applicable). Transparency reduces disputes.

---

## 16. UX Guidelines

### Contribution Creation Wizard (Governance)
Step 1: Select event → Step 2: Choose contribution type → Step 3: Set amount and due date → Step 4: Select covered students → Step 5: Configure delegation → Step 6: Add exemptions → Step 7: Configure sanctions → Step 8: Review and publish

### Governance Dashboard Widgets
Live counters: Total Expected · Collected Today · Unpaid · Overdue · Exempted · Sanction Pending

### Student Dashboard Cards
Per contribution card showing: Event name · Amount · Due date · Status badge · Outstanding balance · Receipt download button · Payment history button

---

## 17. Pre-Development Policy Decisions

Before implementation begins, the following must be formally decided by governance and documented as business rules:

1. Are mandatory contributions authorized under institutional policy?
2. Which roles may impose sanctions, and under what conditions?
3. Can students formally appeal a sanction? What is the process?
4. Does a partial payment prevent sanction, or only full payment?
5. Can receipts be voided after issuance? By whom?
6. Who may edit a contribution after payments have been collected?
7. Is delegation permanent or time-bounded by default?
8. Can a single student have multiple obligations for the same event?

Leaving these ambiguous at design time will produce inconsistent implementation and disputes at runtime.

---

## 18. Development Phases

### Phase 1 — Core MVP
Contribution-linked event creation · Optional/mandatory setting · Student assignment · Manual payment recording · Student dashboard status · PDF receipt generation · Email receipt delivery · Basic summary reports

### Phase 2 — Governance Controls
Exemptions · SG/ORG delegation · Scoped export · Overdue tracking · Advanced report filters

### Phase 3 — Compliance and Hardening
Sanctions workflow · Audit logs · Maker-checker approvals · Duplicate detection · Reconciliation dashboard · Receipt verification page

### Phase 4 — Advanced Operations
Proof upload and verification · Partial payments · Refund and void handling · Collection analytics · Automated reminder engine

---

## 19. Summary Statement

The Contribution Management Module allows SSG, SG, and ORG units to create event-linked contributions that are optional or mandatory, assign them to students within their authorized scope, record and verify payments, manage exemptions, generate and email PDF receipts, and run overdue and sanction workflows based on approved institutional policy. Access to data and actions follows a strict governance hierarchy with scope-based permissions. Campus Admin and higher governance roles can monitor totals, export reports, and review the audit trail. Students receive transparent payment history, receipt access, exemption visibility, and sanction status within their dashboard — reducing confusion and disputes at every level.
