# Student Bulk Import Format

The system supports importing students via CSV or Excel (.xlsx) files. 

## Template Headers

The import system supports two formats: the current **Extended Format** (10 columns) and the **Legacy Format** (7 columns).

### Extended Format (Recommended)
The following columns must appear in this exact order:

1. **School_ID**: The numeric ID of the school. Must match the school you are importing into.
2. **Student_ID**: The unique identification number of the student (e.g., 2023-0001).
3. **Email**: The student's institutional email address.
4. **Last Name**: The student's family name.
5. **First Name**: The student's given name.
6. **Middle Name**: (Optional) The student's middle name.
7. **Department**: The exact name of the department (e.g., College of Engineering).
8. **Course**: The exact name of the program/course (e.g., BS in Computer Science).
9. **Year Level**: (Required for ACTIVE status) Numeric value 1, 2, 3, 4, or 5.
10. **Status**: (Optional) ACTIVE, GRADUATED, INACTIVE, TRANSFERRED, or ARCHIVED. Defaults to ACTIVE.

### Legacy Format
For backward compatibility, the system still accepts the 7-column format:
`Student_ID`, `Email`, `Last Name`, `First Name`, `Middle Name`, `Department`, `Course`.

*Note: Legacy imports default to Year Level 1 and Status ACTIVE.*

## Validation Rules

- **Required Fields**: Student_ID, Email, Last Name, First Name, Department, Course.
- **Year Level**: Must be 1, 2, 3, 4, or 5. Required if Status is ACTIVE.
- **Status**: Must be one of the supported uppercase values.
- **Duplicates**: The system checks for duplicate Student_ID and Email within the file and against existing database records.
- **Associations**: The Department and Course names must exist in the system and be correctly linked to each other.
