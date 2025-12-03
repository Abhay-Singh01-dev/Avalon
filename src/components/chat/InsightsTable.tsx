import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ExternalLink,
  CheckCircle2,
  Loader2,
  BarChart3,
  Download,
  Maximize2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function InsightsTable({ data }) {
  const [selectedChart, setSelectedChart] = React.useState(null);

  // Charts should come from backend data in row.chart_url or row.chart_data
  // If not available, chart feature is disabled
  const getChartUrl = (row) => {
    return row.chart_url || row.chart_data || null;
  };

  const downloadChart = (row) => {
    const chartUrl = getChartUrl(row);
    if (!chartUrl) return;
    
    const link = document.createElement("a");
    link.href = chartUrl;
    link.download = `${row.section.replace(/\s+/g, "_")}_chart.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getDepthColor = (depth) => {
    switch (depth?.toLowerCase()) {
      case "high":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "medium":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "low":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const getStatusIcon = (status) => {
    if (status?.toLowerCase() === "complete") {
      return <CheckCircle2 className="w-4 h-4 text-green-400" />;
    }
    return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
  };

  return (
    <Card className="bg-gray-900/50 border-gray-800 p-6 mt-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white mb-1">
          Research Insights
        </h3>
        <p className="text-sm text-gray-500">
          Comprehensive analysis across key dimensions
        </p>
      </div>

      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-gray-800 hover:bg-gray-800/30">
              <TableHead className="text-gray-400 font-semibold">
                Section
              </TableHead>
              <TableHead className="text-gray-400 font-semibold">
                Key Findings
              </TableHead>
              <TableHead className="text-gray-400 font-semibold">
                Depth
              </TableHead>
              <TableHead className="text-gray-400 font-semibold">
                Visualization
              </TableHead>
              <TableHead className="text-gray-400 font-semibold">
                Links
              </TableHead>
              <TableHead className="text-gray-400 font-semibold">
                Status
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, index) => (
              <TableRow
                key={index}
                className="border-gray-800 hover:bg-gray-800/30 transition-colors"
              >
                <TableCell className="font-medium text-cyan-400">
                  {row.section}
                </TableCell>
                <TableCell>
                  <ul className="space-y-1 text-sm text-gray-300">
                    {row.findings.map((finding, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {finding}
                      </li>
                    ))}
                  </ul>
                </TableCell>
                <TableCell>
                  <Badge className={`${getDepthColor(row.depth)} border`}>
                    {row.depth}
                  </Badge>
                </TableCell>
                <TableCell>
                  {getChartUrl(row) ? (
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setSelectedChart({
                            section: row.section,
                            image: getChartUrl(row),
                          })
                        }
                        className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                      >
                        <BarChart3 className="w-4 h-4 mr-1" />
                        View
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => downloadChart(row)}
                        className="text-gray-400 hover:text-gray-300 hover:bg-gray-800/50"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-600">No chart available</span>
                  )}
                </TableCell>
                <TableCell>
                  {row.links && row.links.length > 0 && (
                    <div className="flex flex-col gap-1">
                      {row.links.slice(0, 2).map((link, idx) => (
                        <a
                          key={idx}
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" />
                          Source {idx + 1}
                        </a>
                      ))}
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(row.status)}
                    <span className="text-sm text-gray-400">{row.status}</span>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Card />

      {/* Chart Viewer Modal */}
      <Dialog
        open={!!selectedChart}
        onOpenChange={() => setSelectedChart(null)}
      >
        <DialogContent className="bg-gray-900 border-gray-800 max-w-3xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              {selectedChart?.section} - Data Visualization
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            <div className="bg-white rounded-lg p-6">
              <img
                src={selectedChart?.image}
                alt={`${selectedChart?.section} chart`}
                className="w-full h-auto"
              />
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button
                onClick={() => downloadChart(selectedChart?.section)}
                className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
              >
                <Download className="w-4 h-4 mr-2" />
                Export as Image
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
