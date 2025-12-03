# Avalon: Next-Generation AI-Driven Pharmaceutical & Clinical Research Assistant

---

## 📋 EXECUTIVE SUMMARY (1-Page Overview)

**Avalon = Secure Local + Cloud Hybrid AI for Pharma & Healthcare**

Avalon is a purpose-built AI platform designed exclusively for clinical research, drug intelligence, patient safety, and pharmaceutical R&D. Unlike generic AI assistants, Avalon combines specialized pharmaceutical expertise with enterprise-grade security, enabling hospitals and research organizations to leverage AI capabilities while maintaining absolute patient data privacy.

### Core Value Proposition

**All PHI processed locally. Deep research handled by multi-agent architecture. AI that hospitals can trust.**

- **🔒 Security First**: Patient Health Information (PHI) never leaves your network. All sensitive queries processed on-premises using local language models.
- **🧠 Multi-Agent Intelligence**: Specialized AI agents work in parallel—Market Intelligence, Clinical Trials, Patents, Safety & PK/PD, Expert Networks—delivering comprehensive pharmaceutical insights.
- **⚡ Hybrid Architecture**: Local processing for PHI and sensitive data; optional cloud reasoning for non-PHI research queries requiring deep synthesis.
- **📊 Enterprise Ready**: Automated PDF/CSV report generation, expert network graphs, document intelligence, and real-time streaming outputs.
- **🏥 Healthcare Compliant**: HIPAA-aligned architecture with full audit trails, timeline visualization, and zero external PHI transmission.

### Quick Facts

| Feature          | Description                                          |
| ---------------- | ---------------------------------------------------- |
| **Deployment**   | On-premises, private cloud, or hybrid                |
| **PHI Handling** | 100% local processing, zero external transmission    |
| **Agents**       | 9 specialized pharmaceutical intelligence agents     |
| **Modes**        | Patient, Safety, Research, Table, Document, Expert, Simple |
| **Reports**      | Enterprise PDF + CSV with automatic generation       |
| **Voice Input**  | Real-time speech recognition with waveform display   |
| **RAG Systems**  | Project RAG + Data Source RAG with local embeddings  |
| **Compliance**   | HIPAA-aligned, full audit trails, source attribution |

### Why Avalon Over Generic AI?

✅ **Runs locally in hospitals** (ChatGPT/Claude cannot)  
✅ **Guarantees PHI isolation** (generic AI cannot)  
✅ **Processes medical documents on-premises** (hospitals cannot send externally)  
✅ **Specialized pharmaceutical agents** (purpose-built for pharma research)  
✅ **Complete explainability** (agent timeline, source citations, audit trails)  
✅ **Real-time Thinking Panel** (shows PHI detection and routing decisions before streaming)  
✅ **7-mode auto-classification** (Patient, Safety, Research, Table, Document, Expert, Simple)  
✅ **Voice-enabled research** (hands-free pharmaceutical queries with waveform visualization)  
✅ **Custom RAG integration** (organization's own documents with local embeddings)  
✅ **Hospital-grade PHI detection** (HIPAA 18 identifiers with confidence scoring)

---

## 🎯 USE CASES

Avalon delivers immediate value across pharmaceutical and healthcare organizations:

- **🏥 Clinical Decision Support**: Real-time drug interaction checks, dosing recommendations, and safety assessments for patient cases—all processed locally with zero PHI exposure
- **🔬 Competitive Intelligence**: Comprehensive market analysis, patent landscape reviews, and competitive positioning for drug development strategy
- **📊 Clinical Trial Intelligence**: Active trial monitoring, phase analysis, endpoint evaluation, and evidence synthesis across multiple studies
- **📄 Regulatory Research**: FDA/EMA guideline interpretation, approval tracking, compliance assessment, and regulatory submission support
- **💊 Drug Repurposing**: Mechanism-based analysis identifying new indications, rare disease opportunities, and formulation innovations
- **👥 Expert Network Discovery**: Knowledge graph construction revealing key opinion leaders, collaboration patterns, and research relationships
- **📑 Automated Report Generation**: One-click PDF/CSV reports compiling multi-agent findings for executive presentations and regulatory documentation
- **🔍 Literature & Document Intelligence**: Upload clinical protocols, research papers, and internal documents for structured insight extraction and integration
- **🎤 Voice-Enabled Research**: Hands-free pharmaceutical queries with real-time speech recognition, waveform visualization, and voice chat conversations
- **📁 Project-Based Research**: Organize research activities into projects with dedicated document storage, conversation grouping, and project-specific RAG

---

## 👥 STAKEHOLDER-SPECIFIC VALUE

### For CIOs: Security, Compliance & Infrastructure

- **🔒 Zero PHI Exposure**: All patient data processed on-premises; no external API calls for sensitive queries
- **📋 HIPAA-Aligned Architecture**: Built-in compliance features, audit trails, and access controls
- **🏗️ Flexible Deployment**: On-premises, private cloud, or hybrid configurations based on organizational needs
- **💰 Cost Efficiency**: Local processing eliminates per-query cloud costs; optional cloud only for non-PHI research
- **🔍 Complete Auditability**: Full traceability of agent steps, routing decisions, and data access for compliance reviews
- **🛡️ Network Isolation**: PHI queries never leave hospital network; strict compartmentalization between local and cloud processing

### For CMOs: Market Intelligence & Competitive Strategy

- **📈 Market Analysis**: IQVIA-style insights on market size, CAGR, competitive density, and key players
- **🏆 Competitive Landscape**: Comprehensive analysis of therapy classes, pipeline entrants, and market positioning
- **💡 Strategic Intelligence**: Patent landscape analysis, FTO assessments, and regulatory pathway insights
- **📊 Executive Reports**: Automated PDF generation with executive summaries for board presentations
- **🔬 Clinical Trial Intelligence**: Real-time monitoring of competitor trials, endpoints, and regulatory designations
- **🌐 Global Market View**: Regional market differentiation, pricing trends, and reimbursement constraints

### For CTOs: Architecture, Scalability & Integration

- **🏛️ Modular Architecture**: Extensible multi-agent pipeline with strict schemas; add custom agents without core changes
- **⚡ Hybrid LLM Routing**: Intelligent engine selection (local vs. cloud) based on PHI detection and query complexity
- **🔄 Real-time Streaming**: Token-by-token response streaming with agent timeline visualization
- **📦 API-Ready**: RESTful APIs for integration with EMR/EHR systems, lab equipment, and research tools
- **🔧 Customizable Data Sources**: Integrate with ClinicalTrials.gov, patent databases, internal repositories, and custom APIs
- **📈 Scalable Design**: Parallel agent execution, caching, rate limiting, and performance optimization for enterprise scale
- **🎤 Voice Interface Integration**: Web Speech API integration with waveform visualization and auto-stop on silence
- **🔍 Dual RAG Architecture**: Project RAG for per-project documents + Data Source RAG for organization-wide knowledge bases

---

## 🏗️ ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                     │
│  "Comprehensive market analysis" OR "What is the mechanism of aspirin?"   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Chat.tsx)                                │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 1. User submits query                                              │    │
│  │ 2. POST /api/chat/send                                             │    │
│  │ 3. Receives streaming response with metadata                       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND (app/routes/chat.py)                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Receives query from frontend                                    │    │
│  │ 2. Calls: master_agent.run_stream(query)                           │    │
│  │ 3. Streams response chunks to client                               │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  MASTER AGENT (app/agents/master_agent.py)                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 1: DETECTION & CLASSIFICATION                               │    │
│  │ ──────────────────────────────────────────────────────────────────│    │
│  │ query_lower = query.lower()                                        │    │
│  │ research_insights_keywords = [                                     │    │
│  │   "research insights", "insights table",                           │    │
│  │   "comprehensive analysis", "market analysis",                     │    │
│  │   "competitive landscape", ...                                     │    │
│  │ ]                                                                  │    │
│  │ enable_research_insights = any(kw in query_lower                   │    │
│  │                                for kw in keywords)                 │    │
│  │                                                                    │    │
│  │ Result: enable_research_insights = True/False                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                      │                                      │
│                    ┌─────────────────┴─────────────────┐                  │
│                    │                                   │                  │
│          enable_research_insights?                      │                  │
│                    │                                   │                  │
│              YES   │   NO                              │                  │
│                    │                                   │                  │
│                    ▼                                   ▼                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ PHASE 2: WORKER ORCHESTRATION (SHARED PATH)                       │    │
│  │ ──────────────────────────────────────────────────────────────────│    │
│  │ Parallel execution with asyncio.gather():                          │    │
│  │                                                                    │    │
│  │   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │    │
│  │   │ MarketAgent    │  │ ClinicalAgent  │  │ PatentAgent    │    │    │
│  │   │ ────────────── │  │ ────────────── │  │ ────────────── │    │    │
│  │   │ • Market size  │  │ • Active trials│  │ • Patents      │    │    │
│  │   │ • CAGR         │  │ • Phases       │  │ • Expiry dates │    │    │
│  │   │ • Key players  │  │ • Sponsors     │  │ • Assignees    │    │    │
│  │   │ • Trends       │  │ • Indications  │  │ • Claims       │    │    │
│  │   └────────────────┘  └────────────────┘  └────────────────┘    │    │
│  │                                                                    │    │
│  │   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │    │
│  │   │ SafetyAgent    │  │ WebIntelAgent  │  │ ExpertNetwork  │    │    │
│  │   │ ────────────── │  │ ────────────── │  │ Agent           │    │    │
│  │   │ • PKPD         │  │ • News         │  │ • Graph         │    │    │
│  │   │ • Adverse evts │  │ • Publications │  │ • KOLs          │    │    │
│  │   │ • Interactions │  │ • Regulatory   │  │ • Collaborations│    │    │
│  │   │ • Warnings     │  │ • Updates      │  │                 │    │    │
│  │   └────────────────┘  └────────────────┘  └────────────────┘    │    │
│  │                                                                    │    │
│  │ Each worker returns:                                               │    │
│  │ {                                                                  │    │
│  │   "full_text": "Detailed findings...",                            │    │
│  │   "metadata": {                                                    │    │
│  │     "sources": [                                                   │    │
│  │       {"url": "https://pubmed.ncbi.nlm.nih.gov/..."},             │    │
│  │       {"url": "https://clinicaltrials.gov/..."}                   │    │
│  │     ]                                                              │    │
│  │   }                                                                │    │
│  │ }                                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                    │                                   │                    │
│                    ▼                                   ▼                    │
│  ┌──────────────────────────────────┐  ┌────────────────────────────────┐│
│  │ PATH A: RESEARCH INSIGHTS TABLE   │  │ PATH B: SIMPLE TEXT SYNTHESIS   ││
│  │ (enable_research_insights = True) │  │ (enable_research_insights = False)││
│  │                                   │  │                                  ││
│  │ ┌──────────────────────────────┐ │  │ ┌────────────────────────────┐  ││
│  │ │ PHASE 3: INSIGHTS COMPILATION │ │  │ │ PHASE 3: TEXT SYNTHESIS    │  ││
│  │ │ ──────────────────────────── │ │  │ │ ────────────────────────── │  ││
│  │ │ insights = await             │ │  │ │ • Combine worker outputs   │  ││
│  │ │   _build_research_insights_   │ │  │ │ • Structure narrative      │  ││
│  │ │   table(worker_results)      │ │  │ │ • Add source citations     │  ││
│  │ │                               │ │  │ │ • Generate full_text       │  ││
│  │ │ For each worker:              │ │  │ │ • Create timeline events  │  ││
│  │ │ • Extract key findings        │ │  │ │                              │  ││
│  │ │ • Calculate depth score       │ │  │ │ final_json = {             │  ││
│  │ │ • Extract source links       │ │  │ │   "full_text": "Synthesized │  ││
│  │ │ • Determine status           │ │  │ │     paragraph response...",│  ││
│  │ │                               │ │  │ │   "mode": "pharma_research",│  ││
│  │ │ Build insight_row:           │ │  │ │   "workers": {...},        │  ││
│  │ │ {                             │ │  │ │   "trace": [...]          │  ││
│  │ │   "section": "Market",        │ │  │ │ }                          │  ││
│  │ │   "key_findings": [...],      │ │  │ │                              │  ││
│  │ │   "depth": "High",            │ │  │ │ yield final_json           │  ││
│  │ │   "links": [...],             │ │  │ │   → Stream to frontend      │  ││
│  │ │   "status": "Complete"        │ │  │ └────────────────────────────┘  ││
│  │ │ }                             │ │  │                                  ││
│  │ └──────────────────────────────┘ │  │                                  ││
│  │                                   │  │                                  ││
│  │ ┌──────────────────────────────┐ │  │                                  ││
│  │ │ PHASE 4: FINAL RESPONSE      │ │  │                                  ││
│  │ │ ──────────────────────────── │ │  │                                  ││
│  │ │ final_json = {               │ │  │                                  ││
│  │ │   "full_text": "...",        │ │  │                                  ││
│  │ │   "research_insights": [     │ │  │                                  ││
│  │ │     {                        │ │  │                                  ││
│  │ │       "section": "Market",   │ │  │                                  ││
│  │ │       "key_findings": [...], │ │  │                                  ││
│  │ │       "depth": "High",       │ │  │                                  ││
│  │ │       "links": [...],        │ │  │                                  ││
│  │ │       "status": "Complete"   │ │  │                                  ││
│  │ │     },                        │ │  │                                  ││
│  │ │     // ... more sections      │ │  │                                  ││
│  │ │   ],                          │ │  │                                  ││
│  │ │   "mode": "pharma_research", │ │  │                                  ││
│  │ │   "workers": {...},          │ │  │                                  ││
│  │ │   "trace": [...]             │ │  │                                  ││
│  │ │ }                             │ │  │                                  ││
│  │ │                               │ │  │                                  ││
│  │ │ yield final_json              │ │  │                                  ││
│  │ │   → Stream to frontend        │ │  │                                  ││
│  │ └──────────────────────────────┘ │  │                                  ││
│  └──────────────────────────────────┘  └────────────────────────────────┘│
│                    │                                   │                    │
│                    └─────────────────┬─────────────────┘                  │
│                                      │                                      │
│                                      ▼                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND RENDERING                                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ if (message.metadata?.research_insights) {                          │    │
│  │   // PATH A: Render Research Insights Table                        │    │
│  │   <ResearchInsightsTable insights={...} />                         │    │
│  │   ┌──────────────────────────────────────────────────────────────┐ │    │
│  │   │ 📊 Research Insights Table                                    │ │    │
│  │   │ ┌──────────┬──────────────┬──────┬───────────┬───────┬──────┐│ │    │
│  │   │ │ Section  │ Key Findings │Depth│ Visual    │ Links │Status││ │    │
│  │   │ ├──────────┼──────────────┼──────┼───────────┼───────┼──────┤│ │    │
│  │   │ │ Market   │ • Finding 1  │ 🟢H │ 📊 View  │ Src 1 │✓ Comp││ │    │
│  │   │ │ Clinical │ • Finding 1  │ 🟡M │ 📊 View  │ Src 1 │✓ Comp││ │    │
│  │   │ │ Patents  │ • Finding 1  │ 🟡M │ 📊 View  │  —    │ Limit││ │    │
│  │   │ │ Safety   │ • Finding 1  │ 🔴L │ 📊 View  │  —    │ Miss ││ │    │
│  │   │ │ Web      │ • Finding 1  │ 🟡M │    —     │ Src 1 │✓ Comp││ │    │
│  │   │ └──────────┴──────────────┴──────┴───────────┴───────┴──────┘│ │    │
│  │   └──────────────────────────────────────────────────────────────┘ │    │
│  │ } else {                                                           │    │
│  │   // PATH B: Render Simple Text Response                          │    │
│  │   <StreamingMessageBubble content={full_text} />                  │    │
│  │   ┌──────────────────────────────────────────────────────────────┐ │    │
│  │   │ Synthesized paragraph response with agent findings...        │ │    │
│  │   │ • Market analysis shows...                                    │ │    │
│  │   │ • Clinical trials indicate...                                 │ │    │
│  │   │ • Patent landscape reveals...                                 │ │    │
│  │   │ [Source citations and timeline visible]                        │ │    │
│  │   └──────────────────────────────────────────────────────────────┘ │    │
│  │ }                                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER SEES OUTPUT                                  │
│  PATH A: Research Insights Table (structured, tabular)                      │
│  PATH B: Simple Text Response (narrative, synthesized)                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔥 SECTION 1 — PRODUCT OVERVIEW

