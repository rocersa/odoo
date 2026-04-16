# Payroll Localization Feasibility Report: New Zealand vs. Australia

## Executive Summary

There is **no New Zealand payroll localization** (`l10n_nz_hr_payroll`) in Odoo 19.0. New Zealand accounting exists (`l10n_nz`, ~579 lines), and NZ bank payment files exist (`l10n_nz_eft`, ~1,015 lines), but the payroll engine and compliance reporting layer are entirely absent.

Using **Australia** as a benchmark is instructive, but it represents a **near-worst-case** scenario. The Australian localization is one of the largest and most complex in the Odoo ecosystem because of real-time government reporting (STP), multiple tax schedules, and superannuation law. A New Zealand localization would be significantly smaller than Australia's, though still non-trivial because of **payday filing** (mandatory since 2019) and the interaction of PAYE, ACC, KiwiSaver, and student loans.

---

## 1. What Currently Exists

### New Zealand
| Module | Purpose | Size |
|--------|---------|------|
| `l10n_nz` | Chart of accounts, GST tax reports, basic invoice formatting | ~579 lines |
| `l10n_nz_eft` | EFT batch payment file export for NZ banks | ~1,015 lines |
| `l10n_nz_hr_payroll` | **Does not exist** | — |

The `l10n_nz` module does contain a single payroll-related account (`21410 — Payroll Accruals Payable`), but there are no salary rules, tax tables, payslip computations, or government reporting features.

### Australia (the comparison)
| Module | Purpose | Size |
|--------|---------|------|
| `l10n_au_hr_payroll` | Core payroll engine (PAYG, Medicare, HELP, super, ETP, termination) | ~13,500 lines |
| `l10n_au_hr_payroll_account` | STP XML generation, SuperStream, ABA payments, accounting bridge | ~9,700 lines |
| `l10n_au_hr_payroll_api` | Superchoice API integration (IAP proxy), MFA, audit logging | ~3,200 lines |
| **Total AU payroll ecosystem** | | **~26,400 lines** |

For context, simpler payroll localizations such as **Lithuania** (`l10n_lt_hr_payroll`, ~1,600 lines) and **Malaysia** (`l10n_my_hr_payroll`, ~1,200 lines) are an order of magnitude smaller than Australia. NZ would likely sit between those simple localizations and Australia.

---

## 2. Anatomy of the Australian Localization (Complexity Benchmark)

### 2.1 Core Payroll (`l10n_au_hr_payroll`)
This module overrides and extends the base `hr_payroll` engine in three major ways:

1. **Tax Computation Logic** (`models/hr_payslip.py`, 1,276 lines)  
   Implements PAYG withholding across **seven different ATO schedules** (regular, seniors, actors, horticultural, WHM, PALM, voluntary agreements), Medicare levy, HELP/STSL, backpay withholding, and termination payments (ETP).

2. **Employee & Contract Extensions** (`models/hr_version.py`, 633 lines)  
   Adds ~40 AU-specific fields to the contract version object: TFN declaration status, tax treatment category, Medicare exemption, study loans, child support garnishees, salary sacrifice superannuation, casual loading, etc.

3. **Data-Driven Rules** (~30 salary rules + 1,948-line parameter file)  
   AU tax tables are stored as dated `hr.rule.parameter.value` records. The module ships with multiple fiscal-year versions of withholding coefficients, super guarantee rates (11% → 11.5% → 12%), ETP caps, and allowance limits.

4. **Superannuation**  
   Custom models for super funds (`l10n_au.super.fund`) and employee super accounts (`l10n_au.super.account`), with split proportions and fund validation.

5. **Tests**  
   12 test files (~3,800 lines) covering edge cases across all tax schedules.

### 2.2 Accounting & Compliance (`l10n_au_hr_payroll_account`)
This is the **government reporting layer**:

- **STP (Single Touch Payroll)**: An 845-line XML builder that generates ATO-compliant `PAYEVNT.0004` and `PAYEVNTEMP.0004` documents, handles corrections, full-file replacements, and year-end finalisation.
- **SuperStream**: A 540-line SAFF CSV generator and payment batch manager for super contributions.
- **ABA File Export**: Bank payment file generation for salary disbursements.
- **XSD Schemas**: ATO XML schema files (~2,400 lines) for validation.

### 2.3 API Integration (`l10n_au_hr_payroll_api`)
A ~3,200-line module that pushes STP and SuperStream data to the **Superchoice** clearing house via Odoo's IAP proxy. It includes employer registration, status polling, payment cancellation, MFA enforcement, and ATO-mandated audit logging.

---

## 3. What a New Zealand Localization Would Need

### 3.1 Core Payroll Engine (`l10n_nz_hr_payroll`)
You would need to build:

