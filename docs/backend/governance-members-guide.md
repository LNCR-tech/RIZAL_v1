# Governance Members Guide

This guide documents backend behavior for creating, searching, updating, and removing governance members.

## One Active Governance Membership Per User

A student user can be an active member of only one governance unit at a time. This is enforced in the governance hierarchy service without adding new tables or migrations.

The rule applies when:

- Adding a member with `POST /api/governance/units/{governance_unit_id}/members`
- Reassigning a member's `user_id` with `PATCH /api/governance/members/{governance_member_id}`
- Searching candidates with `GET /api/governance/students/search`

Inactive historical memberships are allowed. A student can be added to a new governance unit after their previous membership is deactivated.

## Add Member Validation

When adding a member, the backend first validates the target student and unit scope, then checks whether the user already has an active membership in any other governance unit.

If an active membership exists elsewhere, the API returns:

```http
409 Conflict
```

The response detail explains that the user can only belong to one governance unit at a time and must be removed from the other unit first.

## Candidate Search Filtering

`GET /api/governance/students/search` excludes users who already have an active governance membership.

When `governance_unit_id` is provided, the search still excludes:

- active members already in the target unit
- active members in any other governance unit

This keeps already-assigned students from appearing in the add-member search results.

## How To Test

Run the focused governance member tests:

```bash
pytest backend/tests/test_governance_members.py
```

The coverage verifies that:

- adding the same active user to another governance unit returns `409`
- candidate search hides users already active in another governance unit
- updating a member to use a user active in another governance unit returns `409`
