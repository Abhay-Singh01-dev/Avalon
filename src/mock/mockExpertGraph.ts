export const mockExpertGraph = {
  nodes: [
    { id: "Dr. A", group: "expert", label: "Dr. A - Lead Researcher" },
    { id: "Dr. B", group: "expert", label: "Dr. B - Clinical Specialist" },
    { id: "Dr. C", group: "expert", label: "Dr. C - Trial Investigator" },
    { id: "Dr. D", group: "expert", label: "Dr. D - KOL" },
    { id: "Institute X", group: "institution", label: "Harvard Medical Center" },
    { id: "Institute Y", group: "institution", label: "Johns Hopkins" },
    { id: "Trial Y", group: "trial", label: "NCT00123456" },
    { id: "Trial Z", group: "trial", label: "NCT00789012" },
    { id: "Paper Z", group: "paper", label: "Nature Medicine 2024" },
    { id: "Paper W", group: "paper", label: "NEJM Review 2023" }
  ],
  edges: [
    { source: "Dr. A", target: "Institute X" },
    { source: "Dr. B", target: "Institute X" },
    { source: "Dr. A", target: "Paper Z" },
    { source: "Dr. C", target: "Trial Y" },
    { source: "Trial Y", target: "Institute X" },
    { source: "Dr. D", target: "Institute Y" },
    { source: "Dr. D", target: "Paper W" },
    { source: "Dr. B", target: "Trial Z" },
    { source: "Trial Z", target: "Institute Y" },
    { source: "Paper Z", target: "Paper W" },
    { source: "Dr. A", target: "Dr. D" },
    { source: "Institute X", target: "Institute Y" }
  ],
  meta: {
    title: "Expert Network (Mock)",
    description: "NotebookLM-style mind map for prototype - Shows KOL relationships, institutional affiliations, and research collaborations"
  }
};

export type MockExpertGraphType = typeof mockExpertGraph;
