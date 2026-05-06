# ShikshaWave: DFD and Database Documentation

This document provides a detailed overview of the Data Flow Diagrams (DFDs) and the core database schema for the ShikshaWave School Management System.

---

## 1. Data Flow Diagrams (DFD)

### 1.1 First Level DFD (Context Diagram)
The Context Diagram shows the high-level boundary of the ShikshaWave system and its interaction with external entities.

```mermaid
graph LR
    subgraph ShikshaWave["ShikshaWave School Management System"]
        SystemProcess((Core System))
    end

    Student["Student / Parent"]
    Staff["Staff / Teacher"]
    Admin["School Admin"]
    SuperAdmin["System Super Admin"]

    %% Student Flows
    Student -- "Admission Application" --> SystemProcess
    Student -- "Fee Payment" --> SystemProcess
    SystemProcess -- "Fee Receipts / Result Cards" --> Student
    SystemProcess -- "Attendance Notifications" --> Student

    %% Staff Flows
    Staff -- "Attendance / Check-in" --> SystemProcess
    Staff -- "Marks Entry" --> SystemProcess
    SystemProcess -- "Salary Slips / Schedule" --> Staff

    %% Admin Flows
    Admin -- "Configuration / Setup" --> SystemProcess
    Admin -- "Payroll Release" --> SystemProcess
    SystemProcess -- "Analytical Dashboards" --> Admin

    %% Super Admin Flows
    SuperAdmin -- "Subscription Management" --> SystemProcess
    SystemProcess -- "Platform Stats" --> SuperAdmin
```

---

### 1.2 Second Level DFD (Detailed Process Diagram)
The Level 2 DFD decomposes the system into major functional modules and identifies the data flow between them.

```mermaid
graph TD
    subgraph Core_Processes["Functional Modules"]
        P1((1.0 Auth & RBAC))
        P2((2.0 Admission & Student Mgmt))
        P3((3.0 Finance & Fee Mgmt))
        P4((4.0 HRMS & Payroll))
        P5((5.0 Academic & Exams))
        P6((6.0 Support & Communication))
    end

    DB_Master[(Master DB)]
    DB_Student[(Student DB)]
    DB_Finance[(Finance DB)]
    DB_Staff[(Staff DB)]

    %% Process 1 Flows
    P1 <--> DB_Master
    P1 -- "Authorization" --> P2
    P1 -- "Authorization" --> P3

    %% Process 2 Flows
    P2 -- "Create Profile" --> DB_Student
    P2 -- "Trigger Fees" --> P3
    P2 -- "Map Documents" --> DB_Student

    %% Process 3 Flows
    P3 -- "Record Payment" --> DB_Finance
    P3 -- "Fetch Dues" --> DB_Finance

    %% Process 4 Flows
    P4 -- "Staff Records" --> DB_Staff
    P4 -- "Salary Generation" --> DB_Finance

    %% Process 5 Flows
    P5 -- "Results / Timetable" --> DB_Student
    P5 -- "Workload Mapping" --> DB_Staff

    %% Process 6 Flows
    P6 -- "Tickets" --> DB_Master
    P6 -- "Notifications" --> DB_Student
```

---

## 2. Key Database Tables & Structure

### 2.1 Core System Entities

#### `SchoolMaster` (Multi-Tenancy Anchor)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `SchoolID` (PK) | AutoInt | Unique identifier for each school. |
| `SchoolCode` | Varchar(20) | Unique code for the school entity. |
| `SchoolName` | Varchar(100) | Full name of the school. |
| `RegistrationNumber` | Varchar(50) | Official registration number. |
| `LogoPath` / `SchoolLogo` | Text / Binary | School branding assets. |

#### `UserMaster` (Authentication & Profile)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `UserID` (PK) | AutoInt | Unique identifier for the user. |
| `UserCode` | Varchar(20) | Login username / identifier. |
| `PasswordHash` | Varchar(255) | SHA-256 hashed password. |
| `ProfileID` (FK) | Int | Link to `ProfileMaster` (Role: Admin, Teacher, etc.). |
| `SchoolID` (FK) | Int | Multi-tenant link to `SchoolMaster`. |

---

### 2.2 Student & Academic Entities

#### `StudentMaster` (Core Academic Data)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `StudentID` (PK) | AutoInt | Unique identifier for the student. |
| `AdmissionNo` | Varchar(50) | School-assigned admission number. |
| `FullName` | Varchar(100) | Student's full name. |
| `CurrentClassID` (FK)| Int | Link to `ClassMaster`. |
| `AcademicYearID` (FK)| Int | Current session tracking. |

#### `ClassMaster` & `SectionMaster`
- `ClassMaster`: `ClassID`, `ClassName`, `ClassCode`, `SchoolID`.
- `SectionMaster`: `SectionID`, `ClassID`, `SectionName`, `Capacity`.

---

### 2.3 Financial Entities

#### `FeeType_Master` (Revenue Config)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `FeeTypeId` (PK) | AutoInt | Unique ID for fee type. |
| `FeeTypeName` | Varchar(100) | e.g., Admission Fee, Tuition Fee. |
| `DefaultAmount` | Decimal | Base amount for this fee type. |

#### `Payment` (Transaction Ledger)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `PaymentID` (PK) | AutoInt | Unique transaction ID. |
| `ReceiptNo` | Varchar(50) | Formatted receipt ID (e.g., RCP-...). |
| `StudentID` (FK) | Int | Payer identification. |
| `Amount` | Decimal | Paid amount. |
| `PaymentMode` | Varchar(20) | Cash, Online, Cheque, etc. |

---

### 2.4 HRMS & Support

#### `SalaryComponentMaster`
- `ComponentID`, `ComponentName`, `ComponentType` (Earning/Deduction).

#### `TicketSystem`
- `TicketID`, `Subject`, `Priority`, `Status`, `AssignedTo`, `CreatedBy`.

---

> [!NOTE]
> All critical business logic is implemented via **Stored Procedures** (e.g., `Proc_Student_Admission_With_Documents`, `Proc_Payment_Insert`) to ensure atomic transactions and high performance across the Microsoft SQL Server backend.
