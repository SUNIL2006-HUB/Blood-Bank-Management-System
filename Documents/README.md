
# Blood Bank Management System

## Problem Statement

Blood banks rely heavily on manual or fragmented processes to track donors, blood donations, and stock availability. This makes it difficult to know how much blood of a given group is currently available, to keep donor records up to date, and to respond quickly when a hospital or patient needs blood. There is a need for a centralized system that digitizes donor registration, donation recording, inventory tracking, and blood issuance, so that blood banks can operate more accurately and efficiently.

## Project Description

The **Blood Bank Management System** is a system to manage blood donation and availability in blood banks. It allows:

- **Blood bank staff** to register donors, record blood donations, and issue blood from stock.
- **Recipients/hospitals** to view and search current blood availability by blood group.
- **Blood bank management** to generate reports on donations and availability over a selected period.

The system maintains an internal record of blood stock that is automatically updated whenever a donation is recorded or blood is issued, ensuring availability figures always reflect actual holdings.

## Documents

All project documentation is available in the `Documents` folder:

| Document | Description |
| --- | --- |
| **SRS_Document.docx** | Software Requirements Specification. Contains a single requirements table listing all Functional Requirements (FR-01 to FR-08) and Non-Functional Requirements (NFR-01 to NFR-04), each with an ID, type, description, priority, pass/fail acceptance criteria, and rationale. |
| **Test_Plan_Document.docx** | Manual test plan covering Unit (UT), Integration (IT), and System (ST) test cases for each implemented use case — Register Donor, Record Donation, View/Search Availability, Issue Blood, and Generate Reports. Each test case includes pre-conditions, steps, test data, and expected results; Actual Result and Test Result columns are left blank for execution. |
| **Use_Case_Diagram.docx** | UML use case diagram showing the three actors (Blood Bank Staff, Recipient/Hospital, Blood Bank Management) and the six use cases, including the `«include»` relationships where Record Donation and Issue Blood both trigger the internal Update Blood Availability use case. |
| **Use_Case_Flow.docx** | Detailed use case specifications (UC1–UC6) describing the goal, actor, main flow, alternate flow, and exception flow for each use case, mapped back to the functional requirements in the SRS. |

## Traceability

Every functional requirement in the SRS is covered by a corresponding use case in the Use Case Diagram/Flow, and every implemented use case has a dedicated set of test cases in the Test Plan — so the four documents are consistent with one another end to end.
