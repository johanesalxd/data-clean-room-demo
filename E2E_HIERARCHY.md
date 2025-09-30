# BigQuery Data Sharing Hierarchy - Presentation Slides

This document contains presentation-ready slides for explaining BigQuery's data sharing hierarchy. Each slide focuses on a specific layer with clear connections to previous and next layers.

---

## Slide 1: Real-World Example - E-Commerce Partnership

**Title:** Use Case: Merchant & Payment Provider Collaboration

```mermaid
graph TB
    Step1["LAYER&nbsp;1:&nbsp;DATA&nbsp;LAYER<br/>Merchant:&nbsp;customer&nbsp;emails,&nbsp;orders<br/>Provider:&nbsp;transaction&nbsp;data,&nbsp;account&nbsp;tiers"]
    Step2["LAYER&nbsp;2:&nbsp;PROTECTION<br/>Both&nbsp;parties&nbsp;hash&nbsp;customer&nbsp;emails<br/>SHA256&nbsp;with&nbsp;shared&nbsp;salt<br/>Remove&nbsp;raw&nbsp;email&nbsp;addresses"]
    Step3["LAYER&nbsp;3:&nbsp;ACCESS&nbsp;CONTROL<br/>Merchant:&nbsp;Authorized&nbsp;view&nbsp;on&nbsp;demographics<br/>Provider:&nbsp;Authorized&nbsp;view&nbsp;on&nbsp;transactions<br/>Hide&nbsp;sensitive&nbsp;PII&nbsp;columns"]
    Step4["LAYER&nbsp;4:&nbsp;DATASET<br/>merchant_data&nbsp;dataset<br/>provider_data&nbsp;dataset<br/>Separate&nbsp;GCP&nbsp;projects"]
    Step5["LAYER&nbsp;5:&nbsp;SHARING<br/>DCR:&nbsp;Customer&nbsp;segmentation&nbsp;analysis<br/>DCX:&nbsp;Account&nbsp;tier&nbsp;prediction&nbsp;model"]
    Step6["LAYER&nbsp;6:&nbsp;ANALYSIS<br/>DCR:&nbsp;AVG&nbsp;spend&nbsp;by&nbsp;account&nbsp;tier<br/>DCX:&nbsp;BQML&nbsp;logistic&nbsp;regression&nbsp;model"]

    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4
    Step4 --> Step5
    Step5 --> Step6

    style Step1 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Step2 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Step3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Step4 fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Step5 fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style Step6 fill:#e0f2f1,stroke:#00796b,stroke-width:2px
```

**Real-World Scenario:**

**Business Goal:** E-commerce merchant and payment provider want to collaborate on customer insights without exposing raw PII.

**DCR Roles:**
- Data Clean Room Owner: Creates and manages the DCR environment
- Data Contributors: Merchant and Provider publish their protected datasets
- Subscribers: Both parties subscribe to analyze the combined data

**Implementation:**
1. **Data Layer:** Merchant has customer demographics and purchase history. Provider has payment transactions and account tier information.
2. **Protection:** Both hash customer email addresses using SHA256 with a shared secret salt, enabling secure joins.
3. **Access Control:** Each party creates authorized views exposing only necessary columns, hiding raw PII.
4. **Dataset:** Data remains in separate GCP projects (merchant_data and provider_data) for security.
5. **Sharing:** Use DCR for privacy-preserving customer segmentation. Use DCX for collaborative ML model training. Enable subscriber email logging for audit trails.
6. **Analysis:**
   - DCR query: Calculate average spend by account tier with 50+ user threshold
   - DCX query: Train BQML model to predict which customers will upgrade to premium accounts

**Result:** Both parties gain valuable insights while protecting customer privacy and maintaining data sovereignty.

---

## Slide 2: Overview - The Complete Hierarchy

**Title:** BigQuery Data Sharing: From Columns to Clean Rooms