**Avalon** is a next-generation AI-driven Pharmaceutical & Clinical Research Assistant that transforms scattered medical knowledge into actionable intelligence across clinical research, treatment insights, safety analysis, and regulatory reasoning.

Avalon serves as a secure, local-first, multi-agent medical intelligence platform designed specifically for pharmaceutical companies, clinical research organizations, hospitals, and healthcare institutions. Unlike generic AI assistants, Avalon is purpose-built for the pharmaceutical domain, combining deep medical reasoning with enterprise-grade security and compliance.

**Value Proposition:** _Avalon transforms scattered medical knowledge into actionable intelligence across clinical research, treatment insights, safety analysis, and regulatory reasoning._

---

## 🔥 SECTION 2 — AVALON'S CORE FEATURES

### Multi-Agent Pharma Intelligence Pipeline (Fully Implemented in Prototype)

Avalon orchestrates specialized AI agents that work in parallel to deliver comprehensive pharmaceutical insights. Each agent is an expert in its domain—from market intelligence to clinical trial analysis, patent landscapes to safety profiling. The system intelligently routes queries to the appropriate agents, synthesizes their findings, and presents unified, evidence-backed responses.

### Local (On-Prem) + Cloud Hybrid Architecture (Partially Implemented — requires larger models or enterprise environment)

Avalon operates on a sophisticated hybrid architecture that prioritizes security and performance. Patient Health Information (PHI) and sensitive clinical data are processed entirely on-premises using local language models, ensuring zero data leaves your network. For non-PHI research queries requiring deep reasoning, Avalon can optionally leverage cloud-based models while maintaining strict compartmentalization.

### Real-time Streaming Output (Fully Implemented in Prototype)

Experience live, token-by-token responses as Avalon processes your queries. The streaming interface provides immediate feedback, showing agent activity, reasoning steps, and findings as they emerge. This real-time visibility transforms the research experience from waiting for results to actively observing intelligence generation.

### Agent Timeline Visualization (Fully Implemented in Prototype)

Every query generates a detailed timeline showing which agents were activated, what tasks they performed, and how their outputs contributed to the final answer. This transparency enables researchers to understand the reasoning process, verify sources, and build trust in AI-generated insights.

### Expert Network Graphs (Fully Implemented in Prototype)

Avalon automatically builds knowledge graphs connecting researchers, institutions, clinical trials, and publications. These visual networks reveal collaboration patterns, expertise clusters, and research relationships that would be impossible to discover manually. Interactive graph visualizations help identify key opinion leaders, research gaps, and collaboration opportunities.

### Research Insights Table (Fully Implemented - Enterprise-Grade Dark Theme)

Avalon generates structured research insights tables with an enterprise-grade dark theme UI matching ChatGPT Teams and Perplexity Pro standards. The table component features:

- **Dark Glass Morphism Design**: Professional gray-900/30 background with backdrop blur effects
- **Structured Data Display**: Six-column layout (Section | Key Findings | Depth | Visualization | Links | Status)
- **Color-Coded Depth Indicators**: Visual depth tags (green for High, yellow for Medium, gray for Low) with proper contrast
- **Expandable Findings**: "Show more" functionality for long lists of key findings
- **Interactive Visualizations**: BarChart3 icon buttons linking to data visualizations
- **External Source Links**: Direct links to research sources with ExternalLink icons
- **Status Indicators**: Complete, Limited, or Missing Data status with CheckCircle2 icons
- **Smooth Animations**: 500ms fade-in animation for professional appearance
- **Responsive Design**: Horizontal scroll for smaller screens with sticky header
- **Hover Effects**: Subtle transitions on row hover for enhanced interactivity

The Research Insights Table is automatically displayed when multi-agent research queries include comprehensive analysis keywords, providing a structured overview of findings from all active agents.

### File Upload & Document Intelligence (Fully Implemented in Prototype)

Upload PDFs, clinical trial documents, research papers, and internal reports. Avalon extracts structured insights, identifies key arguments, summarizes findings, and integrates document content into research queries. The system supports multiple formats including PDF, DOCX, TXT, and Markdown, with intelligent text extraction and analysis.

### CSV Export for Agent-Generated Tables (Fully Implemented in Prototype)

Avalon automatically detects tables in agent responses and provides one-click CSV download functionality. When the system generates structured data tables (market analysis, clinical trial comparisons, drug summaries), a download button appears allowing users to export the data as CSV for further analysis in Excel, Tableau, or other analytics tools. The CSV export feature includes:

- **Automatic Table Detection**: Identifies markdown tables in agent responses using pipe character analysis
- **Smart CSV Formatting**: Proper escaping of special characters and quote handling
- **Timestamped Filenames**: Downloads named with current timestamp for easy organization
- **Available in Real-Time**: Works for both completed messages and streaming responses
- **Clean Data Export**: Extracts table HTML and converts to properly formatted CSV structure

### Automated Report Generation (PDF + CSV) (Partially Implemented — requires larger models or enterprise environment)

Generate enterprise-grade reports with a single click. Avalon compiles multi-agent findings into professionally formatted PDF documents with executive summaries, agent-by-agent sections, data tables, and source citations. CSV exports enable further analysis in Excel, Tableau, or other analytics tools. Reports include branding support and are stored securely for future reference.

### Intelligent Mode Classification (Fully Implemented in Prototype)

Avalon uses an Auto-Mode Intelligence system that automatically classifies queries into seven specialized modes without requiring user specification:

- **Patient Mode**: Activated for patient-specific queries containing PHI. Ensures all processing occurs locally with strict privacy controls.
- **Safety Mode**: For clinical safety queries, drug interactions, dosing, and contraindication analysis with medical disclaimers.
- **Research Mode**: Comprehensive multi-agent analysis for deep pharmaceutical research questions.
- **Table Mode**: Automatically detected when queries contain "compare", "vs", "differences" - generates structured comparison tables.
- **Document Mode**: Activated when PDF/DOCX files are uploaded for analysis with structured insight extraction.
- **Expert Mode**: For expert network queries, KOL identification, and collaboration graph generation.
- **Simple Mode**: Quick, direct answers (3-6 bullets) for straightforward informational queries without agent orchestration.

