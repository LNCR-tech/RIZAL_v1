# Frequently Asked Questions

[<- Back to doc index](../README.md)

> **Status:** ACTIVE
> **Last Updated:** 2026-04-25

---

## SSOT Note

Canonical user navigation and product overview are maintained in:
- [docs/user/overview.md](../../docs/user/overview.md)
- [docs/user/navigation.md](../../docs/user/navigation.md)

If this FAQ conflicts with those pages, follow `docs/user/*`.

---

## About Aura

**Q: What is Aura?**  
A: Aura is a school attendance platform with role-based workspaces, event attendance tracking, reporting, and assistant features.

**Q: Does each school have separate data?**  
A: Yes. Data is isolated by school context (`school_id`) across backend and assistant flows.

**Q: What services make up the platform?**  
A: Backend (FastAPI), frontend (Vue 3 + Vite), assistant service (`assistant-v2`), PostgreSQL, Redis, and Celery workers.

---

## Login and Access

**Q: I forgot my password. What should I do?**  
A: Use your organization's reset flow from the login page and coordinate with Campus Admin if needed.

**Q: Why am I forced to change password after first login?**  
A: Accounts created with temporary credentials require password change for security.

**Q: Why am I getting an inactive account or school message?**  
A: Your account or school status is disabled. Contact Campus Admin or platform administrator.

---

## Attendance

**Q: What is the difference between PRESENT and LATE?**  
A: `PRESENT` means check-in happened within on-time windows. `LATE` means check-in was after those windows.

**Q: Can I still check in when late?**  
A: Yes, while the event attendance window is open and policy allows late check-ins.

**Q: Why does face attendance fail for one user only?**  
A: Usually due to missing/low-quality face registration, camera permission issues, or poor lighting.

---

## Workspaces and Features

**Q: Where do students operate?**  
A: Student workflow is under `/dashboard`.

**Q: Where does School IT/Campus Admin operate?**  
A: School operations are under `/workspace`.

**Q: Where does Governance/SSG operate?**  
A: Governance workflows are under `/governance`.

**Q: Where is platform administration?**  
A: Admin workspace is under `/admin` (permissions required).

---

## AI Assistant

**Q: Is assistant chat available in the app?**  
A: Yes, chat routes exist per workspace (for example `/dashboard/chat`, `/workspace/chat`, `/admin/chat`, `/governance/chat`) when enabled by role and deployment settings.

**Q: Can assistant queries access other schools' data?**  
A: No. Assistant data access follows school-level isolation rules.

---

## Operations and Troubleshooting

**Q: Pages open but data is missing. What should I check first?**  
A: Check network connectivity and backend health, then retry.

**Q: Attendance appears incorrect for an event. What should be verified first?**  
A: Verify event scope, attendance window configuration, and whether capture was manual or face-based.

**Q: I need the Android install guide. Where is it?**  
A: Use [APK User Manual](./apk_manual.md).

