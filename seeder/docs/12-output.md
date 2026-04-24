# Chapter 12 — Output Files

[<- Back to index](./README.md)

---

## 12.1 Location

All credential output files are written to `seeder/storage/seeder_outputs/`. This directory is created automatically if it does not exist. It is gitignored.

---

## 12.2 Files

Three files are written per run, one per user category:

| File | Contents |
|---|---|
| `campus_admin_credentials.{ext}` | One row per school — the campus admin account |
| `student_governance_credentials.{ext}` | All SSG, SG, and ORG officers |
| `student_credentials.{ext}` | All regular students |

The file extension is determined by `SEED_CREDENTIALS_FORMAT`:

| Format | Delimiter | Extension |
|---|---|---|
| `csv` | `,` | `.csv` |
| `tsv` | `\t` | `.tsv` |
| `psv` | `\|` | `.psv` |

---

## 12.3 Schema

All three files share the same column schema:

| Column | Description |
|---|---|
| `School` | The school name |
| `Role` | The user's role (e.g., `Campus Admin`, `SSG Officer`, `Student`) |
| `Email` | Login email |
| `Password` | Plaintext password (before hashing) |
| `First Name` | First name |
| `Last Name` | Last name |

---

## 12.4 Usage

These files are the primary way to get login credentials after a seed run. Open the appropriate file to find accounts for testing:

- Use `campus_admin_credentials` to log in as a school administrator
- Use `student_governance_credentials` to log in as an SSG/SG/ORG officer
- Use `student_credentials` to log in as a regular student

If `SEED_UNIQUE_PASSWORDS = False` (default), all students share the password `Student123!` and you don't need the credentials file for students — just pick any student email from the database.

---

## 12.5 File Overwrite Behavior

Each run overwrites the output files from scratch. The files are opened with `'w'` mode at the start of `run_demo()`, which truncates any existing content. This means re-running the seeder always produces fresh credential files that match the current database state.