| Component | Description | Estimated Effort |
|-----------|-------------|------------------|
| **PAYE tax rules** | Progressive tax brackets (current rates: 10.5%, 17.5%, 30%, 33%, 39%). Annual thresholds change, so dated `hr.rule.parameter` records are required. | Medium |
| **ACC Earner Levy** | Flat percentage (~1.6%) on earnings up to an annual maximum. Simple salary rule + parameter. | Low |
| **KiwiSaver** | Employee deductions (3%, 4%, 6%, 8%, 10%), employer contributions (minimum 3%), and **ESCT** (tax on employer contributions at a separate progressive rate). | Medium |
| **Student Loan** | 12% deduction on earnings above the weekly/fortnightly threshold. | Low |
| **Child Support** | Deductions similar to AU; simpler than AU's multi-tier garnishee system. | Low |
| **Employee/Contract fields** | IRD number, tax code (e.g., M, ME, S, SH, ST), KiwiSaver rate, KiwiSaver status (opt-in/out, contributions holiday), student loan flag, ESCT rate. | Low |
| **Salary rules & structures** | ~15–25 rules (vs. AU's ~30+). NZ has fewer payment categories and no complex ETP rules. | Medium |
| **Termination / final pay** | Annual leave cash-up, final pay PAYE calculations. Simpler than AU ETP legislation. | Medium |
| **Tests** | Edge cases for PAYE brackets, ACC caps, KiwiSaver/ESCT combinations, student loan thresholds. | Medium |

**Realistic size estimate:** 2,500–4,500 lines of code and data.

### 3.2 Accounting & Reporting (`l10n_nz_hr_payroll_account`)
NZ does **not** have an STP equivalent, but it does have **payday filing** (mandatory since April 2019). Employers must file employment information within **2 working days of every payday**.

| Component | Description | Estimated Effort |
|-----------|-------------|------------------|
| **Payday filing report** | Generate an employment information file conforming to Inland Revenue's file-upload specification. As of 2025, IR supports file upload to myIR; the specification covers CSV/XML formatting for employee details and pay-period data (gross earnings, PAYE, KiwiSaver, ESCT, student loan, child support). | High |
| **IR345 / IR348 automation** | While payday filing replaced the old monthly IR348 for most employers, you still need to aggregate deductions and support the payment reconciliation workflow. | Medium |
| **Accounting bridge** | Map salary expenses and liabilities to the NZ chart of accounts (already has `21410 — Payroll Accruals Payable`). | Low |
| **EFT payments** | Can reuse the existing `l10n_nz_eft` module for batch salary payments; no new bank file format needed. | Low |

**Realistic size estimate:** 2,000–4,000 lines of code and report templates.

### 3.3 API Integration (Optional but Valuable)
Inland Revenue offers myIR APIs for digital service providers. An automated payday filing module would:

- Authenticate with IR's myIR API.
- Push employment information automatically per pay run.
- Handle validation errors and amendment filings.

**Realistic size estimate:** 2,000–4,000 lines (if you choose to build this).

---

## 4. Complexity Assessment

| Scenario | Effort | Comparison |
|----------|--------|------------|
| **Basic NZ payroll** (correct calculations + manual CSV download for myIR upload) | **Medium** | Comparable to Lithuania or Malaysia (~3,000–5,000 lines total). Most of the work is configuring salary rules and tax tables. |
| **Full NZ payroll** (correct calculations + automated payday filing reports + accounting bridge) | **High** | Comparable to a mid-tier European localization (~6,000–10,000 lines). The payday filing report generator is the largest single piece of work. |
| **Full NZ payroll + IR API** (automated submission to Inland Revenue) | **Very High** | Approaches the lower end of the Australian effort (~10,000–15,000 lines). You avoid AU's superannuation and ETP complexity, but you add API infrastructure. |

### Why Australia Looks So Much Bigger
Australia's localization is an outlier for three reasons that **do not** apply to NZ:

1. **Multiple tax schedules**: AU has 7+ withholding schedules for different worker categories. NZ has essentially one PAYE table.
2. **Superannuation guarantee law**: AU SG involves fund choice, contribution rate changes, and preservation ages. KiwiSaver is simpler (fixed employee rates, flat employer minimum).
3. **Real-time STP + SuperStream API**: AU built both a government XML reporter *and* a private clearing-house API integration. NZ only requires payday filing, and file-upload (non-API) is an acceptable compliance path for many employers.

---

## 5. Recommendation

### Is it worth creating an NZ localization?

**Yes, but with caveats depending on your ambition level.**

1. **If you need a "basic" localization** to calculate PAYE, ACC, KiwiSaver, and student loans correctly, and you are happy for users to **download a file and manually upload it to myIR**, the effort is **manageable** (roughly 1–2 senior Odoo developers for 2–3 months). This would fill a genuine gap in the Odoo ecosystem.

2. **If you need full automation** (direct API submission to Inland Revenue, amendment handling, and zero manual steps), the project complexity jumps significantly. You would be looking at a multi-month project with dedicated compliance expertise to interpret IR's file-upload specification and myIR API documentation.

3. **Australia is not a 1:1 proxy for NZ effort.** Use Australia to understand the *architecture* (how `hr.payslip`, `hr.salary.rule`, and `hr.rule.parameter` work together), but do not assume NZ requires 26,000 lines of code. A realistic full-featured NZ payroll localization is likely **one-third to one-half the size** of the Australian stack.

### Immediate Next Steps
If you decide to proceed, the recommended approach is:
1. Obtain the latest **Inland Revenue "Payday Filing File Upload Specification"** (available from ird.govt.nz) to scope the reporting layer accurately.
2. Start with the **core module** (`l10n_nz_hr_payroll`) focusing on PAYE, ACC, KiwiSaver, and student loan salary rules.
3. Build the **payday filing report** as a QWeb-based CSV/XML generator in a second module (`l10n_nz_hr_payroll_account`) before considering any API integration.
4. Reuse `l10n_nz_eft` for salary disbursements; no new bank file work is needed.

---

## 6. Practical Options for Our Business

**Context:** We currently run payroll in **Xero** (copying employee hours from Odoo manually), and we plan to migrate our accounting to Odoo. We have asked our Odoo account manager whether an official NZ payroll localization is planned.

### 6.1 How Odoo Prioritizes Localizations

Odoo typically builds payroll localizations where there is **large enterprise demand** or a **strategic partner** willing to co-fund the work. The countries with full payroll in Odoo 19 are mostly large markets (US, AU, BE, FR, CH, MX, IN) or markets with a dominant local partner.

**New Zealand is a small market.** Odoo already ships `l10n_nz` (accounting) and `l10n_nz_eft` (bank payments), but stopped short of payroll. That is usually a signal that payroll is **not on the near-term roadmap** unless a major partner or customer pushes it.

> **Translation:** unless the account manager comes back with a committed release quarter, do not bank on an official localization appearing in the next 12–18 months.

### 6.2 Four Realistic Paths

| Option | Payroll runs in | Effort | Best for |
|--------|----------------|--------|----------|
| **A. Keep the hybrid** | Xero | Very low | Buying time while deciding. Migrate accounting to Odoo now; keep Xero *only* for payroll. |
| **B. Thin integration** | Xero, but automated | Low–Medium | Build an Odoo module that pushes approved timesheet/attendance data to Xero via API, eliminating the manual copy-paste. |
| **C. Custom NZ payroll** | Odoo | Medium–High | Build a private `l10n_nz_hr_payroll` scoped to *our* needs only (no IR API, just CSV upload). |
| **D. Third-party payroll bridge** | External NZ SaaS (e.g. PayHero, FlexiTime, Employment Hero) | Medium | Keep payroll in a dedicated NZ SaaS, but push hours from Odoo and pull journal entries back via API. |

### 6.3 Which Option Fits?

#### If you want to cancel Xero *soon* (next 6 months)
The safest bets are **Option C** (aggressively scoped) or **Option D**.

**Option C — “Good enough” custom payroll**
- Cover only *our* pay structures, not every edge case in NZ law.
- Skip the myIR API for now. Generate a CSV matching IR’s payday filing upload spec and upload it to myIR manually each payday.
- Target: **1 senior Odoo developer for 2–3 months**.
- Deliverables: PAYE tables, ACC earner levy, KiwiSaver (employee + employer + ESCT), student loans, child support if applicable, basic payslip PDF.
- Employee self-service can leverage Odoo’s existing **Employee Self-Service** (My Odoo / Portal) for payslip access; no need to build a portal from scratch.

**Option D — NZ payroll SaaS bridge**
- Use an NZ payroll provider with an API. Keep payroll logic *outside* Odoo, but eliminate manual data entry.
- Usually faster to implement than a full payroll engine, and you retain local compliance expertise.

#### If you are happy to keep Xero for another 12–24 months
**Option A or B** is the smart play.

- **Option A** is essentially the status quo, just with accounting migrated to Odoo. Many businesses run this way indefinitely. The only cost is the monthly Xero subscription.
- **Option B** removes the manual friction. If Xero has an API endpoint for timesheets/payroll data, a small Odoo module can push approved work entries straight into Xero. This is typically a **2–4 week** project for one developer.

### 6.4 Recommended Decision Framework

1. **Wait for the account manager’s answer**, but set a deadline (e.g. 2 weeks). If they cannot give a firm release quarter, assume it is not happening soon.
2. **In the meantime, scope Option C internally.** List exact pay types, deduction types, and reporting needs. If the list is short and standard, a custom build is very doable.
3. **Do not try to build a full “productized” localization** on the first pass. Build a *private* module that solves *our* business problem. Expand or open-source it later if desired.
4. **If the custom build feels too big**, keep Xero for payroll even after migrating accounting to Odoo. The subscription cost is almost certainly cheaper than 3–6 months of senior developer time.

### 6.5 Payday Filing Reference (NZ)

- **Payday filing** is mandatory for all NZ employers since April 2019.
- Electronic filings must be submitted within **2 working days** of each payday.
- Employers can file via:
  - Payroll software with direct IR integration;
  - myIR file upload (CSV/XML); or
  - Paper (only if annual PAYE + ESCT is under $50,000).
- For more details: [ird.govt.nz/payday-filing](https://www.ird.govt.nz/employing-staff/payday-filing)
