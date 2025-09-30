# Data Protection Strategy for BigQuery Data Clean Rooms

## Executive Summary

This document summarizes the key findings from our analysis of Google Cloud's data protection capabilities for BigQuery data clean rooms. The core recommendation is to use a **layered, integrated approach** that combines multiple technologies based on your use case.

### Two Protection Scenarios

**1. Internal Access Control (Your Team)**
- Use DLP to discover and classify sensitive data
- Apply DDM for real-time masking based on user identity
- Enable operational analytics with role-based access

**2. External Data Sharing (DCR/DCX via Analytics Hub)**
- Use DLP to discover and classify sensitive data
- Apply deterministic hashing for secure joins (not DDM)
- Use authorized views to control data exposure
- Apply analysis rules for aggregation thresholds (DCR only)
- Enable subscriber email logging for audit trails (DCR only)

### DCPA Lifecycle for Data Clean Rooms

1. **Discover:** Use Sensitive Data Protection (DLP) to automatically find sensitive data
2. **Classify:** Use DLP's extensive library to categorize data types (PII, PHI, financial data)
3. **Protect:** Use **hashing + authorized views** for external sharing (not DDM)
4. **Analyze:** Enable secure analytics through analysis rules and differential privacy

## Key Technologies Overview

### BigQuery Dynamic Data Masking (DDM)
- **Purpose:** Real-time, query-level access control **within your organization**
- **How it works:** Applies masking rules at query time based on user identity
- **Best for:** Operational analytics, BI dashboards, developer access
- **Key advantage:** No performance impact, single source of truth
- **Cost:** Bundled with BigQuery Enterprise/Enterprise Plus editions
- **Important:** DDM is for **internal access control only** - it does not apply to data shared via DCR/DCX

### BigQuery Differential Privacy
- **Purpose:** Anonymizing aggregate results for statistical analysis
- **How it works:** Adds calibrated statistical noise to aggregate queries
- **Best for:** External data sharing, research, public statistics
- **Key advantage:** Mathematical privacy guarantees
- **Limitation:** Slower query execution, requires careful configuration

### Sensitive Data Protection (DLP)
- **Purpose:** Discovery, classification, and transformation of sensitive data
- **How it works:** Scans data at rest, identifies 150+ types of sensitive information
- **Best for:** Data discovery, compliance audits, automated governance
- **Key advantage:** Comprehensive scanning and structured metadata output
- **Cost:** Pay-per-byte processed (can be expensive for large datasets)

## Protection Mechanisms: Internal vs External Sharing

### Internal Access Control (DDM)
**Use Case:** Your team accessing your organization's data

**How it works:**
- DDM policies applied to tables in your project
- Masks data based on user identity (IAM roles)
- Users query tables directly
- Real-time masking at query execution

**Example:**
```sql
-- Developer sees masked email, Analyst sees full email
SELECT email, revenue FROM customers;
-- Result depends on who runs the query
```

### External Sharing (DCR/DCX)
**Use Case:** Sharing data across organizational boundaries via Analytics Hub

**How it works:**
- **Hashing:** Transform PII before sharing (for secure joins)
- **Authorized Views:** Control what columns/rows are exposed
- **Analysis Rules:** Enforce aggregation thresholds (DCR only)
- **Subscriber Email Logging:** Audit who queries the data (DCR only)

**Key Difference:** DDM policies do NOT transfer to linked datasets. Protection happens through:
1. Pre-processing (hashing)
2. View-level access control (authorized views)
3. Query restrictions (analysis rules for DCR)

**Example:**
```sql
-- Create authorized view with hashed email (no raw PII)
CREATE VIEW shared_customers AS
SELECT
  TO_BASE64(SHA256(CONCAT(email, 'SALT'))) AS hashed_email,
  age,
  country
FROM customers;
-- This view is shared via Analytics Hub, not the raw table
```

## The Secure Join Problem in Data Clean Rooms

### The Challenge
When sharing data between organizations (merchant and e-wallet provider), you cannot join on raw PII like email addresses because:
1. It exposes sensitive information to the other party
2. It violates privacy principles of data clean rooms
3. It creates compliance and security risks

### The Solution: One-Way Deterministic Hashing

Based on the analysis, the **best practice for data clean rooms** is **one-way, key-based hashing**:

#### Why This Works
- **Deterministic:** Same input always produces same output (enables joins)
- **Irreversible:** Cannot be decrypted to reveal original PII
- **Secure:** Uses cryptographic hashing with a secret salt
- **Simple:** Can be implemented directly in BigQuery SQL

#### Implementation Method
```sql
-- Both parties apply the same transformation
TO_BASE64(SHA256(CONCAT(email, 'SHARED_SECRET_SALT'))) AS hashed_email
```

#### Alternative: Cloud KMS-Based Encryption
For enterprise scenarios, you can use:
- `DETERMINISTIC_ENCRYPT` with Cloud KMS keys
- More secure but more complex setup
- Requires careful IAM permission management

## Recommended Architecture for This Demo

### For the Data Clean Room Demo
1. **Use One-Way Hashing:** Implement SHA256 with shared salt for email join keys
2. **Remove Raw PII:** Exclude original email columns from shared views
3. **Enable Joins:** Both merchant and provider hash emails identically
4. **Preserve Analytics:** Hashed emails work perfectly for joins and ML models

### Why This is Best Practice
- **Security:** Other party cannot reverse-engineer email addresses
- **Functionality:** Joins work perfectly on hashed values
- **Simplicity:** No complex key management required
- **Realistic:** Mirrors real-world data clean room implementations

## Key Takeaways

1. **Know Your Use Case:**
   - **Internal access:** Use DLP for discovery + DDM for enforcement
   - **External sharing (DCR/DCX):** Use DLP for discovery + Hashing for secure joins + Authorized Views for access control

2. **DDM vs DCR/DCX Protection:**
   - DDM is for **internal** operational analytics (your team accessing your tables)
   - Hashing + Authorized Views + Analysis Rules are for **external** data sharing (DCR/DCX via Analytics Hub)
   - These are **complementary**, not alternatives

3. **Security First:** Never join on raw PII in data clean rooms - always use deterministic hashing

4. **Layered Approach for DCR/DCX:**
   - Layer 1: DLP discovers sensitive data
   - Layer 2: Hash PII for secure joins
   - Layer 3: Authorized views control column/row exposure
   - Layer 4: Analysis rules enforce aggregation thresholds (DCR)
   - Layer 5: Subscriber email logging for audit trails (DCR)

5. **Best Practice for This Demo:**
   - Use SHA256 hashing with shared salt for email join keys
   - Share only authorized views (never raw tables)
   - Enable subscriber email logging for DCR audit trails
   - Apply analysis rules to prevent re-identification

This approach transforms your demo from a simple data sharing example into a sophisticated, security-conscious data clean room that follows industry best practices.
