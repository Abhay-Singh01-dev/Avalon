import React, { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, FileText, Filter } from "lucide-react";
import ReportRow from "@/components/reports/ReportRow";
import AdvancedFiltersModal from "@/components/modals/AdvancedFiltersModal";
import { useAppContext } from "@/context/AppContext";

export default function ReportsPage() {
  const { reports, loading, refreshAll } = useAppContext();
  const [searchQuery, setSearchQuery] = useState("");
  const [filtersModalOpen, setFiltersModalOpen] = useState(false);

  // MOCK REPORTS: Inject demo reports for prototype/demo purposes
  const mockReports = React.useMemo(
    () => [
      // PDF Reports
      {
        id: "mock-report-001",
        name: "Sample Market & Clinical Analysis",
        about:
          "Comprehensive pharmaceutical market analysis with clinical trial landscape",
        query: "market analysis + clinical trials + competitive intelligence",
        type: "pdf" as const,
        created_at: new Date().toISOString(),
        file_url: "/mock_reports/sample.pdf",
        isMock: true,
      },
      {
        id: "mock-report-002",
        name: "Oncology Drug Development Report",
        about:
          "Analysis of emerging oncology therapeutics and immunotherapy trends in cancer treatment",
        query: "oncology + immunotherapy + cancer drug pipeline",
        type: "pdf" as const,
        created_at: new Date(
          Date.now() - 2 * 24 * 60 * 60 * 1000
        ).toISOString(),
        file_url: "/mock_reports/oncology_report.pdf",
        isMock: true,
      },
      {
        id: "mock-report-003",
        name: "GLP-1 Agonist Market Assessment",
        about:
          "Competitive landscape of GLP-1 receptor agonists for diabetes and obesity treatment",
        query: "GLP-1 + semaglutide + tirzepatide + obesity market",
        type: "pdf" as const,
        created_at: new Date(
          Date.now() - 5 * 24 * 60 * 60 * 1000
        ).toISOString(),
        file_url: "/mock_reports/glp1_market.pdf",
        isMock: true,
      },
      // CSV Reports
      {
        id: "mock-csv-001",
        name: "Clinical Trials Pipeline Data",
        about:
          "Active clinical trials across therapeutic areas with phase, endpoints, and success rates",
        query: "clinical trials + pipeline + phase 3 + endpoints",
        type: "csv" as const,
        created_at: new Date(
          Date.now() - 1 * 24 * 60 * 60 * 1000
        ).toISOString(),
        file_url: "/mock_reports/clinical_trials_pipeline.csv",
        isMock: true,
      },
      {
        id: "mock-csv-002",
        name: "Drug Safety & Adverse Events Analysis",
        about:
          "Pharmacovigilance data on adverse events, severity, and patient outcomes",
        query: "drug safety + adverse events + pharmacovigilance",
        type: "csv" as const,
        created_at: new Date(
          Date.now() - 3 * 24 * 60 * 60 * 1000
        ).toISOString(),
        file_url: "/mock_reports/drug_safety_analysis.csv",
        isMock: true,
      },
      {
        id: "mock-csv-003",
        name: "Pharmaceutical Market Forecast 2024-2028",
        about:
          "Market size, growth rates, and competitive analysis across therapeutic areas",
        query: "market size + pharma forecast + therapeutic areas",
        type: "csv" as const,
        created_at: new Date(
          Date.now() - 7 * 24 * 60 * 60 * 1000
        ).toISOString(),
        file_url: "/mock_reports/pharma_market_analysis.csv",
        isMock: true,
      },
    ],
    []
  );

  // Combine real reports with mock reports - always show mock reports
  const allReports = React.useMemo(() => {
    // Always include mock reports along with real reports
    return [...mockReports, ...reports];
  }, [reports, mockReports]);
  const [appliedFilters, setAppliedFilters] = useState({
    name: "",
    about: "",
    dateFrom: "",
    dateTo: "",
  });

  const handleDeleteReport = async (reportId: string) => {
    // Don't delete mock reports
    if (reportId.startsWith("mock-")) {
      console.log("[Reports] Cannot delete mock report");
      return;
    }
    console.log("[Reports] Deleting report:", reportId);
    // Refresh reports list after deletion
    await refreshAll();
    console.log("[Reports] Reports list refreshed");
  };

  const applyAdvancedFilters = (filters: {
    name: string;
    about: string;
    dateFrom: string;
    dateTo: string;
  }) => {
    setAppliedFilters(filters);
  };

  const filteredReports = allReports.filter((report) => {
    // Search query filter
    const matchesSearch =
      report.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.about?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.query?.toLowerCase().includes(searchQuery.toLowerCase());

    // Advanced filters
    const matchesName =
      !appliedFilters.name ||
      report.name.toLowerCase().includes(appliedFilters.name.toLowerCase());

    const matchesAbout =
      !appliedFilters.about ||
      report.about?.toLowerCase().includes(appliedFilters.about.toLowerCase());

    const matchesDateFrom =
      !appliedFilters.dateFrom ||
      (report.created_at &&
        new Date(report.created_at) >= new Date(appliedFilters.dateFrom));

    const matchesDateTo =
      !appliedFilters.dateTo ||
      (report.created_at &&
        new Date(report.created_at) <= new Date(appliedFilters.dateTo));

    return (
      matchesSearch &&
      matchesName &&
      matchesAbout &&
      matchesDateFrom &&
      matchesDateTo
    );
  });

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-950 via-black to-gray-950">
      {/* Header */}
      <div className="border-b border-gray-800/30 bg-gradient-to-r from-gray-950/80 via-black/50 to-gray-950/80 backdrop-blur-sm">
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  Reports Library
                </h1>
                <p className="text-gray-500">
                  Access and manage your research reports
                </p>
              </div>
              <Button
                onClick={() => setFiltersModalOpen(true)}
                className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 shadow-lg shadow-blue-500/20"
              >
                <Filter className="w-4 h-4 mr-2" />
                Advanced Filters
              </Button>
            </div>

            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search reports by name, topic, or query..."
                className="w-full pl-12 bg-gray-900/50 border-gray-800 text-gray-200 placeholder:text-gray-600 h-12 focus-visible:ring-blue-500/50"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6">
          <Card className="bg-gray-900/40 border-gray-800/50 overflow-hidden shadow-lg shadow-black/30 rounded-xl">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-gray-800/50 bg-gray-800/30">
              <div className="col-span-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Report Details
              </div>
              <div className="col-span-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Query
              </div>
              <div className="col-span-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Date
              </div>
              <div className="col-span-4 text-xs font-semibold text-gray-400 uppercase tracking-wider text-right">
                Actions
              </div>
            </div>

            {/* Table Body */}
            <div>
              {loading ? (
                <div className="text-center py-20">
                  <FileText className="w-12 h-12 text-gray-700 mx-auto mb-4 animate-pulse" />
                  <p className="text-gray-500">Loading reports...</p>
                </div>
              ) : filteredReports.length > 0 ? (
                filteredReports.map((report) => (
                  <ReportRow
                    key={report.id}
                    report={report}
                    onDelete={handleDeleteReport}
                  />
                ))
              ) : (
                <div className="text-center py-20">
                  <FileText className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <p className="text-lg font-medium text-gray-400 mb-2">
                    No reports yet
                  </p>
                  <p className="text-sm text-gray-600">
                    Generate your first report to see it here
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Advanced Filters Modal */}
      <AdvancedFiltersModal
        isOpen={filtersModalOpen}
        onClose={() => setFiltersModalOpen(false)}
        onApplyFilters={applyAdvancedFilters}
      />
    </div>
  );
}