```mermaid
graph TB
    Layer1["LAYER&nbsp;1:&nbsp;DATA&nbsp;LAYER<br/>Column&nbsp;→&nbsp;Table&nbsp;→&nbsp;View"]
    Layer2["LAYER&nbsp;2:&nbsp;PROTECTION&nbsp;MECHANISMS<br/>DLP&nbsp;•&nbsp;Hashing&nbsp;•&nbsp;DDM&nbsp;•&nbsp;Encryption"]
    Layer3["LAYER&nbsp;3:&nbsp;ACCESS&nbsp;CONTROL<br/>Authorized&nbsp;Views&nbsp;•&nbsp;RLS&nbsp;•&nbsp;CLS"]
    Layer4["LAYER&nbsp;4:&nbsp;DATASET&nbsp;ORGANIZATION<br/>Dataset&nbsp;•&nbsp;Linked&nbsp;Dataset"]
    Layer5["LAYER&nbsp;5:&nbsp;SHARING&nbsp;MECHANISMS<br/>Data&nbsp;Exchange&nbsp;•&nbsp;Data&nbsp;Clean&nbsp;Room"]
    Layer6["LAYER&nbsp;6:&nbsp;ANALYSIS&nbsp;PATTERNS<br/>Aggregation&nbsp;•&nbsp;List&nbsp;Overlap&nbsp;•&nbsp;Diff&nbsp;Privacy"]

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Layer5
    Layer5 --> Layer6

    style Layer1 fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Layer2 fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style Layer3 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style Layer4 fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style Layer5 fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style Layer6 fill:#e0f2f1,stroke:#00796b,stroke-width:3px
```

**Key Message:** The example you just saw flows through 6 layers of increasing abstraction, with protection applied at each stage. Let's explore each layer in detail.

---

## Slide 3: Data Layer - The Foundation

**Title:** Layer 1: Data Layer

```mermaid
graph TB
    subgraph Current["CURRENT:&nbsp;DATA&nbsp;LAYER"]
        direction TB
        Column["Column<br/><br/>Sensitive&nbsp;data&nbsp;fields<br/>Identifiers<br/>Attributes"]
        Table["Table<br/><br/>Data&nbsp;entities<br/>Fact&nbsp;tables<br/>Dimension&nbsp;tables"]
        View["View<br/><br/>Filtered&nbsp;results<br/>Transformed&nbsp;data<br/>Joined&nbsp;datasets"]

        Column -->|"Columns form"| Table
        Table -->|"Tables create"| View
    end

    subgraph Next["NEXT:&nbsp;Protection&nbsp;Mechanisms"]
        direction TB
        Protection["Apply&nbsp;security&nbsp;controls<br/>to&nbsp;discovered&nbsp;data"]
    end

    Current --> Next

    style Current fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Next fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Column fill:#ffffff,stroke:#1976d2,stroke-width:2px
    style Table fill:#ffffff,stroke:#1976d2,stroke-width:2px
    style View fill:#ffffff,stroke:#1976d2,stroke-width:2px
```

**Key Points:**
- Column: Individual data fields containing sensitive information
- Table: Primary storage for structured data
- View: Query-based subsets without data duplication

---

## Slide 4: Protection Mechanisms - DCPA Lifecycle

**Title:** Layer 2: Protection Mechanisms