**Mode Detection Priority Order:**
1. Patient Mode (PHI detected - highest priority)
2. Safety Mode (non-pharma or risk queries)
3. Document Mode (file attachments present)
4. Table Mode (comparison intent detected)
5. Expert Mode (expert/specialist queries)
6. Research Mode (deep analysis keywords)
7. Simple Mode (default fallback)

### Thinking Panel System (Fully Implemented in Prototype)

Before any tokens stream to the user, Avalon displays a real-time "Thinking Panel" showing the routing decision and mode classification. This provides complete transparency into how queries are processed.

**Thinking Panel Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER SUBMITS QUERY                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHI DETECTION (Hospital-Grade)                            │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Scans for HIPAA 18 Identifiers:                                    │    │
│  │ • Names, SSN, MRN, DOB, Phone, Email, Address                     │    │
│  │ • Lab values with units (HbA1c, creatinine, BP)                   │    │
│  │ • Patient context keywords ("my patient", "patient ID")           │    │
│  │ • Clinical note patterns (HPI, CC, PMH, medications)              │    │
│  │                                                                    │    │
│  │ Returns: contains_phi, phi_types[], confidence score              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
              PHI Detected?                       No PHI Detected
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────────┐  ┌────────────────────────────────────┐
│ 🟡 LOCAL MODEL ENFORCED          │  │ 🟢 CHECK CLOUD ELIGIBILITY          │
│                                  │  │                                    │
│ Message: "PHI detected →         │  │ If cloud_enabled:                  │
│   Switching to Local Model"      │  │   "No PHI → Using Cloud Model"     │
│                                  │  │ Else:                              │
│ routing_mode = "local"           │  │   "No PHI → Using Local Model"     │
└──────────────────────────────────┘  └────────────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MODE CLASSIFICATION                                      │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Detects: Research, Safety, Table, Document, Expert, Patient, Simple│    │
│  │ Returns: mode, required_agents[], reason                          │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EMIT THINKING EVENT (SSE)                                 │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ {"type": "thinking", "message": "PHI detected → Local Model"}      │    │
│  │ {"type": "routing", "mode": "local", "detected_mode": "safety"}    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND DISPLAYS THINKING PANEL                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ ┌────────────────────────────────────────────────────────────────┐ │    │
│  │ │ ● ● ●  AVALON IS THINKING…                                     │ │    │
│  │ ├────────────────────────────────────────────────────────────────┤ │    │
│  │ │ 🛡️ PHI detected → Switching to Local Model          [Local]   │ │    │
│  │ │ 🔬 Safety Mode activated                                       │ │    │
│  │ │ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░ (loading bar)              │ │    │
│  │ └────────────────────────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                              (250ms delay)
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              TIMELINE EVENTS → AGENT ORCHESTRATION → TOKEN STREAMING         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Thinking Panel UI Features:**
- Animated pulsing dots during processing
- Color-coded PHI indicator (yellow for PHI, green for no PHI)
- Local/Cloud badge showing model selection
- Mode-specific icons and colors
- Animated loading bar
- Automatically hides when first token arrives

### HIPAA-Aware Local PHI Handling (Fully Implemented in Prototype)

Patient Health Information is detected automatically and routed exclusively to local inference engines. Zero PHI data leaves the hospital network, ensuring compliance with HIPAA, GDPR, and other healthcare privacy regulations. The system maintains strict audit trails and access controls.

**PHI Detector Module - Hospital-Grade Detection:**

The PHI detector (`phi_detector.py`) implements comprehensive detection for all HIPAA 18 identifiers:

