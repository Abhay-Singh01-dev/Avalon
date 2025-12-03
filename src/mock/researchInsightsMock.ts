export const mockResearchInsights = [
  {
    section: "Market Insights",
    keyFindings: [
      "Growing demand in metabolic disorders (mock)",
      "New entrants expected (mock)",
      "Reimbursement landscape improving",
      "Competition moderate in major markets"
    ],
    depth: "High",
    visualization: true,
    links: [
      { label: "Source 1", url: "https://example.com" },
      { label: "Source 2", url: "https://example.com" }
    ],
    status: "Complete"
  },
  {
    section: "Clinical Trials",
    keyFindings: [
      "Multiple Phase II/III trials active",
      "Promising safety profile so far",
      "Endpoints well-aligned with guidelines",
      "Strong sponsor representation"
    ],
    depth: "High",
    visualization: true,
    links: [{ label: "ClinicalTrials.gov", url: "https://clinicaltrials.gov" }],
    status: "Complete"
  },
  {
    section: "Patents",
    keyFindings: [
      "Several filings in last 24 months",
      "Mechanistic claims observed",
      "Delivery system patents still active"
    ],
    depth: "Medium",
    visualization: true,
    links: [{ label: "USPTO", url: "https://uspto.gov" }],
    status: "Complete"
  },
  {
    section: "Unmet Needs",
    keyFindings: [
      "Therapy gaps in resistant patients",
      "Need for improved adherence",
      "Limited data for special populations",
      "Access barriers in developing regions"
    ],
    depth: "High",
    visualization: false,
    links: [{ label: "Source 1", url: "https://example.com" }],
    status: "Complete"
  },
  {
    section: "Web Documents",
    keyFindings: [
      "Recent guidelines published (mock)",
      "New reviews summarizing MoA",
      "Industry reports show adoption trends"
    ],
    depth: "Medium",
    visualization: false,
    links: [
      { label: "FDA", url: "https://fda.gov" },
      { label: "EMA", url: "https://ema.europa.eu" }
    ],
    status: "Complete"
  },
  {
    section: "Internal Documents",
    keyFindings: [
      "Previous analysis reports available",
      "Internal market assessments",
      "Competitive intelligence summaries"
    ],
    depth: "Medium",
    visualization: false,
    links: [{ label: "Internal DB", url: "#" }],
    status: "Complete"
  },
  {
    section: "Expert Network",
    keyFindings: [
      "Top researchers identified",
      "KOL clusters around major centers",
      "Strong institutional collaboration",
      "Mind-map graph available"
    ],
    depth: "Low",
    visualization: true, // MUST open graph modal
    links: [{ label: "Source 1", url: "https://example.com" }],
    status: "Complete",
    graphId: "mock-expert-network" // used by View button
  }
];

export type ResearchInsight = typeof mockResearchInsights[number];
