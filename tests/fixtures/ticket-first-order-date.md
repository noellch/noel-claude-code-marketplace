# Asana task — "Customer report: first order date wrong for some customers"

Project: MAAC Issues (not the Support project)
Assignee: you
Priority: High   Product: Reports   Feature: Customer report   Org ID: 5338
Created: 2026-10-27 by Lanchi (CS)

## Description

Beauty Corp (org 5338) says the customer report's "first order date" column started showing recent dates for long-time customers. They export the report weekly. The Oct 20 export was fine; the Oct 27 export is wrong.

Example: customer c-1042 placed their first order on 2024-03-02. The report now shows 2026-10-25 for them.

## Comments

- **Lanchi, 10/27:** Attached both exports (binary, not reproduced here). Only customers with more than one order look affected; single-order customers are fine.
- **Dash, 10/28:** Nothing changed in the report config on our side. Could this be related to the order pagination release last week?