```mermaid
graph TB
    subgraph Previous["PREVIOUS:&nbsp;Data&nbsp;Layer"]
        direction TB
        PrevData["Raw&nbsp;data&nbsp;in<br/>columns,&nbsp;tables,&nbsp;views"]
    end

    subgraph Current["CURRENT:&nbsp;PROTECTION&nbsp;MECHANISMS"]
        direction TB

        subgraph Discover["STEP&nbsp;1:&nbsp;DISCOVER&nbsp;&&nbsp;CLASSIFY"]
            DLP["DLP&nbsp;-&nbsp;Sensitive&nbsp;Data&nbsp;Protection<br/><br/>Scans&nbsp;for&nbsp;sensitive&nbsp;information<br/>150+&nbsp;info&nbsp;types<br/>Automated&nbsp;discovery"]
        end

        subgraph Protect["STEP&nbsp;2:&nbsp;PROTECT"]
            Hash["Deterministic&nbsp;Hashing<br/><br/>Secure&nbsp;joins<br/>Irreversible<br/>DCR&nbsp;best&nbsp;practice"]
            DDM["Dynamic&nbsp;Data&nbsp;Masking<br/><br/>Identity-based<br/>Query-time<br/>Real-time"]
            Encrypt["Cloud&nbsp;KMS&nbsp;Encryption<br/><br/>Reversible<br/>Key&nbsp;management<br/>Enterprise-grade"]
        end

        DLP --> Hash
        DLP --> DDM
        DLP --> Encrypt
    end

    subgraph Next["NEXT:&nbsp;Access&nbsp;Control"]
        direction TB
        Access["Define&nbsp;who&nbsp;can<br/>see&nbsp;what&nbsp;data"]
    end

    Previous --> Current
    Current --> Next

    style Previous fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Current fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style Next fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Discover fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style Protect fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style DLP fill:#ffffff,stroke:#f57c00,stroke-width:2px
    style Hash fill:#ffffff,stroke:#f57c00,stroke-width:2px
    style DDM fill:#ffffff,stroke:#f57c00,stroke-width:2px
    style Encrypt fill:#ffffff,stroke:#f57c00,stroke-width:2px
```

**Key Points:**
- DLP: Discovers and classifies sensitive data automatically
- Hashing: One-way transformation for secure joins
- DDM: Real-time masking based on user identity
- Encryption: Reversible protection with key management

---

## Slide 5: Access Control - Fine-Grained Security

**Title:** Layer 3: Access Control

```mermaid
graph TB
    subgraph Previous["PREVIOUS:&nbsp;Protection&nbsp;Mechanisms"]
        direction TB
        PrevProtect["Protected&nbsp;data&nbsp;with<br/>hashing,&nbsp;masking,&nbsp;encryption"]
    end

    subgraph Current["CURRENT:&nbsp;ACCESS&nbsp;CONTROL&nbsp;LAYER"]
        direction TB

        AuthView["Authorized&nbsp;View<br/><br/>Share&nbsp;query&nbsp;results<br/>without&nbsp;dataset&nbsp;access<br/>Controlled&nbsp;exposure"]

        RLS["Row-Level&nbsp;Security<br/><br/>Filter&nbsp;rows&nbsp;by<br/>user&nbsp;identity<br/>Policy-based&nbsp;access"]

        CLS["Column-Level&nbsp;Security<br/><br/>Hide&nbsp;sensitive&nbsp;columns<br/>from&nbsp;users<br/>Taxonomy-based"]
    end

    subgraph Next["NEXT:&nbsp;Dataset&nbsp;Organization"]
        direction TB
        Dataset["Group&nbsp;tables&nbsp;into<br/>logical&nbsp;containers"]
    end

    Previous --> Current
    Current --> Next

    style Previous fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Current fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style Next fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style AuthView fill:#ffffff,stroke:#7b1fa2,stroke-width:2px
    style RLS fill:#ffffff,stroke:#7b1fa2,stroke-width:2px
    style CLS fill:#ffffff,stroke:#7b1fa2,stroke-width:2px
```

**Key Points:**
- Authorized View: Share specific data without granting dataset permissions
- Row-Level Security: Different users see different rows automatically
- Column-Level Security: Hide sensitive columns based on user roles

---

## Slide 6: Dataset Organization - Logical Containers

**Title:** Layer 4: Dataset Organization