| Identifier Category | Detection Patterns |
|--------------------|--------------------|
| **Names** | Patient names, placeholders (John Doe, Jane Doe) |
| **SSN** | Social Security Numbers (XXX-XX-XXXX formats) |
| **MRN** | Medical Record Numbers (MRN#, MR#, chart numbers) |
| **DOB** | Dates of birth, age specifications |
| **Phone Numbers** | All phone formats including international |
| **Email Addresses** | Standard email patterns |
| **Physical Addresses** | Street addresses, cities, ZIP codes |
| **Clinical Measurements** | Lab values with units (HbA1c, creatinine, BP, weight) |
| **Patient Context** | "my patient", "patient ID", "patient named" |
| **Clinical Notes** | HPI, CC, PMH, medications, diagnoses |
| **Vitals** | Blood pressure, pulse, temperature, SpO2 |
| **Lab Results** | Any numeric value with medical units |

**PHI Detection Result Structure:**
```
PHIDetectionResult:
  - contains_phi: boolean
  - phi_types: List[PHIType]  # Which types were detected
  - confidence: float         # 0.0 to 1.0
  - matched_patterns: List[str]
  - recommendation: "local" | "block"
```

**PHI Type Enum:**
- NAME, SSN, MRN, DOB, PHONE, EMAIL, ADDRESS
- PATIENT_DATA, LAB_RESULTS, VITALS, DIAGNOSIS
- MEDICATION_SPECIFIC, UNKNOWN

### No Mock Data — Real Model Outputs (Fully Implemented in Prototype)

Avalon generates authentic, model-driven responses. The system explicitly avoids mock data, templates, or hard-coded responses. When data is unavailable, Avalon clearly states "Unknown — requires validated data" rather than inventing statistics or facts.

### Voice Input & Voice Chat (Fully Implemented in Prototype)

Avalon provides hands-free pharmaceutical research through an integrated voice system:

- **Real-time Speech Recognition**: Uses Web Speech API with continuous listening and interim results for live transcription
- **Waveform Visualization**: Dynamic audio waveform display showing voice input levels with smooth animations
- **Auto-Stop on Silence**: Intelligent silence detection automatically stops recording after configurable silence duration
- **Voice Chat Modal**: Dedicated full-screen voice conversation mode for hands-free research sessions
- **Text-to-Speech Response**: AI responses can be spoken aloud for complete hands-free interaction
- **Browser Compatibility**: Supports Chrome and Edge with graceful degradation for unsupported browsers

### Data Source RAG Integration (Fully Implemented in Prototype)

Avalon includes a Retrieval-Augmented Generation system for custom organizational knowledge:

- **Local Embeddings**: Uses sentence-transformers (all-MiniLM-L6-v2) running locally on CPU
- **Multi-Format Support**: Supports PDF, DOCX, TXT, MD, CSV, and JSON documents
- **Automatic Categorization**: Documents are automatically categorized by therapeutic area
- **Semantic Search**: Cosine similarity-based retrieval of relevant document chunks
- **Source-Specific Queries**: Users can restrict searches to specific data sources

### Secure Compartmentalization Between PHI and Cloud Models (Partially Implemented — requires larger models or enterprise environment)

The architecture enforces strict boundaries between PHI-sensitive local processing and non-PHI cloud reasoning. Queries are automatically classified, and routing decisions are logged and auditable. This compartmentalization enables powerful cloud-based analysis for research while maintaining absolute security for patient data.

### Modular Worker Agents with Strict Schemas (Fully Implemented in Prototype)

Each worker agent operates with well-defined schemas, ensuring consistent output formats and enabling reliable integration. Agents can be added, modified, or disabled without affecting the core orchestration system, providing flexibility for customization and future enhancements.

---

## 🔥 SECTION 3 — COMPLETE ARCHITECTURE OVERVIEW

### 1. Avalon Master Agent

The **Avalon Master Agent** serves as the central orchestrator of the entire platform. It performs several critical functions:

**Query Classification & Domain Detection**: The Master Agent first determines whether a query falls within the pharmaceutical domain. Non-pharmaceutical questions are politely redirected, ensuring the system maintains focus on its specialized expertise.

**Task Decomposition**: Complex research questions are broken down into discrete, parallelizable tasks. For example, a query about "GLP-1 agonist competitive landscape" might be decomposed into market analysis, clinical trial review, patent examination, and safety profiling tasks.

**Worker Agent Coordination**: The Master Agent selects which specialized worker agents to activate based on query content. It manages parallel execution, handles agent failures gracefully, and ensures all relevant perspectives are captured.

**Pharma Guardrails**: Built-in pharmaceutical domain expertise ensures responses meet industry standards. The Master Agent enforces depth requirements, evidence standards, and output quality controls specific to pharmaceutical research.

**Synthesis Engine**: After worker agents complete their tasks, the Master Agent synthesizes their outputs into a coherent, structured response. This synthesis maintains source attribution, preserves key findings, and presents information in formats optimized for different use cases.

**Structured Outputs**: The Master Agent generates outputs in multiple formats—narrative summaries, structured tables, bullet points, and JSON—depending on user needs and query type.

### 2. Local LLM Execution Layer

The **Local LLM Execution Layer** runs small, efficient language models (currently Mistral-7B Q6_K) directly on your infrastructure.

**Current Architecture**: In the prototype implementation, all specialized agents share a single local language model instance. This unified model approach enables the multi-agent pipeline to function efficiently with minimal infrastructure requirements while maintaining the core orchestration and domain-specific reasoning capabilities.

**Future Architecture**: Planned upgrades will assign dedicated language models (one or two specialized models) to each agent, enabling deeper domain-specific reasoning, enhanced accuracy, and eliminating potential information cross-contamination between agent tasks. Each agent will leverage models optimized for its specific domain expertise.

**LLM Router - Hybrid Dual-Layer Routing:**

The `llm_router.py` module implements intelligent engine selection:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM ROUTER DECISION TREE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User Query ─────► PHI Detection ─────► PHI Found? ─────► YES ─► LOCAL     │
│                           │                                  │              │
│                           └── NO ──► Cloud Enabled? ─► YES ──► CLOUD        │
│                                              │                              │
│                                              └── NO ──────────► LOCAL       │
│                                                                              │
│   FALLBACK CHAIN:                                                           │
│   1. Primary engine fails → Retry with exponential backoff                  │
│   2. Timeout (30s) → Graceful timeout message                               │
│   3. Connection error → LM Studio not running message                       │
│   4. Short response → Request clarification message                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Graceful Error Handling:**
- Empty/short responses detected and handled with helpful fallback messages
- Timeout handling with user-friendly explanations
- Connection error detection when LM Studio is not running
- All errors logged for debugging and audit

This layer handles:

**PHI-Sensitive Requests**: All queries containing patient health information are processed exclusively by local models. This ensures zero data transmission outside your network.

**Offline Safety Analysis**: Drug interactions, dosing calculations, adverse event assessments, and symptom analysis occur entirely on-premises, providing immediate responses without network dependencies.

**PDF Extraction on Device**: Document processing and text extraction from uploaded files happens locally, preventing sensitive documents from being transmitted to external services.

**Real-time Inference**: Local models provide low-latency responses for common queries, enabling interactive research workflows without waiting for cloud API calls.

**Privacy-First Design**: The local layer operates independently of internet connectivity, ensuring research can continue even during network outages or security incidents.

### 3. Cloud LLM Execution Layer (Optional Future Upgrade)

The **Cloud LLM Execution Layer** is an optional component designed for future activation. When enabled, it handles:

**Deep Reasoning Tasks**: Complex queries requiring extensive chain-of-thought reasoning, multi-step analysis, and sophisticated synthesis leverage cloud-based models for superior performance.

**Advanced Literature Synthesis**: Large-scale literature reviews, meta-analyses, and comprehensive evidence synthesis benefit from cloud models' enhanced reasoning capabilities.

**Market Analysis**: Deep market intelligence queries requiring extensive knowledge of global pharmaceutical markets, pricing trends, and competitive dynamics.

**Patent Interpretation**: Complex patent claims analysis, prior art searches, and intellectual property landscape assessments.

**Clinical Trial Summarization**: Comprehensive analysis of large clinical trial datasets, cross-trial comparisons, and evidence synthesis.

**Non-PHI Pathway**: The cloud layer is strictly gated—only queries confirmed to contain no PHI are routed to cloud models. This pathway includes multiple validation checks and audit logging.

### Intelligent Engine Selection

Avalon automatically chooses which execution engine to use based on:

1. **PHI Detection**: Any detected patient information immediately routes to local processing.
2. **Query Complexity**: Simple informational queries use local models; complex research questions may leverage cloud models if enabled.
3. **Mode Classification**: Safety and patient modes always use local; research mode may use cloud for deep synthesis.
4. **Feature Flags**: Administrators can enable or disable cloud routing based on organizational policies.
5. **Network Conditions**: The system can fall back to local processing if cloud services are unavailable.

This intelligent routing ensures optimal performance, security, and cost-effectiveness for each query type.

---

## 🔥 SECTION 4 — MULTI-AGENT PIPELINE (Detailed)

Avalon's multi-agent architecture consists of specialized worker agents, each an expert in its domain. These agents operate in parallel, providing comprehensive coverage of pharmaceutical research questions.

### 1. Market Intelligence Agent (Partially Implemented — requires larger models or enterprise environment)

The **Market Intelligence Agent** simulates IQVIA-style pharmaceutical market insights, providing competitive landscape analysis and commercial intelligence.

**Responsibilities:**

- Global and regional market size estimation
- 5-year CAGR projections and growth trends
- Brand vs. generics market share analysis
- Competitive density assessment (HHI scores)
- Key player identification and market positioning
- Pipeline entrant analysis
- Pricing pressure factors and reimbursement constraints
- Therapy class evolution and market dynamics

**Strengths:**

- Quantitative market analysis with numerical projections
- Competitive intelligence synthesis
- Regional market differentiation
- Trend identification across therapy areas

**Real Usage Examples:**

- _"Analyze the GLP-1 agonist market landscape"_ → Provides market size, key players (Novo Nordisk, Eli Lilly), competitive dynamics, and growth projections
- _"Compare diabetes drug markets in US vs. EU"_ → Delivers regional market analysis with pricing and reimbursement differences
- _"What is the competitive landscape for PD-1 inhibitors?"_ → Identifies major players, market share, and emerging competitors

### 2. Clinical Trials Agent (Partially Implemented — requires larger models or enterprise environment)

The **Clinical Trials Agent** provides deep analysis of clinical trial data from ClinicalTrials.gov and other sources, offering evidence-based insights into drug development pipelines.

**Responsibilities:**

- Active trial identification by phase, indication, and sponsor
- Phase distribution analysis (Phase I, II, III, IV)
- Study design evaluation (randomized, placebo-controlled, etc.)
- Sponsor and CRO identification
- Primary and secondary endpoint analysis
- Patient population characteristics
- Recruitment status and enrollment data
- Safety summary compilation (adverse events, serious adverse events)
- Efficacy trend analysis across studies
- Regulatory designations (Fast Track, Breakthrough Therapy, Orphan Drug)

**Strengths:**

- Real-time access to ClinicalTrials.gov data
- Cross-trial comparison and synthesis
- Evidence gap identification
- Trial design quality assessment

**Real Usage Examples:**

- _"What are the active Phase III trials for Alzheimer's disease?"_ → Lists trials with sponsors, endpoints, and enrollment status
- _"Analyze safety profile of pembrolizumab from clinical trials"_ → Summarizes adverse events across multiple trials
- _"Compare efficacy endpoints for SGLT2 inhibitors in heart failure"_ → Cross-trial analysis of primary and secondary endpoints

### 3. Patent Landscape Agent (Partially Implemented — requires larger models or enterprise environment)

The **Patent Landscape Agent** interprets patent claims, analyzes intellectual property portfolios, and identifies freedom-to-operate considerations.

**Responsibilities:**

- Patent family identification and analysis
- Filing year and expiration timeline tracking
- Mechanism of action protection analysis
- Chemical class and composition claims interpretation
- Formulation and delivery system patent review
- Global coverage assessment (US, EU, JP, PCT)
- Freedom-to-operate (FTO) flag identification
- Litigation and exclusivity cliff analysis
- Patent landscape visualization

**Strengths:**

- Patent claim interpretation and analysis
- IP strategy insights
- Competitive intelligence through patent monitoring
- Expiration timeline tracking

**Real Usage Examples:**

- _"What patents protect GLP-1 receptor agonists?"_ → Lists patent families, expiration dates, and key claims
- _"Analyze freedom-to-operate for a new insulin formulation"_ → Identifies blocking patents and potential infringement risks
- _"When do key patents expire for checkpoint inhibitors?"_ → Provides expiration timeline and generic entry opportunities

### 4. EXIM Trends Agent (Partially Implemented — requires larger models or enterprise environment)

The **EXIM Trends Agent** analyzes import/export documentation, API manufacturing trends, and global supply chain intelligence.

**Responsibilities:**

- Active Pharmaceutical Ingredient (API) manufacturing trend analysis
- Import/export volume tracking
- Supply chain exposure assessment
- Manufacturing geography analysis
- Trade flow identification
- Regulatory compliance tracking for international trade

**Strengths:**

- Supply chain intelligence
- Manufacturing trend identification
- Trade flow analysis
- Risk assessment for supply chain disruptions

**Real Usage Examples:**

- _"What are the API manufacturing trends for metformin?"_ → Identifies major manufacturing regions and trade flows
- _"Analyze import/export exposure for insulin APIs"_ → Provides trade data and supply chain dependencies

### 5. Safety & PK/PD Agent (Fully Implemented in Prototype)

The **Safety & PK/PD Agent** provides comprehensive pharmacological analysis, including mechanism of action, toxicology, pharmacokinetics, and pharmacodynamics.

**Responsibilities:**

- Mechanism of action (MoA) pathway analysis
- Target class and drug category identification
- Pharmacokinetic profile analysis (half-life, bioavailability, clearance)
- Pharmacodynamic effects and dose-response relationships
- Drug-drug interaction risk assessment
- Adverse event profiling and severity analysis
- Toxicology reasoning and safety margins
- Blood-brain barrier penetration (for CNS drugs)
- On-target and off-target effect identification

**Strengths:**

- Deep pharmacological expertise
- Safety assessment capabilities
- Interaction prediction
- Dosing guidance support

**Real Usage Examples:**

- _"What is the mechanism of action of SGLT2 inhibitors?"_ → Explains the molecular pathway and physiological effects
- _"Analyze drug interactions for warfarin"_ → Lists major interactions with mechanisms and clinical significance
- _"What is the PK/PD profile of metformin?"_ → Provides pharmacokinetic parameters and pharmacodynamic effects

### 6. Internal Document Agent (Fully Implemented in Prototype)

The **Internal Document Agent** processes uploaded documents (PDFs, DOCX, TXT) and extracts structured insights for integration into research workflows.

**Responsibilities:**

- Document text extraction and parsing
- Key argument identification and summarization
- Structured insight extraction
- Section-by-section analysis
- Metadata extraction (authors, dates, sources)
- Integration with query context
- Document search and retrieval

**Strengths:**

- Multi-format document support
- Intelligent text extraction
- Context-aware analysis
- Seamless integration with research queries

**Real Usage Examples:**

- _"Analyze this clinical trial protocol"_ → Extracts study design, endpoints, and key parameters from uploaded PDF
- _"Summarize the key findings from this research paper"_ → Provides structured summary with main arguments and conclusions
- _"What does this internal report say about drug safety?"_ → Extracts safety-related content and integrates with broader research context

### 7. Web Intelligence Agent (Partially Implemented — requires larger models or enterprise environment)

The **Web Intelligence Agent** scrapes and analyzes web content to identify guidelines, scientific updates, regulatory announcements, and recent publications.

**Responsibilities:**

- Web content scraping (non-PHI only)
- Guideline identification (FDA, EMA, WHO, professional societies)
- Scientific publication monitoring
- Regulatory update tracking
- News and press release analysis
- Evidence source identification
- Content summarization and relevance assessment

**Strengths:**

- Real-time information access
- Regulatory monitoring
- Publication tracking
- Guideline identification

**Real Usage Examples:**

- _"What are the latest FDA guidelines for diabetes drugs?"_ → Identifies and summarizes recent FDA guidance documents
- _"Find recent publications on GLP-1 agonists"_ → Scrapes and summarizes recent scientific literature
- _"What regulatory updates affect SGLT2 inhibitors?"_ → Tracks and reports recent regulatory changes

### 8. Expert Network Agent (Fully Implemented in Prototype)

The **Expert Network Agent** builds knowledge graphs connecting researchers, institutions, clinical trials, and publications to reveal collaboration patterns and expertise clusters.

**Responsibilities:**

- Knowledge graph construction
- Expert identification and profiling
- Institution and affiliation mapping
- Collaboration network analysis
- Research relationship visualization
- Key opinion leader (KOL) identification
- Publication network analysis
- Clinical trial investigator networks

**Strengths:**

- Network analysis and visualization
- Relationship discovery
- KOL identification
- Collaboration pattern recognition

**Real Usage Examples:**

- _"Build an expert network for diabetes research"_ → Creates graph showing leading researchers, institutions, and their connections
- _"Who are the key opinion leaders in oncology?"_ → Identifies top researchers and their collaboration networks
- _"Visualize clinical trial investigator networks"_ → Maps relationships between investigators and institutions across trials

---

## 🔥 SECTION 5 — AVALON WORKFLOW EXAMPLES

Avalon adapts its behavior based on query type, automatically selecting the appropriate mode and agent combination. Here are real-world usage scenarios:

### Scenario 1: Researcher Wants GLP-1 Competitor Analysis

**Query:** _"Provide comprehensive competitive analysis of GLP-1 receptor agonists including market share, clinical trials, and patent landscape"_

**Avalon's Process:**

1. **Mode Detection**: Classifies as Research Mode (comprehensive analysis requested)
2. **Agent Selection**: Activates Market Intelligence Agent, Clinical Trials Agent, Patent Landscape Agent, and Safety & PK/PD Agent in parallel
3. **Execution**:
   - Market Agent analyzes competitive landscape, market size, and key players
   - Clinical Trials Agent reviews active trials, phases, and endpoints
   - Patent Agent examines IP protection and expiration timelines
   - Safety Agent provides mechanism of action and safety profiles
4. **Synthesis**: Master Agent combines findings into structured response with executive summary, market analysis, clinical evidence, IP landscape, and safety considerations
5. **Output**: Comprehensive report with tables, bullet points, and source citations

**Mode Used**: Research Mode (multi-agent orchestration)

### Scenario 2: Doctor Wants Safety Checks for a Patient Case

**Query:** _"My patient has HbA1c 8.9%, weight 108 kg, on metformin 1000mg BID. Should I add a GLP-1 agonist? Check for contraindications and drug interactions."_

**Avalon's Process:**

1. **Mode Detection**: Classifies as Clinical Safety Mode (PHI detected: patient-specific data)
2. **PHI Routing**: All processing occurs on local LLM (zero data leaves network)
3. **Agent Selection**: Activates Safety & PK/PD Agent and Internal Document Agent (if relevant documents uploaded)
4. **Execution**:
   - Safety Agent checks contraindications for GLP-1 agonists
   - Safety Agent analyzes drug interactions between metformin and GLP-1 agonists
   - Safety Agent provides dosing recommendations based on patient parameters
5. **Synthesis**: Master Agent provides direct, actionable clinical guidance
6. **Output**: Structured safety assessment with contraindication check, interaction analysis, and dosing recommendations

**Mode Used**: Clinical Safety Mode (local-only processing)

### Scenario 3: Hospital Wants PK/PD Insights

**Query:** _"Explain the pharmacokinetics and pharmacodynamics of SGLT2 inhibitors, including half-life, mechanism, and clinical implications"_

**Avalon's Process:**

1. **Mode Detection**: Classifies as Research Mode (comprehensive explanation requested)
2. **Agent Selection**: Primarily Safety & PK/PD Agent, with optional Web Intelligence Agent for recent guidelines
3. **Execution**:
   - Safety & PK/PD Agent provides detailed PK/PD analysis
   - Web Intelligence Agent checks for recent guidelines or updates
4. **Synthesis**: Master Agent structures response with clear sections on pharmacokinetics, pharmacodynamics, and clinical implications
5. **Output**: Detailed explanation with tables showing PK parameters, mechanism diagrams (text-based), and clinical relevance

**Mode Used**: Research Mode (focused on PK/PD expertise)

### Scenario 4: Pharma Team Wants a Compiled PDF Report

**Query:** _"Generate a comprehensive report on the diabetes drug market, including all agent findings, and export as PDF"_

**Avalon's Process:**

1. **Mode Detection**: Classifies as Research Mode with report generation intent
2. **Agent Selection**: Activates all relevant agents (Market, Clinical Trials, Patents, Safety, Web Intelligence)
3. **Execution**: All agents execute in parallel, generating comprehensive findings
4. **Synthesis**: Master Agent synthesizes all findings into structured format
5. **Report Generation**:
   - Extracts agent data from conversation
   - Generates enterprise PDF with executive summary
   - Includes agent-by-agent sections with findings
   - Adds data tables, source citations, and metadata
   - Applies professional pharmaceutical styling
6. **Storage**: PDF saved to reports library with metadata (date, topic, agents used)
7. **Output**: Downloadable PDF report with full research findings

**Mode Used**: Research Mode + Report Generation

### Scenario 5: Analyst Wants a Table Summarizing Mechanisms

**Query:** _"Create a comparison table of GLP-1, SGLT2, and DPP-4 inhibitors showing mechanism, indications, and key side effects"_

**Avalon's Process:**

1. **Mode Detection**: Classifies as Table Mode (explicit table request)
2. **Agent Selection**: Safety & PK/PD Agent (for mechanisms and side effects), no multi-agent orchestration needed
3. **Execution**: Safety Agent provides mechanism and safety data for all three drug classes
4. **Table Formatting**: Master Agent formats response as Markdown table with strict quality controls
5. **Output**: Clean, structured comparison table with three drug classes, mechanisms, indications, and side effects

**Mode Used**: Table Mode (direct table generation)

### How Avalon Decides Which Mode to Use

Avalon uses intelligent mode classification based on:

1. **Query Content Analysis**: Keywords, phrases, and intent detection
2. **PHI Detection**: Automatic identification of patient-specific information
3. **Complexity Assessment**: Simple vs. comprehensive query analysis
4. **Explicit Format Requests**: Table, bullet points, or narrative format preferences
5. **Document Context**: Presence of uploaded documents triggers Document Mode
6. **Metadata Analysis**: Previous conversation context and user preferences

The system prioritizes security (Safety Mode for PHI), efficiency (Simple Mode for straightforward queries), and comprehensiveness (Research Mode for deep analysis) based on query characteristics.

---

## 🔥 SECTION 6 — SECURITY & HEALTHCARE COMPLIANCE

Avalon is designed from the ground up to meet the stringent security and compliance requirements of healthcare and pharmaceutical organizations.

### Local Inference for PHI

All queries containing Patient Health Information (PHI) are automatically detected and processed exclusively on local language models. PHI detection uses pattern matching for:

- Patient identifiers (names, medical record numbers)
- Clinical measurements (lab values, vitals with units)
- Medical history references
- Treatment-specific patient data

Once PHI is detected, the query is immediately routed to the local LLM execution layer, ensuring zero external data transmission.

### Zero PHI Leaves Hospital Network

The architecture enforces strict network boundaries. PHI-containing queries never reach external APIs, cloud services, or third-party systems. All processing occurs within your infrastructure, behind your firewall, and under your direct control. Network monitoring and logging confirm that no PHI data is transmitted externally.

### Optional Cloud Pathway Only for Non-PHI Questions

The cloud LLM execution layer is strictly gated with multiple validation checks:

- PHI detection must pass (no patient data detected)
- Query must be classified as non-PHI research
- Feature flags must permit cloud routing
- Audit logs record all routing decisions

Even when cloud routing is enabled, the system defaults to local processing unless explicitly needed for deep synthesis tasks.

### Full Traceability of Agent Steps

Every query generates a complete audit trail:

- **Timeline Events**: Step-by-step record of agent activation, task execution, and completion
- **Agent Attribution**: Each finding is attributed to its source agent
- **Source Citations**: External sources (publications, trials, patents) are tracked and cited
- **Routing Decisions**: Logs show why specific agents were selected and which execution engine was used
- **Error Tracking**: Failures, retries, and fallback behaviors are logged

This traceability enables compliance audits, quality assurance, and debugging.

### Auditability with Timeline Logs

The Agent Timeline Visualization provides real-time and historical views of:

- Query classification and mode selection
- Agent activation sequence and parallel execution
- Task completion status and timing
- Data sources accessed and citations generated
- Synthesis steps and final output generation

Timeline logs are stored securely and can be exported for compliance reviews, quality audits, or research documentation.

### HIPAA-Aligned Architecture

Avalon's architecture aligns with HIPAA requirements through:

1. **Administrative Safeguards**: Role-based access controls, user authentication, and audit logging
2. **Physical Safeguards**: On-premises deployment options, network isolation, and infrastructure controls
3. **Technical Safeguards**: Encryption at rest and in transit, access controls, and PHI detection/routing
4. **Business Associate Considerations**: Clear data handling policies, breach notification procedures, and compliance documentation

The system is designed to support HIPAA compliance, though organizations should conduct their own compliance assessments based on specific use cases and regulatory requirements.

### Additional Security Features

- **Secure Document Storage**: Uploaded documents are stored with encryption and access controls
- **Session Management**: Secure session handling with token-based authentication
- **Rate Limiting**: Protection against abuse and resource exhaustion
- **Input Validation**: Sanitization and validation of all user inputs
- **Error Handling**: Secure error messages that don't leak sensitive information

---

## 🔥 SECTION 7 — REPORT GENERATION

Avalon's report generation system transforms multi-agent research findings into enterprise-grade documents suitable for executive presentations, regulatory submissions, and research documentation.

### Enterprise PDF Structure

PDF reports follow a professional pharmaceutical industry format with strict page ordering:

#### Page 1: Cover Page

```
┌─────────────────────────────────────┐
│         AVALON                      │
│                                     │
│     [Report Title]                  │
│                                     │
│  AI-Generated Pharmaceutical        │
│  Research Report                    │
│                                     │
│  Report Generated: [Date]           │
│  Report ID: [ID]                    │
│  Conversation ID: [ID]              │
│                                     │
│  Research Agents Deployed:          │
│  • Market Intelligence Agent        │
│  • Clinical Trials Analysis Agent   │
│  • Patent Landscape Agent           │
│  • Import/Export Intelligence Agent │
│  • Web Intelligence Agent           │
│  • Internal Documents Agent         │
│  • Safety & PK/PD Agent             │
│  • Expert Network Agent             │
│                                     │
│  Confidential Research —            │
│  Not For Distribution               │
└─────────────────────────────────────┘
```

#### Page 2: Executive Summary

```
Executive Summary

• Key finding 1
• Key finding 2
• Key finding 3
...

This report is programmatically generated
using Avalon's Multi-Agent Research Pipeline.
```

#### Page 3+: Agent Sections

Each agent section follows this structure:

```
╔═══════════════════════════════════════╗
║ SECTION 1 — Market Intelligence      ║  ← Colored header
╚═══════════════════════════════════════╝

Summary of Findings
[Summary text from agent...]

Key Insights
• Insight 1
• Insight 2
• Insight 3

Data Tables
┌────────────────────────────────────┐
│ Company    │ Product   │ Sales     │
├────────────────────────────────────┤
│ Novo       │ Ozempic   │ $8.9B     │
│ Lilly      │ Mounjaro  │ $5.2B     │
└────────────────────────────────────┘

Citations
Source 1, Source 2, Source 3

Provenance Notes
Database query - Q3 2024
```

#### Page Footer (All Pages Except Cover)

Every page includes a footer with:

**Left side:**

```
Page 1
```

**Center:**

```
© Avalon — AI-Driven Pharmaceutical Research Infrastructure
```

**Right side:**

```
Generated by Avalon — Confidential Clinical Research
```

### Automatic Table Extraction

The system automatically identifies and extracts tables from agent outputs:

- Market data tables (market size, CAGR, competitive metrics)
- Clinical trial tables (trial listings, phase distributions, endpoints)
- Patent tables (patent families, expiration dates, coverage)
- Comparison tables (drug comparisons, mechanism summaries)

Tables are formatted with professional styling, proper alignment, and clear headers.

### CSV Table Export

In addition to PDF reports, Avalon generates CSV exports for:

- **Data Analysis**: Import into Excel, Tableau, or other analytics tools
- **Further Processing**: Custom analysis and visualization
- **Data Sharing**: Structured data for collaboration

CSV files include:

- Agent findings in tabular format
- Source citations
- Metadata columns (agent name, timestamp, data depth indicators)

### Branding Support

Reports support custom branding:

- **Logo Integration**: Organization logos can be added to cover pages
- **Color Schemes**: Custom color palettes aligned with organizational branding
- **Footer Customization**: Organization name, contact information, disclaimers

### Report Storage

Generated reports are stored securely in the reports library with:

- **Metadata Indexing**: Searchable by topic, date, agents used, and keywords
- **Version Control**: Historical versions of reports for the same query
- **Access Controls**: Role-based access to reports based on user permissions
- **Export Options**: Download as PDF or CSV, share via secure links

Reports can be retrieved, viewed, downloaded, or regenerated at any time, providing a comprehensive research documentation system.

---

## 🔥 SECTION 8 — WHY AVALON OVER CHATGPT/CLAUDE

While ChatGPT and Claude are powerful general-purpose AI assistants, they are not designed for the unique requirements of pharmaceutical research and healthcare environments. Avalon provides specialized capabilities that generic AI cannot match.

### ChatGPT Cannot Run Locally in a Hospital

ChatGPT operates exclusively as a cloud service, requiring all queries to be transmitted to OpenAI's servers. This architecture is incompatible with hospital environments that must process PHI on-premises. Avalon's local-first architecture enables hospitals to deploy AI capabilities while maintaining complete control over sensitive data.

### Claude Cannot Guarantee PHI Isolation

While Claude offers some enterprise features, it cannot guarantee that PHI will never leave your network. Claude processes queries on Anthropic's infrastructure, requiring data transmission outside your control. Avalon's automatic PHI detection and local-only routing ensure absolute isolation of patient data.

### Hospitals Cannot Send Medical Documents Externally

Healthcare organizations are prohibited from sending patient records, clinical documents, or PHI to external services. ChatGPT and Claude require document uploads to their cloud infrastructure, creating compliance risks. Avalon processes all documents locally, enabling document intelligence without external transmission.

### Avalon Blends Local Inference + Cloud Reasoning

Avalon's hybrid architecture provides the best of both worlds:

- **Local Processing**: Fast, secure, compliant handling of PHI and sensitive queries
- **Cloud Reasoning** (optional): Deep synthesis capabilities for non-PHI research when needed
- **Intelligent Routing**: Automatic selection of the optimal execution engine

Generic AI assistants offer only cloud-based processing, forcing organizations to choose between security and capability.

### Extensible Multi-Agent Pipeline Specialized for Medicine

Avalon's multi-agent architecture is purpose-built for pharmaceutical research:

- **Specialized Agents**: Market Intelligence, Clinical Trials, Patents, Safety & PK/PD, and more
- **Domain Expertise**: Each agent understands pharmaceutical terminology, regulatory context, and industry standards
- **Parallel Execution**: Multiple agents work simultaneously, providing comprehensive coverage
- **Extensibility**: New agents can be added for emerging needs (regulatory analysis, real-world evidence, etc.)

ChatGPT and Claude are general-purpose systems that lack this specialized pharmaceutical intelligence.

### Customizable Data Sources

Avalon integrates with pharmaceutical-specific data sources:

- ClinicalTrials.gov for trial data
- Patent databases for IP analysis
- Internal document repositories
- Custom data sources via API integration

Generic AI assistants cannot access these specialized sources or integrate with internal systems.

### Explainability via Timeline

Avalon provides complete transparency through the Agent Timeline Visualization:

- **Step-by-Step Reasoning**: See exactly how the system arrived at its conclusions
- **Agent Attribution**: Understand which agents contributed which findings
- **Source Tracking**: Verify all sources and citations
- **Audit Trail**: Complete record for compliance and quality assurance

ChatGPT and Claude provide limited visibility into their reasoning processes, making it difficult to verify accuracy or understand how conclusions were reached.

### Additional Advantages

- **No Subscription Costs for Local Processing**: Local inference runs on your infrastructure without per-query fees
- **Offline Capability**: Local processing works without internet connectivity
- **Customization**: Agents can be fine-tuned for organizational needs
- **Regulatory Alignment**: Built with pharmaceutical and healthcare compliance in mind
- **Research-Grade Outputs**: Structured formats optimized for pharmaceutical research workflows

---

## 🔥 SECTION 9 — FUTURE ROADMAP

Avalon is continuously evolving to meet the growing needs of pharmaceutical research and healthcare intelligence. Planned enhancements include:

### Dedicated Models Per Agent

**Current State**: All agents in the prototype share a single local language model (Mistral-7B Q6_K), which enables efficient multi-agent orchestration with minimal infrastructure requirements.

**Future Enhancement**: Each specialized agent will be assigned dedicated language models (one or two models per agent) optimized for its specific domain expertise. This architecture upgrade will provide:

- **Deeper Domain-Specific Reasoning**: Each agent (Market Intelligence, Clinical Trials, Patents, Safety & PK/PD, etc.) will leverage models fine-tuned or optimized for its specific pharmaceutical domain
- **Enhanced Accuracy**: Dedicated models eliminate information cross-contamination between agent tasks, ensuring each agent's outputs are based solely on its specialized knowledge domain
- **Scalable Performance**: Larger models (70B+ parameters) can be deployed per agent for complex reasoning tasks while maintaining on-premises deployment and security
- **Independent Optimization**: Each agent's model can be independently optimized, fine-tuned, or upgraded without affecting other agents in the pipeline

This dedicated model architecture ensures maximum accuracy, prevents information leakage between agent tasks, and enables each agent to deliver deeper, more reliable insights specific to its pharmaceutical domain expertise.

### Real Medical Device Integration

Direct integration with medical devices, laboratory systems, and diagnostic equipment to automatically ingest clinical data, lab results, and device outputs. This integration will enable real-time safety monitoring, automated adverse event detection, and seamless data flow into research workflows.

### EMR/EHR Modules

Native integration with Electronic Medical Records (EMR) and Electronic Health Records (EHR) systems:

- **Secure Data Access**: Read-only access to patient records with proper authorization
- **Clinical Decision Support**: Real-time recommendations based on patient data
- **Population Health Analysis**: Aggregate insights across patient populations
- **Quality Metrics**: Automated quality measure calculation and reporting

### Advanced Reporting Engine

Enhanced report generation capabilities:

- **Interactive Reports**: Web-based reports with drill-down capabilities
- **Custom Templates**: Organization-specific report templates and branding
- **Automated Scheduling**: Scheduled report generation and distribution
- **Multi-Format Export**: Additional formats (PowerPoint, Word, JSON)
- **Collaborative Editing**: Multi-user report editing and commenting

### Real-Time Research Agents

Agents that continuously monitor and update:

- **Clinical Trial Monitoring**: Real-time updates on trial status, enrollment, and results
- **Regulatory Tracking**: Automatic alerts for FDA/EMA approvals, guidance updates, and safety communications
- **Publication Monitoring**: New research paper alerts based on saved queries
- **Market Intelligence**: Continuous competitive landscape updates

### Regulatory Analysis (FDA/EMA)

Dedicated regulatory intelligence agent:

- **Approval Tracking**: Monitor drug approvals, label changes, and regulatory actions
- **Guidance Interpretation**: Analysis of FDA, EMA, and other regulatory guidance documents
- **Compliance Assessment**: Evaluate regulatory compliance for drug development programs
- **Submission Support**: Assistance with regulatory submission preparation

### Additional Planned Features

- **Multi-Language Support**: Analysis and reporting in multiple languages for global pharmaceutical operations
- **Advanced Graph Analytics**: Enhanced expert network analysis with machine learning-based relationship discovery
- **Predictive Analytics**: Forecasting models for market trends, trial outcomes, and competitive dynamics
- **API Ecosystem**: Public APIs for integration with other pharmaceutical research tools
- **Mobile Applications**: Native mobile apps for on-the-go research and clinical decision support
- **Advanced Voice Features**: Enhanced voice commands, multi-language speech recognition, and voice-controlled navigation (building on existing voice implementation)

---

## 🔥 SECTION 9.5 — ADDITIONAL IMPLEMENTED FEATURES

The following features are fully implemented in the current Avalon prototype and provide additional capabilities beyond the core multi-agent pipeline.

### Voice Input & Voice Chat System (Fully Implemented in Prototype)

Avalon includes a premium voice interaction system enabling hands-free pharmaceutical research queries with ChatGPT-style voice recording capabilities.

**Voice Recorder Features:**

- **Real-time Speech Recognition**: Uses Web Speech API with continuous listening and interim results for live transcription
- **Waveform Visualization**: Dynamic audio waveform display showing voice input levels with smooth animations
- **Auto-Stop on Silence**: Intelligent silence detection automatically stops recording after configurable silence duration (default: 2 seconds)
- **Echo Suppression**: Prevents audio feedback and repetition issues during voice input
- **Volume Level Monitoring**: Real-time volume level display using Web Audio API for visual feedback
- **Error Handling**: Graceful handling of microphone access denial and browser compatibility issues

**Voice Chat Modal:**

- **Dedicated Voice Conversation Mode**: Full-screen modal for voice-only pharmaceutical research conversations
- **Automatic Conversation Creation**: Creates new conversation when voice chat begins
- **Text-to-Speech Response**: AI responses can be spoken aloud for hands-free interaction
- **Status Indicators**: Visual feedback showing listening, processing, and speaking states
- **Seamless Integration**: Voice transcripts are automatically submitted as chat messages

**Implementation Location**: `src/components/chat/VoiceRecorder.tsx`, `src/components/chat/WaveformVisualizer.tsx`, `src/components/modals/VoiceChatModal.tsx`

### Data Source RAG System (Fully Implemented in Prototype)

Avalon includes a separate Retrieval-Augmented Generation (RAG) system for custom data sources, enabling organizations to integrate their own pharmaceutical documents and research materials.

**Data Source RAG Architecture:**

- **Local Embedding Model**: Uses `sentence-transformers` (all-MiniLM-L6-v2) for CPU-based embeddings without external API dependencies
- **Document Ingestion Pipeline**: Supports PDF, DOCX, TXT, MD, CSV, and JSON files with automatic text extraction
- **Intelligent Chunking**: Configurable chunk sizes (default: 1000 characters) with overlap for context preservation
- **Category Detection**: Automatic categorization of documents based on content keywords (oncology, cardiology, neurology, diabetes, etc.)
- **Semantic Search**: Cosine similarity-based retrieval of relevant document chunks

**Data Source Categories:**

| Category | Keywords Detected |
|----------|------------------|
| Oncology | cancer, tumor, chemotherapy, immunotherapy, carcinoma |
| Cardiology | heart, cardiac, cardiovascular, hypertension, arrhythmia |
| Neurology | brain, neuron, alzheimer, parkinson, epilepsy, stroke |
| Diabetes | diabetes, insulin, glucose, hba1c, metformin, glp-1 |
| Immunology | immune, antibody, autoimmune, inflammation, cytokine |
| Infectious | infection, antibiotic, viral, bacterial, pathogen |
| Rare Disease | orphan, rare disease, genetic disorder |

**RAG Retrieval Features:**

- **Query-Based Category Detection**: Automatically identifies relevant categories from user queries
- **Source-Specific Retrieval**: Users can restrict search to specific data sources ("use only my oncology data")
- **Hybrid Search**: Combines keyword matching with semantic similarity for improved accuracy
- **Configurable Top-K**: Adjustable number of retrieved chunks (default: 5)
- **MongoDB Storage**: Embeddings and chunks stored in MongoDB for persistence

**Configuration Flags:**

```
DATA_SOURCE_RAG_ENABLED=true/false  # Enable/disable data source RAG
DATA_SOURCE_CHUNK_SIZE=1000         # Characters per chunk
DATA_SOURCE_CHUNK_OVERLAP=100       # Overlap between chunks
DATA_SOURCE_TOP_K=5                 # Number of chunks to retrieve
```

**Implementation Location**: `backend/app/rag/data_sources_ingest.py`, `backend/app/rag/data_sources_embedder.py`, `backend/app/rag/data_sources_retriever.py`

### Projects Management System (Fully Implemented in Prototype)

Avalon provides a comprehensive project management system for organizing pharmaceutical research activities, conversations, and documents.

**Project Features:**

- **Project Creation & Management**: Create, rename, and delete research projects with descriptions
- **Conversation Grouping**: Associate multiple chat conversations with specific research projects
- **Project-Specific File Upload**: Upload and manage documents (PDF, DOCX, TXT) at the project level
- **File Enable/Disable Toggle**: Enable or disable specific files from being used in project context
- **Visual Project Cards**: Color-coded project cards with gradient backgrounds for easy identification
- **Project RAG Integration**: Uploaded project files can be used for retrieval-augmented generation (requires RAG enabled)

**Project File Management:**

- **Drag-and-Drop Upload**: Easy file upload interface with progress indicators
- **File Metadata Display**: Shows file name, size, and upload timestamp
- **File Removal**: Remove files from projects when no longer needed
- **File Status Indicators**: Visual indicators showing file processing status

**Project Navigation:**

- **Expandable Project View**: Collapsible project cards showing associated chats
- **Quick Chat Access**: Click to navigate directly to any project-associated conversation
- **Project Statistics**: Display of chat count and last updated timestamp

**Implementation Location**: `src/pages/Projects.tsx`, `backend/app/routes/projects.py`

### Settings & Customization System (Fully Implemented in Prototype)

Avalon provides extensive customization options through a comprehensive settings interface with multiple configuration categories.

**Settings Categories:**

1. **Agent Customization**:
   - **Agent Persona**: Custom system prompt additions for personalized AI behavior
   - **Response Style**: Configure preferred output format (detailed, concise, technical, etc.)

2. **Focus Areas Configuration**:
   - **Research Focus Areas**: Define therapeutic areas of interest (oncology, cardiology, neurology, etc.)
   - **Custom Focus Areas**: Add custom research focus areas with associated URLs
   - **Link Management**: Add multiple reference links per focus area
   - **File Attachments**: Upload reference files for each focus area
   - **Enable/Disable Toggle**: Toggle individual focus areas on/off

3. **Data Sources Configuration**:
   - **Custom Data Sources**: Define external data source URLs
   - **Source Enable/Disable**: Toggle data sources for selective retrieval
   - **Expert Network Files**: Upload files for expert network analysis
   - **Patent Files**: Upload patent documents for analysis

4. **General Settings**:
   - **Notifications**: Enable/disable system notifications
   - **Auto-Save**: Automatic saving of settings changes

**Settings Persistence:**

- **MongoDB Storage**: Settings stored in MongoDB for persistence across sessions
- **Default User Configuration**: Single-user mode with default settings profile
- **Real-time Updates**: Settings changes apply immediately without restart

**Implementation Location**: `src/pages/Settings.tsx`, `backend/app/routes/settings.py`

### Reports Library & Management (Fully Implemented in Prototype)

Avalon includes a dedicated reports library for managing generated pharmaceutical research reports.

**Reports Features:**

- **Report Listing**: Searchable list of all generated reports with metadata
- **Report Types**: Support for PDF and CSV report formats
- **Report Metadata**: Includes report name, description, query, creation date, and file size
- **Search Functionality**: Filter reports by name, description, or query content
- **Advanced Filters**: Modal-based filtering by date range, report type, and other criteria
- **Report Download**: Direct download links for PDF and CSV reports
- **Mock Reports**: Demo reports available for prototype demonstration

**Report Row Display:**

- **Visual Icons**: Different icons for PDF vs CSV reports
- **File Size Display**: Human-readable file size formatting
- **Creation Date**: Relative time display ("2 days ago")
- **Quick Actions**: View, download, and delete options

**Implementation Location**: `src/pages/Reports.tsx`, `src/components/reports/ReportRow.tsx`, `backend/app/routes/reports.py`

### Admin Dashboard (Fully Implemented in Prototype)

Avalon includes an administrative dashboard for system monitoring and management.

**Admin Features:**

- **System Overview**: High-level statistics and status indicators
- **Usage Metrics**: Query counts, active users, and resource utilization
- **Agent Performance**: Monitoring of individual agent response times and success rates
- **Error Tracking**: View and manage system errors and exceptions
- **Configuration Management**: Administrative settings and feature flags

**Implementation Location**: `src/pages/AdminDashboard.tsx`, `backend/app/routes/admin.py`

### Modal System (Fully Implemented in Prototype)

Avalon includes a comprehensive modal system for various interactive features.

**Available Modals:**

1. **Expert Graph Modal**: Interactive visualization of expert network graphs with zoom, pan, and node selection
2. **PDF Viewer Modal**: In-app PDF document viewing without external downloads
3. **CSV Viewer Modal**: Tabular display of CSV data with sorting and filtering capabilities
4. **Search Chats Modal**: Search across all conversations by content, date, or topic
5. **Group Chat Modal**: Multi-user conversation support (placeholder for future enhancement)
6. **Advanced Filters Modal**: Complex filtering interface for reports and data
7. **Voice Chat Modal**: Dedicated voice interaction interface

**Modal Features:**

- **Responsive Design**: Modals adapt to screen size with proper scrolling
- **Keyboard Navigation**: ESC key closes modals, focus trapping for accessibility
- **Backdrop Click**: Click outside modal to close
- **Animation**: Smooth open/close transitions

**Implementation Location**: `src/components/modals/`

### External API Integrations (Fully Implemented in Prototype)

Avalon integrates with multiple pharmaceutical and biomedical data APIs for real-time information retrieval.

**PubMed Integration:**

- **Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- **Rate Limiting**: Configurable requests per second (default: 3 RPS)
- **Search Capabilities**: Search for publications by keyword, author, or MeSH terms
- **Abstract Retrieval**: Fetch publication abstracts for analysis
- **Citation Information**: Author lists, journal names, and publication dates

**ClinicalTrials.gov Integration:**

- **Base URL**: `https://clinicaltrials.gov/api/query/study_fields`
- **Maximum Records**: Configurable limit per query (default: 40)
- **Cache TTL**: 24-hour caching of trial data
- **Search Fields**: Trial phase, condition, intervention, sponsor, status

**PatentsView Integration:**

- **Base URL**: `https://api.patentsview.org/patents/query`
- **Page Size**: Configurable results per page (default: 20)
- **Cache TTL**: 24-hour caching of patent data
- **API Key Support**: Optional API key for enhanced access
- **Search Fields**: Patent number, assignee, claims, filing date

**Configuration:**

```
PUBMED_BASE_URL=https://eutils.ncbi.nlm.nih.gov/entrez/eutils
PUBMED_RATE_LIMIT_RPS=3
CLINICALTRIALS_BASE_URL=https://clinicaltrials.gov/api/query/study_fields
CLINICALTRIALS_MAX_RECORDS=40
PATENTSVIEW_BASE_URL=https://api.patentsview.org/patents/query
PATENTSVIEW_PAGE_SIZE=20
```

**Implementation Location**: `backend/app/services/pubmed_client.py`, `backend/app/services/clinicaltrials_client.py`, `backend/app/services/patent_client.py`

### Caching & Performance System (Fully Implemented in Prototype)

Avalon includes a comprehensive caching system for optimized performance and reduced API calls.

**Cache Features:**

- **CacheManager**: Centralized cache management with configurable TTL
- **Query Caching**: Cache frequent pharmaceutical queries to reduce LLM calls
- **API Response Caching**: Cache external API responses (PubMed, ClinicalTrials.gov, PatentsView)
- **Configurable Expiration**: Different TTL values for different cache types
- **Memory-Efficient**: Automatic cleanup of expired cache entries

**Cache Configuration:**

```
EXTERNAL_CACHE_TTL=86400          # 24 hours for external APIs
CLINICALTRIALS_CACHE_TTL=86400    # 24 hours for trial data
PATENTSVIEW_CACHE_TTL=86400       # 24 hours for patent data
```

**Implementation Location**: `backend/app/core/cache.py`

### Retry & Error Handling System (Fully Implemented in Prototype)

Avalon includes robust error handling with automatic retry mechanisms for reliability.

**Retry Features:**

- **Retry Decorator**: `retry_llm_call()` decorator for automatic retry on LLM failures
- **Configurable Retries**: Maximum retry attempts configurable (default: 3)
- **Exponential Backoff**: Increasing delay between retry attempts
- **Error Classification**: Different handling for transient vs permanent errors
- **Graceful Degradation**: Fallback responses when retries exhausted

**External Request Handling:**

```
EXTERNAL_REQUEST_TIMEOUT=15       # 15 second timeout
EXTERNAL_MAX_RETRIES=3            # 3 retry attempts
```

**Implementation Location**: `backend/app/core/retry.py`

### Tracing & Debugging System (Fully Implemented in Prototype)

Avalon includes tracing capabilities for debugging and performance monitoring.

**Trace Features:**

- **Request Tracing**: Track requests through the multi-agent pipeline
- **Agent Execution Timing**: Measure individual agent response times
- **Error Tracing**: Capture and log errors with full context
- **Performance Metrics**: Collect timing data for optimization

**Implementation Location**: `backend/app/core/trace.py`

### Source Verification System (Fully Implemented in Prototype)

Avalon includes source verification helpers to validate and verify research sources.

**Verification Features:**

- **Source Validation**: Verify URLs and citations are accessible
- **Claim Verification**: Propose verification checks for claims made by agents
- **Citation Tracking**: Track source usage across agent responses
- **Quality Assessment**: Evaluate source reliability and relevance

**Implementation Location**: `backend/app/agents/helpers/verification.py`

### Schema Enforcement System (Fully Implemented in Prototype)

Avalon enforces strict output schemas for consistent agent responses.

**Schema Enforcer Features:**

- **Output Validation**: Validate agent outputs against predefined schemas
- **Format Correction**: Automatically correct minor formatting issues
- **Error Reporting**: Clear error messages for schema violations
- **Flexible Schemas**: Support for multiple output formats (JSON, Markdown, tables)

**Implementation Location**: `backend/app/agents/workers/schema_enforcer.py`

### Outline Expander Agent (Fully Implemented in Prototype)

Avalon includes an outline expander agent for generating detailed content from research outlines.

**Outline Expander Features:**

- **Outline Parsing**: Parse and understand research outlines and structures
- **Content Generation**: Expand outline points into detailed paragraphs
- **Section Organization**: Maintain logical section hierarchy
- **Citation Integration**: Include relevant citations in expanded content

**Implementation Location**: `backend/app/agents/workers/outline_expander.py`

### Report Generator Agent (Fully Implemented in Prototype)

A specialized worker agent for generating formatted research reports.

**Report Generator Features:**

- **Multi-Format Output**: Generate PDF and CSV formats
- **Executive Summary**: Automatic summary generation from agent findings
- **Section Compilation**: Organize agent outputs into report sections
- **Table Extraction**: Extract and format tables from agent responses
- **Citation Compilation**: Collect and format all citations

**Implementation Location**: `backend/app/agents/workers/report_generator_agent.py`

### Timeline Events System (Fully Implemented in Prototype)

Avalon tracks agent activities through a comprehensive timeline events system with hospital-grade audit capabilities.

**Timeline Event Categories:**

| Category | Event Types |
|----------|-------------|
| **Agent Lifecycle** | AGENT_START, AGENT_PROGRESS, AGENT_COMPLETE, AGENT_ERROR |
| **Orchestration** | DECOMPOSITION_START, DECOMPOSITION_COMPLETE, SYNTHESIS_START, SYNTHESIS_COMPLETE |
| **Mode Classification** | MODE_SIMPLE, MODE_RESEARCH, MODE_TABLE, MODE_DOCUMENT, MODE_SAFETY, MODE_PATIENT, MODE_EXPERT |
| **PHI & Security** | PHI_DETECTED, PHI_ROUTING, LOCAL_ONLY_ENFORCED, CLOUD_BLOCKED |
| **Document Processing** | DOCUMENT_UPLOAD, DOCUMENT_EXTRACTION, DOCUMENT_PHI_SCAN, DOCUMENT_ANALYSIS |
| **LLM Routing** | LLM_ROUTING, LLM_LOCAL_CALL, LLM_LOCAL_RESPONSE, LLM_ERROR, LLM_FALLBACK |
| **Report Generation** | REPORT_GENERATION_START, REPORT_GENERATION_COMPLETE |
| **Error Handling** | ERROR, FALLBACK, GRACEFUL_DEGRADATION |

**Timeline Event Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TIMELINE EVENT SEQUENCE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ──► {"type": "thinking", "message": "PHI detected → Local Model"}       │
│  2. ──► {"type": "routing", "mode": "local", "detected_mode": "safety"}     │
│  3. ──► {"event": "phi_detected", "agent": "security", "message": "⚠️..."}  │
│  4. ──► {"event": "mode_safety", "agent": "master", "message": "🔍..."}     │
│  5. ──► {"event": "llm_routing", "agent": "master", "message": "🖥️..."}    │
│  6. ──► {"event": "agent_start", "agent": "safety_pkpd", "message": "..."}  │
│  7. ──► {"event": "agent_progress", "agent": "safety_pkpd", "message": "..."}│
│  8. ──► {"event": "agent_complete", "agent": "safety_pkpd", "message": "..."}│
│  9. ──► {"event": "synthesis_start", "agent": "master", "message": "..."}   │
│ 10. ──► {"type": "token", "delta": "..."} ... token streaming               │
│ 11. ──► {"event": "synthesis_complete", "agent": "master"}                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Timeline Features:**

- **Real-time Streaming**: Timeline events stream to frontend via SSE during processing
- **PHI Audit Trail**: All PHI detection and routing decisions logged for compliance
- **Agent Display Names**: Human-readable agent names for the UI
- **Status Tracking**: Pending, running, completed, or failed status per agent
- **Timestamps**: Automatic ISO timestamp on all events
- **Metadata Support**: Optional metadata attached to events for debugging

**Frontend AgentTimeline Component:**

The `AgentTimeline.tsx` component provides visual representation with:
- Color-coded status indicators (running: blue, completed: green, pending: gray, error: red)
- Agent-specific icons (market, clinical, patents, safety, expert, security, etc.)
- Collapsible timeline view
- Real-time status updates during streaming

**Implementation Location**: `backend/app/agents/timeline_events.py`, `src/components/chat/AgentTimeline.tsx`

### UI Component Library (Fully Implemented in Prototype)

Avalon includes a comprehensive UI component library based on shadcn/ui with custom enhancements.

**Available Components:**

| Component | Description |
|-----------|-------------|
| Badge | Status indicators and labels |
| Button | Action buttons with variants |
| Card | Content containers with headers |
| Collapsible | Expandable/collapsible sections |
| Dialog | Modal dialog windows |
| DropdownMenu | Context menus and dropdowns |
| Input | Text input fields |
| Label | Form labels |
| ScrollArea | Scrollable containers |
| Select | Dropdown selection |
| Switch | Toggle switches |
| Table | Data tables |
| Tabs | Tabbed interfaces |
| Textarea | Multi-line text input |

**Design System:**

- **Dark Theme**: Enterprise-grade dark theme matching ChatGPT Teams aesthetics
- **Glass Morphism**: Backdrop blur effects for modern appearance
- **Responsive Design**: Mobile-first responsive layouts
- **Accessibility**: ARIA labels and keyboard navigation support

**Implementation Location**: `src/components/ui/`

### Streaming Message System (Fully Implemented in Prototype)

Avalon implements real-time streaming for AI responses with specialized components.

**Streaming Components:**

1. **ThinkingPanel**: Displays PHI detection and routing decisions before streaming starts
2. **StreamingMessageBubble**: Displays streaming text with cursor animation
3. **ThinkingIndicator**: Shows AI processing state with animated dots
4. **RawOutputBox**: Displays raw agent output for debugging

**ThinkingPanel Features:**
- Animated pulsing dots header ("Avalon is Thinking…")
- PHI/No-PHI icon with yellow/green color coding
- Local/Cloud badge indicator
- Mode activation message (Research, Safety, Table, etc.)
- Animated loading bar with CSS animations
- Automatically hides when first token arrives

**Streaming Features:**

- **Token-by-Token Display**: Text appears character by character for natural feel
- **Cursor Animation**: Blinking cursor indicates active streaming
- **Throttled Scrolling**: Prevents jittery scrolling during fast updates
- **Abort Capability**: Cancel ongoing requests with AbortController

**SSE Event Types Handled:**
| Event Type | Purpose |
|------------|---------|
| `thinking` | PHI detection routing message (first event) |
| `routing` | Mode and routing decision details |
| `timeline` | Agent lifecycle and orchestration events |
| `data_source_used` | Data Source RAG indicator |
| `token` | Streaming response tokens |
| `report_ready` | Report generation signal |
| `final` | Stream completion with message ID |

**Implementation Location**: `src/components/chat/ThinkingPanel.tsx`, `src/components/chat/StreamingMessageBubble.tsx`, `src/components/chat/ThinkingIndicator.tsx`, `src/components/chat/RawOutputBox.tsx`

### Multi-Agent View Renderers (Fully Implemented in Prototype)

Avalon includes specialized view components for each agent's output.

**Agent-Specific Views:**

| Agent View | Features |
|------------|----------|
| MarketAgentView | Market size charts, competitor tables, trend indicators |
| ClinicalTrialsAgentView | Trial listings, phase distributions, endpoint tables |
| PatentsAgentView | Patent families, expiration timelines, claim summaries |
| InternalDocsAgentView | Document excerpts, key findings, relevance scores |
| WebEvidenceAgentView | Source cards, publication summaries, guideline highlights |
| UnmetNeedsAgentView | Gap analysis, opportunity identification |
| ExpertGraphViewer | Interactive network visualization with D3.js |
| TimelineView | Step-by-step agent execution timeline |

**MultiAgentRenderer:**

- **Automatic View Selection**: Chooses appropriate view based on agent type
- **Collapsible Sections**: Expand/collapse individual agent outputs
- **Unified Styling**: Consistent appearance across all agent views

**Implementation Location**: `src/components/chat/agents/`

### Project RAG Feature Flags (Fully Implemented in Prototype)

Avalon includes comprehensive feature flags for controlling RAG capabilities.

**Project RAG Flags:**

```
ENABLE_PROJECT_RAG=true/false     # Enable project-level RAG
ENABLE_LINK_FETCH=true/false      # Enable fetching URLs for RAG
ENABLE_WEB_SCRAPING=true/false    # Enable web scraping for RAG
```

**Project RAG Configuration:**

```
RAG_CHUNK_SIZE=350                # Tokens per chunk
RAG_CHUNK_OVERLAP=50              # Overlap between chunks
RAG_TOP_K=5                       # Top chunks to retrieve
PROJECT_FILES_DIR=project_files   # Storage directory
```

**LM Studio Embedding:**

```
LMSTUDIO_EMBEDDING_URL=http://localhost:1234/v1/embeddings
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
```

**Note**: Project RAG features require larger models (≥14B/70B parameters) for safe operation in healthcare contexts and are disabled by default.

**Implementation Location**: `backend/app/config.py`, `backend/app/services/rag/`

### MongoDB Collections (Fully Implemented in Prototype)

Avalon uses MongoDB for persistent storage with the following collection structure.

**Collections:**

| Collection | Purpose |
|------------|---------|
| conversations | Chat conversations with messages |
| projects | Research project definitions |
| project_files | Files uploaded to projects |
| project_links | Links associated with projects |
| reports | Generated PDF/CSV reports |
| settings | User/system settings |
| internal_docs | Uploaded documents for analysis |
| project_embeddings | RAG embeddings for project files |
| expert_graphs | Expert network graph data |
| data_source_chunks | Data source RAG chunks |

**Database Configuration:**

```
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=pharma_ai_db
```

**Note**: Avalon uses only local MongoDB—no cloud database connections.

---

## 🔥 SECTION 10 — FINAL SUMMARY STATEMENT

**Avalon** is a modular, secure, clinical-grade AI platform designed to bring deep pharmaceutical intelligence into hospitals and research environments while preserving patient confidentiality and delivering multi-agent reasoning at scale.

Avalon transforms how pharmaceutical companies, clinical researchers, and healthcare institutions access and utilize medical knowledge. By combining specialized multi-agent intelligence with enterprise-grade security, Avalon enables organizations to leverage AI capabilities without compromising patient privacy or regulatory compliance.

### Key Platform Capabilities

| Capability | Implementation Status |
|------------|----------------------|
| Multi-Agent Intelligence (9 specialized agents) | ✅ Fully Implemented |
| PHI Detection (HIPAA 18 identifiers) | ✅ Fully Implemented |
| Thinking Panel (Real-time routing display) | ✅ Fully Implemented |
| 7-Mode Auto Classification | ✅ Fully Implemented |
| Timeline Events (Hospital-grade audit) | ✅ Fully Implemented |
| Voice-Enabled Research | ✅ Fully Implemented |
| Data Source RAG (Local embeddings) | ✅ Fully Implemented |
| Project Management System | ✅ Fully Implemented |
| Real-time Streaming (SSE) | ✅ Fully Implemented |
| Expert Network Graphs | ✅ Fully Implemented |
| Document Intelligence | ✅ Fully Implemented |
| Report Generation (PDF/CSV) | ⚡ Partially Implemented |
| Cloud LLM Integration | ⚡ Optional/Future |

The platform's local-first architecture ensures that sensitive patient data never leaves your network, while its optional cloud reasoning capabilities provide powerful analysis for non-PHI research questions. The multi-agent pipeline delivers comprehensive insights across market intelligence, clinical trials, patents, safety analysis, and regulatory intelligence—all orchestrated by a master agent that understands pharmaceutical research workflows.

### Complete Feature Set

With real-time streaming outputs, **Thinking Panel** for transparent routing decisions, agent timeline visualization, expert network graphs, automated report generation, voice-enabled research with waveform visualization, dual RAG architecture (Project RAG + Data Source RAG), and seamless document intelligence, Avalon provides a complete research intelligence platform.

The system's **intelligent 7-mode classification** (Patient, Safety, Research, Table, Document, Expert, Simple) automatically adapts to different query types—from simple informational questions to comprehensive research analyses to patient-specific safety checks. **Hospital-grade PHI detection** ensures all HIPAA 18 identifiers are caught and routed to local processing. Project management capabilities enable organized research workflows with dedicated document storage and conversation grouping.

Avalon represents the future of pharmaceutical AI: specialized, secure, and scalable. It bridges the gap between the need for powerful AI capabilities and the requirement for absolute data security, enabling organizations to unlock the full potential of AI-driven pharmaceutical research while maintaining the highest standards of privacy and compliance.

---

_Avalon: Transforming Pharmaceutical Intelligence Through Secure AI_
