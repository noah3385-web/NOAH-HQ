# Outlook Operating System — CURRENT

**Last updated:** 2026-08-24
**Scope:** Outlook only. This file records the *current* operating architecture and
validated capability surface. Dated handoffs and prior evidence are preserved separately
and are not edited by this file.

---

## Live-work architecture

```
Inbox  →  Categories + Flags  →  Favorites / Search Folders
```

Inbox is the single live-work destination. Folder-based routing for active work is
retired. No dated or replacement working folder exists, and none is to be created.

## Operator / transport roles

| Role | System |
|---|---|
| Primary Outlook operator | Claude Code |
| Primary write transport | Zapier Microsoft Outlook connection (`Noah.Rosen@myccmortgage.com`) |
| Read + independent verification | Microsoft 365 / Graph |

Every production write is performed on one path and verified on the other.

## Capability state

| Capability | State | Basis |
|---|---|---|
| Set Categories on an Email | **VALIDATED** | Production writes + Graph readback |
| Move Email to Folder | **VALIDATED** | Production writes + Graph readback (relocate, not copy; attachments and `internetMessageId` preserved) |
| Flag / Unflag Email | **UNVALIDATED** | First-class Zapier action exists but has never been exercised. Not to be run as a test — only on a message that genuinely warrants a flag |
| Existing Inbox-rule management | **UNSUPPORTED** on the current path | Not available through Claude Code + Zapier first-class actions, and no read-only Graph rules surface is exposed. Handle in the Outlook UI manually |
| Folder deletion | **UNVALIDATED / OUT OF SCOPE** | Never attempted; not authorized |

### Category rules
- Use only the existing Outlook master category list. Never create a substitute or new category.
- `Set Categories on an Email` **replaces** the full category set. Always read existing
  categories first, compute `EXISTING ∪ AUTHORIZED`, and pass the full union.
- Never pass `isRead` on a category call — it would alter read state as a side effect.

### Prohibited
- Raw / generic mutating API actions (including Zapier's `Make API Mutating Request`).
- The blocked `Microsoft_365` MCP write path.
- Any permission-bypass mode.
- Todoist, Airtable, Copilot.

---

## Routing cutover

The four primary obsolete-routing rules — **Loan Alerts**, **Blend / Encompass**,
**CCM News**, and **CrossCountry Mortgage** — were **manually disabled by Noah** and
**visually verified by ChatGPT**. The cutover is complete.

Observed confirmation in the data: the Loan Alerts folder stopped receiving at
`2026-08-24T20:55Z`, and the Inbox began receiving the same alert class directly from
`21:08Z`.

Protected and not to be altered: Phase 1 category-only rules, Promotions, RingCentral,
Archive / BoomTown routing, Search Folders, Favorites.

---

## Legacy folder classification

| Folder | Classification | Treatment |
|---|---|---|
| Operations | RETIRE CANDIDATE — rescue complete | Obsolete as a working surface |
| Shireen Shackelford | RETIRE CANDIDATE | Blend borrower-portal automation only |
| Notifications | RETIRE CANDIDATE | dotloop / Workday / marketing |
| Loan Alerts | RETIRE CANDIDATE — **historical body preserved** | ~3,833 items. Retired as a working surface; the archive stays intact |
| CCM News | RETIRE CANDIDATE | Corporate newsletters and bulletins |
| PIPELINE 7 RECORDS, ROI REPORTING | TRUE RECORDS | Preserve; do not touch |
| Archive | COLD LEGACY | Leave; never bulk-process |

**RETIRE CANDIDATE means only:** active work has been rescued and the folder is obsolete
as a working surface. It does **not** authorize deletion.

**No mass historical migration is planned.** No bulk read-state changes, no wholesale
moves, no message-by-message historical audit.