```mermaid
graph TB
    subgraph Previous["PREVIOUS:&nbsp;Access&nbsp;Control"]
        direction TB
        PrevAccess["Access-controlled<br/>views&nbsp;and&nbsp;tables"]
    end

    subgraph Current["CURRENT:&nbsp;DATASET&nbsp;ORGANIZATION"]
        direction LR

        Dataset["Dataset<br/><br/>Logical&nbsp;container<br/>Groups&nbsp;related&nbsp;tables<br/>Access&nbsp;control&nbsp;boundary<br/>Single&nbsp;project"]

        LinkedDataset["Linked&nbsp;Dataset<br/><br/>Cross-project&nbsp;reference<br/>Centralized&nbsp;governance<br/>Multi-project&nbsp;access<br/>Unified&nbsp;view"]

        Dataset -->|"Can link to"| LinkedDataset
    end

    subgraph Next["NEXT:&nbsp;Sharing&nbsp;Mechanisms"]
        direction TB
        Sharing["Share&nbsp;datasets&nbsp;with<br/>external&nbsp;organizations"]
    end

    Previous --> Current
    Current --> Next

    style Previous fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Current fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style Next fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Dataset fill:#ffffff,stroke:#388e3c,stroke-width:2px
    style LinkedDataset fill:#ffffff,stroke:#388e3c,stroke-width:2px
```

**Key Points:**
- Dataset: Primary organizational unit in BigQuery
- Linked Dataset: Symbolic link to shared datasets via Analytics Hub
- Sharing enabled through Analytics Hub platform

---

## Slide 7: Sharing Mechanisms - DCX vs DCR

**Title:** Layer 5: Sharing Mechanisms

```mermaid
graph TB
    subgraph Previous["PREVIOUS:&nbsp;Dataset&nbsp;Organization"]
        direction TB
        PrevDataset["Organized&nbsp;datasets<br/>ready&nbsp;for&nbsp;sharing"]
    end

    subgraph Current["CURRENT:&nbsp;SHARING&nbsp;MECHANISMS"]
        direction TB

        subgraph DCX["Data&nbsp;Exchange&nbsp;(DCX)"]
            direction TB
            DCXFeatures["Trusted&nbsp;Partnership<br/><br/>Direct&nbsp;dataset&nbsp;access<br/>Full&nbsp;query&nbsp;capabilities<br/>ML&nbsp;model&nbsp;training<br/>Data&nbsp;egress&nbsp;allowed<br/><br/>Use&nbsp;when:&nbsp;High&nbsp;trust"]
        end

        subgraph DCR["Data&nbsp;Clean&nbsp;Room&nbsp;(DCR)"]
            direction TB
            DCRFeatures["Privacy-Preserving<br/><br/>Restricted&nbsp;queries&nbsp;only<br/>Aggregation&nbsp;thresholds<br/>No&nbsp;data&nbsp;egress<br/>Audit&nbsp;trails<br/><br/>Use&nbsp;when:&nbsp;Privacy&nbsp;critical"]
        end
    end

    subgraph Next["NEXT:&nbsp;Analysis&nbsp;Patterns"]
        direction TB
        Analysis["Execute&nbsp;privacy-preserving<br/>analytics&nbsp;queries"]
    end

    Previous --> Current
    Current --> Next

    style Previous fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Current fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style Next fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style DCX fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style DCR fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style DCXFeatures fill:#ffffff,stroke:#388e3c,stroke-width:2px
    style DCRFeatures fill:#ffffff,stroke:#d84315,stroke-width:2px
```

**Key Points:**
- Both DCX and DCR are implemented via Analytics Hub platform
- DCX: Trusted partnerships with full data access
- DCR: Privacy-critical scenarios with restricted access

---

## Slide 8: Analysis Patterns - DCR vs DCX Analytics

**Title:** Layer 6: Analysis Patterns

