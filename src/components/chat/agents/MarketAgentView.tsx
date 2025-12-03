import React from "react";
import { TrendingUp, DollarSign, BarChart3 } from "lucide-react";
import AgentSection from "./AgentSection";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type MarketAgentData = {
  section: string;
  summary: string;
  details?: {
    market_size?: string;
    cagr?: string;
    key_players?: string[];
    growth_drivers?: string[];
    market_segments?: Array<{
      segment?: string;
      size?: string;
      growth?: string;
    }>;
    competitive_landscape?: Array<{
      company?: string;
      market_share?: string;
      products?: string[];
    }>;
    [key: string]: any;
  };
  confidence?: number;
  sources?: string[];
};

export default function MarketAgentView({ worker }: { worker: MarketAgentData }) {
  const details = worker.details || {};
  const marketSize = details.market_size;
  const cagr = details.cagr;
  const keyPlayers = details.key_players || [];
  const growthDrivers = details.growth_drivers || [];
  const marketSegments = details.market_segments || [];
  const competitiveLandscape = details.competitive_landscape || [];

  return (
    <AgentSection
      title="Market Analysis"
      icon={<TrendingUp className="w-5 h-5" />}
      summary={worker.summary}
      confidence={worker.confidence}
      sources={worker.sources}
      color="green"
    >
      <div className="space-y-4">
        {/* Market Size & CAGR */}
        {(marketSize || cagr) && (
          <div className="grid grid-cols-2 gap-4">
            {marketSize && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="w-4 h-4 text-green-400" />
                  <span className="text-xs text-gray-500 uppercase">Market Size</span>
                </div>
                <p className="text-sm font-semibold text-white">{marketSize}</p>
              </div>
            )}
            {cagr && (
              <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                  <span className="text-xs text-gray-500 uppercase">CAGR</span>
                </div>
                <p className="text-sm font-semibold text-white">{cagr}</p>
              </div>
            )}
          </div>
        )}

        {/* Market Segments Table */}
        {marketSegments.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Market Segments
            </h4>
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-800/50 border-gray-800">
                    <TableHead className="text-gray-300 text-xs">Segment</TableHead>
                    <TableHead className="text-gray-300 text-xs">Size</TableHead>
                    <TableHead className="text-gray-300 text-xs">Growth</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {marketSegments.map((segment, idx) => (
                    <TableRow key={idx} className="border-gray-800 hover:bg-gray-800/30">
                      <TableCell className="text-gray-300 text-xs">
                        {segment.segment || "N/A"}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {segment.size || "N/A"}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {segment.growth || "N/A"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* Competitive Landscape Table */}
        {competitiveLandscape.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Competitive Landscape
            </h4>
            <div className="border border-gray-800 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-800/50 border-gray-800">
                    <TableHead className="text-gray-300 text-xs">Company</TableHead>
                    <TableHead className="text-gray-300 text-xs">Market Share</TableHead>
                    <TableHead className="text-gray-300 text-xs">Products</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {competitiveLandscape.map((company, idx) => (
                    <TableRow key={idx} className="border-gray-800 hover:bg-gray-800/30">
                      <TableCell className="text-gray-300 text-xs">
                        {company.company || "N/A"}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {company.market_share || "N/A"}
                      </TableCell>
                      <TableCell className="text-gray-300 text-xs">
                        {company.products?.join(", ") || "N/A"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* Key Players */}
        {keyPlayers.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Key Players
            </h4>
            <div className="flex flex-wrap gap-2">
              {keyPlayers.map((player, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-gray-800/50 border border-gray-700 rounded text-xs text-gray-300"
                >
                  {player}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Growth Drivers */}
        {growthDrivers.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Growth Drivers
            </h4>
            <ul className="space-y-1">
              {growthDrivers.map((driver, idx) => (
                <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-green-400 mt-1">•</span>
                  <span>{driver}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Other Details */}
        {Object.keys(details).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Additional Insights
            </h4>
            <div className="text-sm text-gray-300 space-y-1">
              {Object.entries(details).map(([key, value]) => {
                if (
                  ["market_size", "cagr", "key_players", "growth_drivers", "market_segments", "competitive_landscape"].includes(key)
                ) {
                  return null;
                }
                if (typeof value === "string") {
                  return (
                    <div key={key}>
                      <span className="text-gray-500 capitalize">{key.replace(/_/g, " ")}:</span>{" "}
                      <span>{value}</span>
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </div>
        )}
      </div>
    </AgentSection>
  );
}

