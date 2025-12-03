import React from "react";
import { Calendar, Clock } from "lucide-react";
import AgentSection from "./AgentSection";

type TimelineItem = {
  date?: string;
  event?: string;
  description?: string;
  milestone?: string;
  status?: string;
};

type TimelineData = {
  timeline?: TimelineItem[];
  milestones?: TimelineItem[];
};

export default function TimelineView({ data }: { data: TimelineData }) {
  const timeline = data.timeline || data.milestones || [];

  const getStatusColor = (status?: string) => {
    if (!status) return "bg-gray-500/20 text-gray-400";
    const s = status.toLowerCase();
    if (s.includes("completed") || s.includes("done")) return "bg-green-500/20 text-green-400";
    if (s.includes("in progress") || s.includes("ongoing")) return "bg-blue-500/20 text-blue-400";
    if (s.includes("upcoming") || s.includes("planned")) return "bg-yellow-500/20 text-yellow-400";
    return "bg-gray-500/20 text-gray-400";
  };

  if (timeline.length === 0) {
    return null;
  }

  return (
    <AgentSection
      title="Timeline"
      icon={<Calendar className="w-5 h-5" />}
      summary={`${timeline.length} timeline event${timeline.length !== 1 ? "s" : ""}`}
      color="purple"
    >
      <div className="space-y-4">
        <div className="relative">
          {/* Timeline Line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-800"></div>

          {/* Timeline Items */}
          <div className="space-y-6">
            {timeline.map((item, idx) => (
              <div key={idx} className="relative flex items-start gap-4">
                {/* Timeline Dot */}
                <div className="relative z-10 flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 border-2 border-purple-500/50 flex items-center justify-center">
                    <Clock className="w-4 h-4 text-purple-400" />
                  </div>
                </div>

                {/* Timeline Content */}
                <div className="flex-1 bg-gray-800/30 rounded-lg p-3 border border-gray-800">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex-1">
                      <h5 className="text-sm font-semibold text-white mb-1">
                        {item.event || item.milestone || `Event ${idx + 1}`}
                      </h5>
                      {item.description && (
                        <p className="text-xs text-gray-400 mb-2">{item.description}</p>
                      )}
                    </div>
                    {item.status && (
                      <span className={`px-2 py-1 rounded text-xs ${getStatusColor(item.status)}`}>
                        {item.status}
                      </span>
                    )}
                  </div>
                  {item.date && (
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Calendar className="w-3 h-3" />
                      <span>{item.date}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AgentSection>
  );
}