```mermaid
graph TB
    subgraph Previous["PREVIOUS:&nbsp;Sharing&nbsp;Mechanisms"]
        direction TB
        PrevSharing["Data&nbsp;shared&nbsp;via<br/>DCX&nbsp;or&nbsp;DCR"]
    end

    subgraph CurrentDCR["CURRENT:&nbsp;DCR&nbsp;ANALYSIS&nbsp;(No&nbsp;Egress)"]
        direction TB

        Aggregation["Aggregation&nbsp;with&nbsp;Threshold<br/><br/>Minimum&nbsp;row&nbsp;counts&nbsp;<br/>Group-level&nbsp;insights<br/>Prevents&nbsp;re-identification"]

        ListOverlap["List&nbsp;Overlap<br/><br/>Find&nbsp;mutual&nbsp;customers<br/>Intersection&nbsp;queries<br/>No&nbsp;full&nbsp;list&nbsp;exposure"]

        DiffPrivacy["Differential&nbsp;Privacy<br/><br/>Add&nbsp;statistical&nbsp;noise<br/>Public&nbsp;statistics&nbsp;release<br/>Mathematical&nbsp;guarantees"]
    end

    subgraph CurrentDCX["CURRENT:&nbsp;DCX&nbsp;ANALYSIS&nbsp;(With&nbsp;Egress)"]
        direction TB

        BQML["BQML&nbsp;Model&nbsp;Training<br/><br/>CREATE&nbsp;MODEL&nbsp;statements<br/>Collaborative&nbsp;ML<br/>Model&nbsp;artifacts&nbsp;saved"]

        DataExport["Data&nbsp;Export<br/><br/>Export&nbsp;to&nbsp;GCS<br/>Download&nbsp;results<br/>External&nbsp;processing"]

        CustomAnalytics["Custom&nbsp;Analytics<br/><br/>Full&nbsp;query&nbsp;flexibility<br/>Join&nbsp;with&nbsp;own&nbsp;data<br/>Unrestricted&nbsp;analysis"]
    end

    subgraph Next["NEXT:&nbsp;Business&nbsp;Insights"]
        direction TB
        Insights["Actionable&nbsp;insights<br/>without&nbsp;privacy&nbsp;risk"]
    end

    Previous --> CurrentDCR
    Previous --> CurrentDCX
    CurrentDCR --> Next
    CurrentDCX --> Next

    style Previous fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style CurrentDCR fill:#ffccbc,stroke:#d84315,stroke-width:3px
    style CurrentDCX fill:#c8e6c9,stroke:#388e3c,stroke-width:3px
    style Next fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5
    style Aggregation fill:#ffffff,stroke:#d84315,stroke-width:2px
    style ListOverlap fill:#ffffff,stroke:#d84315,stroke-width:2px
    style DiffPrivacy fill:#ffffff,stroke:#d84315,stroke-width:2px
    style BQML fill:#ffffff,stroke:#388e3c,stroke-width:2px
    style DataExport fill:#ffffff,stroke:#388e3c,stroke-width:2px
    style CustomAnalytics fill:#ffffff,stroke:#388e3c,stroke-width:2px
```

**Key Points:**

**DCR Analysis (No Data Egress):**
- Aggregation: Group-level insights without individual exposure
- List Overlap: Discover mutual customers securely
- Differential Privacy: Public statistics with privacy guarantees
- Query Templates: Predefined queries for controlled analysis

**DCX Analysis (Data Egress Allowed):**
- BQML: Train ML models with CREATE MODEL statements
- Data Export: Export results to GCS or download
- Custom Analytics: Full query flexibility for trusted partners

---

## Slide 9: Key Takeaways

**Title:** Best Practices Summary

### Protection Strategy
1. Always hash sensitive identifiers for joins in DCRs
   - Use SHA256 with shared salt
   - Never join on raw identifiers

2. Layer multiple protections
   - DLP for discovery
   - DDM for internal operational analytics
   - Hashing for DCR/DCX secure joins
   - Aggregation thresholds for privacy

3. Choose the right sharing mechanism
   - DCX: Trusted ML collaboration (with data egress)
   - DCR: Privacy-critical analytics (no data egress)

### DCPA Lifecycle for Data Clean Rooms
- Discover: Use DLP to find sensitive data
- Classify: Categorize with 150+ info types
- Protect: Apply hashing + authorized views for external sharing
- Analyze: Enable secure insights through analysis rules and differential privacy
