import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, MessageSquare, Shield } from "lucide-react";
import { api } from "@/lib/api";

export default function AdminDashboard() {
  const [stats, setStats] = React.useState<{
    conversations: number;
    messages: number;
    projects: number;
    reports: number;
    status: string;
  } | null>(null);
  const [loading, setLoading] = React.useState(false);

  // Fetch application statistics
  React.useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const response = await api.admin.getStats();
        setStats(response);
      } catch (error) {
        console.error("Error fetching admin stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-950 via-black to-gray-950 overflow-auto">
      <div className="max-w-7xl mx-auto w-full p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Admin Dashboard
          </h1>
          <p className="text-gray-500">
            Application statistics and system overview
          </p>
        </div>

        {loading && (
          <div className="text-center text-gray-500 py-8">Loading...</div>
        )}

        {stats && (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <Card className="bg-gray-900/30 border-gray-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-500 uppercase mb-1">
                        Total Conversations
                      </p>
                      <p className="text-2xl font-bold text-white">
                        {stats.conversations}
                      </p>
                    </div>
                    <MessageSquare className="w-8 h-8 text-blue-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-gray-900/30 border-gray-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-500 uppercase mb-1">
                        Total Messages
                      </p>
                      <p className="text-2xl font-bold text-white">
                        {stats.messages}
                      </p>
                    </div>
                    <FileText className="w-8 h-8 text-green-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-gray-900/30 border-gray-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-500 uppercase mb-1">
                        Projects
                      </p>
                      <p className="text-2xl font-bold text-white">
                        {stats.projects}
                      </p>
                    </div>
                    <Shield className="w-8 h-8 text-purple-400" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-gray-900/30 border-gray-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-500 uppercase mb-1">
                        Reports
                      </p>
                      <p className="text-2xl font-bold text-white">
                        {stats.reports}
                      </p>
                    </div>
                    <FileText className="w-8 h-8 text-cyan-400" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* System Status */}
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Application Status</span>
                    <Badge className="bg-green-500/20 text-green-400">
                      {stats.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Authentication</span>
                    <Badge className="bg-blue-500/20 text-blue-400">
                      Disabled (Open Access)
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Database</span>
                    <Badge className="bg-green-500/20 text-green-400">
                      Connected
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Removed user management and audit log tables */}
        <div className="space-y-4 mt-6">
          <Card className="bg-gray-900/30 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">About This Dashboard</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-400">
                This is a simplified admin dashboard showing application
                statistics. User management and authentication features have
                been removed for open access mode.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
