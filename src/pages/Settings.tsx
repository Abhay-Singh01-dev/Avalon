import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  User,
  Bell,
  Database,
  Shield,
  Zap,
  Bot,
  UserCircle,
  Plus,
  X,
  Link,
  Globe,
  ExternalLink,
  Trash2,
  ChevronDown,
  ChevronRight,
  Upload,
  FileText,
  Edit2,
} from "lucide-react";
import { useAppContext } from "@/context/AppContext";

interface CustomDataSource {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
}

interface ResearchFocusArea {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
}

interface FocusAreaLink {
  id: string;
  url: string;
  title: string;
  enabled: boolean;
}

interface FocusAreaFile {
  id: string;
  name: string;
  fileName: string;
  enabled: boolean;
}

interface FocusAreaWithLinks {
  key: string;
  name: string;
  enabled: boolean;
  isCustom?: boolean;
  links: FocusAreaLink[];
  files: FocusAreaFile[];
}

interface ExpertNetworkFile {
  id: string;
  name: string;
  type: 'link' | 'file';
  url?: string;
  fileName?: string;
  enabled: boolean;
}

interface PatentFile {
  id: string;
  name: string;
  fileName: string;
  uploadedAt: string;
}

export default function SettingsPage() {
  const { settings, updateSettings, loading } = useAppContext();
  const [notifications, setNotifications] = React.useState(true);
  const [autoSave, setAutoSave] = React.useState(true);

  // Agent customization settings - initialize from context
  const [agentPersona, setAgentPersona] = React.useState(
    settings?.agentPersona || ""
  );
  const [responseStyle, setResponseStyle] = React.useState(
    settings?.responseStyle || "detailed"
  );
  const [focusAreas, setFocusAreas] = React.useState(
    settings?.focusAreas || {
      oncology: true,
      cardiology: false,
      neurology: false,
      immunology: false,
      rare_diseases: false,
      gene_therapy: false,
    }
  );
  const [dataSources, setDataSources] = React.useState(
    settings?.dataSources || {
      clinicaltrials: true,
      pubmed: true,
      patents: true,
      market_reports: false,
      expert_networks: false,
    }
  );

  // Custom data sources with URLs for web scraping
  const [customDataSources, setCustomDataSources] = React.useState<CustomDataSource[]>(
    (settings as any)?.customDataSources || []
  );
  const [newDataSourceName, setNewDataSourceName] = React.useState("");
  const [newDataSourceUrl, setNewDataSourceUrl] = React.useState("");

  // Custom research focus areas with links
  const [customFocusAreas, setCustomFocusAreas] = React.useState<ResearchFocusArea[]>(
    (settings as any)?.customFocusAreas || []
  );
  const [newFocusAreaName, setNewFocusAreaName] = React.useState("");
  const [newFocusAreaUrl, setNewFocusAreaUrl] = React.useState("");

  const addCustomDataSource = () => {
    if (!newDataSourceName.trim() || !newDataSourceUrl.trim()) return;
    const newSource: CustomDataSource = {
      id: Date.now().toString(),
      name: newDataSourceName.trim(),
      url: newDataSourceUrl.trim(),
      enabled: true,
    };
    setCustomDataSources([...customDataSources, newSource]);
    setNewDataSourceName("");
    setNewDataSourceUrl("");
  };

  const removeCustomDataSource = (id: string) => {
    setCustomDataSources(customDataSources.filter((s) => s.id !== id));
  };

  const toggleCustomDataSource = (id: string) => {
    setCustomDataSources(
      customDataSources.map((s) =>
        s.id === id ? { ...s, enabled: !s.enabled } : s
      )
    );
  };

  const addCustomFocusArea = () => {
    if (!newFocusAreaName.trim()) return;
    const newArea: ResearchFocusArea = {
      id: Date.now().toString(),
      name: newFocusAreaName.trim(),
      url: newFocusAreaUrl.trim(),
      enabled: true,
    };
    setCustomFocusAreas([...customFocusAreas, newArea]);
    setNewFocusAreaName("");
    setNewFocusAreaUrl("");
  };

  const removeCustomFocusArea = (id: string) => {
    setCustomFocusAreas(customFocusAreas.filter((a) => a.id !== id));
  };

  const toggleCustomFocusArea = (id: string) => {
    setCustomFocusAreas(
      customFocusAreas.map((a) =>
        a.id === id ? { ...a, enabled: !a.enabled } : a
      )
    );
  };

  // Focus areas with expandable links and files
  const [focusAreasWithLinks, setFocusAreasWithLinks] = React.useState<FocusAreaWithLinks[]>([
    { key: 'oncology', name: 'Oncology', enabled: true, files: [], links: [
      { id: '1', url: 'https://www.cancer.gov', title: 'National Cancer Institute', enabled: true },
      { id: '2', url: 'https://www.asco.org', title: 'ASCO - Oncology Research', enabled: true },
    ]},
    { key: 'cardiology', name: 'Cardiology', enabled: false, files: [], links: [
      { id: '3', url: 'https://www.heart.org', title: 'American Heart Association', enabled: true },
    ]},
    { key: 'neurology', name: 'Neurology', enabled: false, files: [], links: [
      { id: '4', url: 'https://www.aan.com', title: 'American Academy of Neurology', enabled: true },
    ]},
    { key: 'immunology', name: 'Immunology', enabled: false, files: [], links: [] },
    { key: 'rare_diseases', name: 'Rare Diseases', enabled: false, files: [], links: [
      { id: '5', url: 'https://rarediseases.org', title: 'NORD - Rare Diseases', enabled: true },
    ]},
    { key: 'gene_therapy', name: 'Gene Therapy', enabled: false, files: [], links: [] },
  ]);
  
  const [expandedFocusAreas, setExpandedFocusAreas] = React.useState<Record<string, boolean>>({});
  const [newLinkUrl, setNewLinkUrl] = React.useState<Record<string, string>>({});
  const [newLinkTitle, setNewLinkTitle] = React.useState<Record<string, string>>({});
  const [editingLink, setEditingLink] = React.useState<string | null>(null);
  const [editLinkUrl, setEditLinkUrl] = React.useState("");
  const [editLinkTitle, setEditLinkTitle] = React.useState("");

  // Expert Networks state
  const [expertNetworkFiles, setExpertNetworkFiles] = React.useState<ExpertNetworkFile[]>([]);
  const [newExpertLinkUrl, setNewExpertLinkUrl] = React.useState("");
  const [newExpertLinkName, setNewExpertLinkName] = React.useState("");

  // Market Reports state
  const [marketReportFiles, setMarketReportFiles] = React.useState<ExpertNetworkFile[]>([]);
  const [newMarketLinkUrl, setNewMarketLinkUrl] = React.useState("");
  const [newMarketLinkName, setNewMarketLinkName] = React.useState("");

  // Patent Files state
  const [patentFiles, setPatentFiles] = React.useState<PatentFile[]>([]);

  const toggleFocusAreaExpanded = (key: string) => {
    setExpandedFocusAreas(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleFocusAreaEnabled = (key: string) => {
    setFocusAreasWithLinks(prev => 
      prev.map(area => area.key === key ? { ...area, enabled: !area.enabled } : area)
    );
    setFocusAreas(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }));
  };

  const addLinkToFocusArea = (areaKey: string) => {
    const url = newLinkUrl[areaKey]?.trim();
    const title = newLinkTitle[areaKey]?.trim();
    if (!url || !title) return;
    
    setFocusAreasWithLinks(prev => 
      prev.map(area => 
        area.key === areaKey 
          ? { ...area, links: [...area.links, { id: Date.now().toString(), url, title, enabled: true }] }
          : area
      )
    );
    setNewLinkUrl(prev => ({ ...prev, [areaKey]: '' }));
    setNewLinkTitle(prev => ({ ...prev, [areaKey]: '' }));
  };

  const removeLinkFromFocusArea = (areaKey: string, linkId: string) => {
    setFocusAreasWithLinks(prev =>
      prev.map(area =>
        area.key === areaKey
          ? { ...area, links: area.links.filter(link => link.id !== linkId) }
          : area
      )
    );
  };

  const toggleLinkEnabled = (areaKey: string, linkId: string) => {
    setFocusAreasWithLinks(prev =>
      prev.map(area =>
        area.key === areaKey
          ? { ...area, links: area.links.map(link => link.id === linkId ? { ...link, enabled: !link.enabled } : link) }
          : area
      )
    );
  };

  const startEditingLink = (areaKey: string, link: FocusAreaLink) => {
    setEditingLink(`${areaKey}-${link.id}`);
    setEditLinkUrl(link.url);
    setEditLinkTitle(link.title);
  };

  const addFileToFocusArea = (areaKey: string, file: File) => {
    const newFile: FocusAreaFile = {
      id: Date.now().toString(),
      name: file.name.replace(/\.[^/.]+$/, ""),
      fileName: file.name,
      enabled: true,
    };
    setFocusAreasWithLinks(prev =>
      prev.map(area =>
        area.key === areaKey
          ? { ...area, files: [...area.files, newFile] }
          : area
      )
    );
  };

  const removeFileFromFocusArea = (areaKey: string, fileId: string) => {
    setFocusAreasWithLinks(prev =>
      prev.map(area =>
        area.key === areaKey
          ? { ...area, files: area.files.filter(f => f.id !== fileId) }
          : area
      )
    );
  };

  const toggleFileEnabled = (areaKey: string, fileId: string) => {
    setFocusAreasWithLinks(prev =>
      prev.map(area =>
        area.key === areaKey
          ? { ...area, files: area.files.map(f => f.id === fileId ? { ...f, enabled: !f.enabled } : f) }
          : area
      )
    );
  };

  // Add custom focus area to the expandable list
  const addCustomFocusAreaExpanded = () => {
    if (!newFocusAreaName.trim()) return;
    const newKey = 'custom_' + Date.now().toString();
    const newArea: FocusAreaWithLinks = {
      key: newKey,
      name: newFocusAreaName.trim(),
      enabled: true,
      isCustom: true,
      links: newFocusAreaUrl.trim() ? [{ id: Date.now().toString(), url: newFocusAreaUrl.trim(), title: newFocusAreaUrl.trim(), enabled: true }] : [],
      files: [],
    };
    setFocusAreasWithLinks(prev => [...prev, newArea]);
    setNewFocusAreaName("");
    setNewFocusAreaUrl("");
  };

  const removeCustomFocusAreaExpanded = (key: string) => {
    setFocusAreasWithLinks(prev => prev.filter(area => area.key !== key));
  };

  const saveEditedLink = (areaKey: string, linkId: string) => {
    setFocusAreasWithLinks(prev =>
      prev.map(area =>
        area.key === areaKey
          ? { ...area, links: area.links.map(link => 
              link.id === linkId ? { ...link, url: editLinkUrl, title: editLinkTitle } : link
            ) }
          : area
      )
    );
    setEditingLink(null);
    setEditLinkUrl("");
    setEditLinkTitle("");
  };

  // Expert Networks functions
  const addExpertNetworkLink = () => {
    if (!newExpertLinkUrl.trim() || !newExpertLinkName.trim()) return;
    setExpertNetworkFiles(prev => [...prev, {
      id: Date.now().toString(),
      name: newExpertLinkName.trim(),
      type: 'link',
      url: newExpertLinkUrl.trim(),
      enabled: true,
    }]);
    setNewExpertLinkUrl("");
    setNewExpertLinkName("");
  };

  const handleExpertFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setExpertNetworkFiles(prev => [...prev, {
      id: Date.now().toString(),
      name: file.name,
      type: 'file',
      fileName: file.name,
      enabled: true,
    }]);
  };

  // Market Reports functions
  const addMarketReportLink = () => {
    if (!newMarketLinkUrl.trim() || !newMarketLinkName.trim()) return;
    setMarketReportFiles(prev => [...prev, {
      id: Date.now().toString(),
      name: newMarketLinkName.trim(),
      type: 'link',
      url: newMarketLinkUrl.trim(),
      enabled: true,
    }]);
    setNewMarketLinkUrl("");
    setNewMarketLinkName("");
  };

  const handleMarketFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setMarketReportFiles(prev => [...prev, {
      id: Date.now().toString(),
      name: file.name,
      type: 'file',
      fileName: file.name,
      enabled: true,
    }]);
  };

  // Patent Files functions
  const handlePatentFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPatentFiles(prev => [...prev, {
      id: Date.now().toString(),
      name: file.name.replace(/\.[^/.]+$/, ""),
      fileName: file.name,
      uploadedAt: new Date().toISOString(),
    }]);
  };

  const removePatentFile = (id: string) => {
    setPatentFiles(prev => prev.filter(f => f.id !== id));
  };

  // Sync with context when settings load
  React.useEffect(() => {
    if (settings) {
      setAgentPersona(settings.agentPersona || "");
      setResponseStyle(settings.responseStyle || "detailed");
      setCustomDataSources((settings as any).customDataSources || []);
      setCustomFocusAreas((settings as any).customFocusAreas || []);
      setFocusAreas(
        settings.focusAreas || {
          oncology: true,
          cardiology: false,
          neurology: false,
          immunology: false,
          rare_diseases: false,
          gene_therapy: false,
        }
      );
      setDataSources(
        settings.dataSources || {
          clinicaltrials: true,
          pubmed: true,
          patents: true,
          market_reports: false,
          expert_networks: false,
        }
      );
    }
  }, [settings]);

  const handleSaveAgentSettings = async () => {
    await updateSettings({
      agentPersona,
      responseStyle,
      focusAreas,
      dataSources,
      customDataSources,
      customFocusAreas,
    } as any);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-950 via-black to-gray-950 overflow-auto">
      <div className="max-w-5xl mx-auto w-full p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-500">
            Manage your account and application preferences
          </p>
        </div>

        <Tabs defaultValue="account" className="space-y-6">
          <TabsList className="bg-gray-900 border border-gray-800">
            <TabsTrigger
              value="account"
              className="data-[state=active]:bg-blue-600"
            >
              <UserCircle className="w-4 h-4 mr-2" />
              Account
            </TabsTrigger>
            <TabsTrigger
              value="profile"
              className="data-[state=active]:bg-blue-600"
            >
              <User className="w-4 h-4 mr-2" />
              Profile
            </TabsTrigger>
            <TabsTrigger
              value="agent"
              className="data-[state=active]:bg-blue-600"
            >
              <Bot className="w-4 h-4 mr-2" />
              Agent Settings
            </TabsTrigger>
            <TabsTrigger
              value="notifications"
              className="data-[state=active]:bg-blue-600"
            >
              <Bell className="w-4 h-4 mr-2" />
              Notifications
            </TabsTrigger>
            <TabsTrigger
              value="data"
              className="data-[state=active]:bg-blue-600"
            >
              <Database className="w-4 h-4 mr-2" />
              Data Sources
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="data-[state=active]:bg-blue-600"
            >
              <Shield className="w-4 h-4 mr-2" />
              Security
            </TabsTrigger>
            <TabsTrigger
              value="rag"
              className="data-[state=active]:bg-blue-600"
            >
              <Zap className="w-4 h-4 mr-2" />
              RAG Features
            </TabsTrigger>
          </TabsList>

          <TabsContent value="account">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">
                  Account Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <p className="text-blue-400 text-sm">
                      Avalon is running in open access mode. All features are
                      available without authentication.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-gray-300">Application Version</Label>
                    <Input
                      value="Avalon v1.0.0"
                      readOnly
                      className="bg-black border-gray-800 text-gray-400"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-gray-300">Access Level</Label>
                    <Input
                      value="Full Access"
                      readOnly
                      className="bg-black border-gray-800 text-gray-400"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="profile">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">
                  Profile Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-gray-300">
                    Full Name
                  </Label>
                  <Input
                    id="name"
                    defaultValue="Dr. Sarah Johnson"
                    className="bg-black border-gray-800 text-gray-200"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-gray-300">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    defaultValue="sarah.johnson@pharma.com"
                    className="bg-black border-gray-800 text-gray-200"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="organization" className="text-gray-300">
                    Organization
                  </Label>
                  <Input
                    id="organization"
                    defaultValue="BioPharma Research Inc."
                    className="bg-black border-gray-800 text-gray-200"
                  />
                </div>
                <Button className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500">
                  Save Changes
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="agent">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">
                  AI Agent Personalization
                </CardTitle>
                <p className="text-sm text-gray-500">
                  Customize your research assistant's behavior and expertise
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Agent Persona */}
                <div className="space-y-2">
                  <Label htmlFor="agent-persona" className="text-gray-300">
                    Agent Persona
                  </Label>
                  <Textarea
                    id="agent-persona"
                    value={agentPersona}
                    onChange={(e) => setAgentPersona(e.target.value)}
                    placeholder="e.g., You are an expert pharmaceutical researcher with 20 years of experience in oncology drug development..."
                    className="bg-black border-gray-800 text-gray-200 min-h-[100px]"
                  />
                  <p className="text-xs text-gray-500">
                    Define how the agent should behave and what expertise it
                    should have
                  </p>
                </div>

                {/* Response Style */}
                <div className="space-y-2">
                  <Label htmlFor="response-style" className="text-gray-300">
                    Response Style
                  </Label>
                  <Select
                    value={responseStyle}
                    onValueChange={setResponseStyle}
                  >
                    <SelectTrigger className="bg-black border-gray-800 text-gray-200">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gray-800">
                      <SelectItem value="concise">
                        Concise - Brief, to-the-point answers
                      </SelectItem>
                      <SelectItem value="detailed">
                        Detailed - Comprehensive analysis with context
                      </SelectItem>
                      <SelectItem value="formal">
                        Formal - Academic and professional tone
                      </SelectItem>
                      <SelectItem value="conversational">
                        Conversational - Friendly and approachable
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Research Focus Areas */}
                <div className="space-y-3">
                  <Label className="text-gray-300">Research Focus Areas</Label>
                  <p className="text-xs text-gray-500 mb-2">
                    Click on each area to view/add related links and files. Toggle to enable/disable.
                  </p>
                  <div className="space-y-3">
                    {focusAreasWithLinks.map((area) => (
                      <div key={area.key} className={`bg-black border ${area.isCustom ? 'border-purple-800/50' : 'border-gray-800'} rounded-lg overflow-hidden`}>
                        {/* Header */}
                        <div className="flex items-center justify-between p-3">
                          <div 
                            className="flex items-center gap-2 flex-1 cursor-pointer"
                            onClick={() => toggleFocusAreaExpanded(area.key)}
                          >
                            {expandedFocusAreas[area.key] ? (
                              <ChevronDown className="w-4 h-4 text-gray-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-gray-400" />
                            )}
                            <span className="text-sm text-gray-300">{area.name}</span>
                            {area.isCustom && (
                              <span className="text-xs bg-purple-900/50 text-purple-400 px-2 py-0.5 rounded-full">Custom</span>
                            )}
                            {(area.links.length > 0 || area.files.length > 0) && (
                              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
                                {area.links.length + area.files.length} item{(area.links.length + area.files.length) !== 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {area.isCustom && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => removeCustomFocusAreaExpanded(area.key)}
                                className="h-6 w-6 text-gray-400 hover:text-red-400"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            )}
                            <Switch
                              checked={area.enabled}
                              onCheckedChange={() => toggleFocusAreaEnabled(area.key)}
                            />
                          </div>
                        </div>
                        
                        {/* Expandable Links & Files Section */}
                        {expandedFocusAreas[area.key] && (
                          <div className="border-t border-gray-800 p-3 space-y-2 bg-gray-900/30">
                            {/* Existing Files */}
                            {area.files.map((file) => (
                              <div key={file.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                                <Switch
                                  checked={file.enabled}
                                  onCheckedChange={() => toggleFileEnabled(area.key, file.id)}
                                  className="scale-75"
                                />
                                <FileText className="w-4 h-4 text-amber-400" />
                                <div className="flex-1 min-w-0">
                                  <span className="text-xs text-gray-300 block truncate">{file.name}</span>
                                  <span className="text-xs text-gray-500">{file.fileName}</span>
                                </div>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => removeFileFromFocusArea(area.key, file.id)}
                                  className="h-6 w-6 text-gray-400 hover:text-red-400"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </Button>
                              </div>
                            ))}

                            {/* Existing Links */}
                            {area.links.map((link) => (
                              <div key={link.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                                {editingLink === `${area.key}-${link.id}` ? (
                                  <>
                                    <Input
                                      value={editLinkTitle}
                                      onChange={(e) => setEditLinkTitle(e.target.value)}
                                      placeholder="Link title"
                                      className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-7 flex-1"
                                    />
                                    <Input
                                      value={editLinkUrl}
                                      onChange={(e) => setEditLinkUrl(e.target.value)}
                                      placeholder="URL"
                                      className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-7 flex-1"
                                    />
                                    <Button
                                      size="sm"
                                      onClick={() => saveEditedLink(area.key, link.id)}
                                      className="h-7 px-2 bg-green-600 hover:bg-green-500"
                                    >
                                      Save
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => setEditingLink(null)}
                                      className="h-7 px-2"
                                    >
                                      <X className="w-3 h-3" />
                                    </Button>
                                  </>
                                ) : (
                                  <>
                                    <Switch
                                      checked={link.enabled}
                                      onCheckedChange={() => toggleLinkEnabled(area.key, link.id)}
                                      className="scale-75"
                                    />
                                    <ExternalLink className="w-4 h-4 text-blue-400" />
                                    <div className="flex-1 min-w-0">
                                      <span className="text-xs text-gray-300 block truncate">{link.title}</span>
                                      <a
                                        href={link.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-blue-400 hover:text-blue-300 truncate block"
                                      >
                                        {link.url}
                                      </a>
                                    </div>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => startEditingLink(area.key, link)}
                                      className="h-6 w-6 text-gray-400 hover:text-blue-400"
                                    >
                                      <Edit2 className="w-3 h-3" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => removeLinkFromFocusArea(area.key, link.id)}
                                      className="h-6 w-6 text-gray-400 hover:text-red-400"
                                    >
                                      <Trash2 className="w-3 h-3" />
                                    </Button>
                                  </>
                                )}
                              </div>
                            ))}
                            
                            {/* Add New Link */}
                            <div className="flex gap-2 mt-2 pt-2 border-t border-gray-800/50">
                              <Input
                                placeholder="Link title"
                                value={newLinkTitle[area.key] || ''}
                                onChange={(e) => setNewLinkTitle(prev => ({ ...prev, [area.key]: e.target.value }))}
                                className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1"
                              />
                              <Input
                                placeholder="URL"
                                value={newLinkUrl[area.key] || ''}
                                onChange={(e) => setNewLinkUrl(prev => ({ ...prev, [area.key]: e.target.value }))}
                                className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1"
                              />
                              <Button
                                size="sm"
                                onClick={() => addLinkToFocusArea(area.key)}
                                disabled={!newLinkTitle[area.key]?.trim() || !newLinkUrl[area.key]?.trim()}
                                className="h-8 px-3 bg-blue-600 hover:bg-blue-500"
                              >
                                <Plus className="w-3 h-3" />
                              </Button>
                            </div>

                            {/* Upload Files */}
                            <label className="flex items-center gap-2 p-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-amber-500/50 hover:bg-amber-500/5 transition-all">
                              <Upload className="w-4 h-4 text-gray-400" />
                              <span className="text-xs text-gray-400">Upload Research Files (PDF, DOCX)</span>
                              <input
                                type="file"
                                accept=".pdf,.docx,.doc"
                                onChange={(e) => {
                                  const file = e.target.files?.[0];
                                  if (file) addFileToFocusArea(area.key, file);
                                  e.target.value = '';
                                }}
                                className="hidden"
                              />
                            </label>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Add Custom Research Focus Area */}
                  <div className="mt-4 pt-4 border-t border-gray-800">
                    <p className="text-xs text-gray-500 mb-3">Add Custom Research Area</p>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Research area name"
                        value={newFocusAreaName}
                        onChange={(e) => setNewFocusAreaName(e.target.value)}
                        className="bg-black border-gray-800 text-gray-200 flex-1"
                      />
                      <Input
                        placeholder="Initial URL (optional)"
                        value={newFocusAreaUrl}
                        onChange={(e) => setNewFocusAreaUrl(e.target.value)}
                        className="bg-black border-gray-800 text-gray-200 flex-1"
                      />
                      <Button
                        onClick={addCustomFocusAreaExpanded}
                        disabled={!newFocusAreaName.trim()}
                        className="bg-blue-600 hover:bg-blue-500"
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Risk Assessment Parameters */}
                <div className="space-y-3">
                  <Label className="text-gray-300">
                    Data Source Risk Assessment
                  </Label>
                  <p className="text-xs text-gray-500">
                    Set reliability thresholds for different data sources
                  </p>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-black border border-gray-800 rounded-lg">
                      <div className="flex-1">
                        <span className="text-sm text-gray-300 font-medium">
                          Peer-Reviewed Journals
                        </span>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">
                            Low Risk
                          </span>
                          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500"
                              style={{ width: "90%" }}
                            ></div>
                          </div>
                          <span className="text-xs text-green-400">90%</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-black border border-gray-800 rounded-lg">
                      <div className="flex-1">
                        <span className="text-sm text-gray-300 font-medium">
                          Clinical Trial Registries
                        </span>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">
                            Low Risk
                          </span>
                          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500"
                              style={{ width: "85%" }}
                            ></div>
                          </div>
                          <span className="text-xs text-green-400">85%</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-black border border-gray-800 rounded-lg">
                      <div className="flex-1">
                        <span className="text-sm text-gray-300 font-medium">
                          Patent Databases
                        </span>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">
                            Medium Risk
                          </span>
                          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-yellow-500"
                              style={{ width: "70%" }}
                            ></div>
                          </div>
                          <span className="text-xs text-yellow-400">70%</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-black border border-gray-800 rounded-lg">
                      <div className="flex-1">
                        <span className="text-sm text-gray-300 font-medium">
                          News & Media
                        </span>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">
                            Medium-High Risk
                          </span>
                          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-orange-500"
                              style={{ width: "50%" }}
                            ></div>
                          </div>
                          <span className="text-xs text-orange-400">50%</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-black border border-gray-800 rounded-lg">
                      <div className="flex-1">
                        <span className="text-sm text-gray-300 font-medium">
                          Social Media & Forums
                        </span>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">
                            High Risk
                          </span>
                          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-red-500"
                              style={{ width: "30%" }}
                            ></div>
                          </div>
                          <span className="text-xs text-red-400">30%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={handleSaveAgentSettings}
                  disabled={loading}
                  className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
                >
                  {loading ? "Saving..." : "Save Agent Settings"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">
                  Notification Preferences
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-gray-300 font-medium">
                      Email Notifications
                    </h4>
                    <p className="text-sm text-gray-500">
                      Receive email updates about new reports
                    </p>
                  </div>
                  <Switch
                    checked={notifications}
                    onCheckedChange={setNotifications}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-gray-300 font-medium">
                      Auto-save Reports
                    </h4>
                    <p className="text-sm text-gray-500">
                      Automatically save research reports
                    </p>
                  </div>
                  <Switch checked={autoSave} onCheckedChange={setAutoSave} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-gray-300 font-medium">
                      Research Alerts
                    </h4>
                    <p className="text-sm text-gray-500">
                      Get notified about new clinical trials
                    </p>
                  </div>
                  <Switch />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="data">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">
                  Data Sources
                </CardTitle>
                <p className="text-sm text-gray-500">
                  Configure data sources for research. Add links and upload files for enhanced analysis.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* RAG Index Status Banner */}
                <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Database className="w-5 h-5 text-blue-400" />
                      <div>
                        <h4 className="text-sm font-medium text-white">Data Source RAG</h4>
                        <p className="text-xs text-gray-400">
                          Files uploaded here are automatically indexed for retrieval
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Status</p>
                        <span className="text-xs px-2 py-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          Disabled
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Indexed Chunks</p>
                        <span className="text-sm font-medium text-gray-300">0</span>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled
                        className="border-gray-700 text-gray-400"
                      >
                        Rebuild Index
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 pl-8">
                    Enable DATA_SOURCE_RAG_ENABLED=true in backend/.env to activate retrieval
                  </p>
                </div>

                <div className="space-y-3">
                  {/* ClinicalTrials.gov */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-green-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">ClinicalTrials.gov</span>
                          <p className="text-xs text-gray-600">Clinical trial registries</p>
                        </div>
                      </div>
                      <Switch
                        checked={dataSources.clinicaltrials}
                        onCheckedChange={(checked) => setDataSources({ ...dataSources, clinicaltrials: checked })}
                      />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <div className="flex gap-2">
                        <Input placeholder="Trial name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Input placeholder="URL" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Button size="sm" className="h-8 px-3 bg-green-600 hover:bg-green-500"><Plus className="w-3 h-3" /></Button>
                      </div>
                      <label className="flex items-center gap-2 p-2 mt-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-green-500/50 hover:bg-green-500/5 transition-all">
                        <Upload className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-400">Upload Clinical Trial Documents</span>
                        <input type="file" accept=".pdf,.docx,.doc" className="hidden" />
                      </label>
                    </div>
                  </div>

                  {/* PubMed - with links/files */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-blue-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">PubMed</span>
                          <p className="text-xs text-gray-600">Biomedical literature</p>
                        </div>
                      </div>
                      <Switch
                        checked={dataSources.pubmed}
                        onCheckedChange={(checked) => setDataSources({ ...dataSources, pubmed: checked })}
                      />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <p className="text-xs text-gray-500 mb-2">Add PubMed article links or upload files</p>
                      <div className="space-y-2">
                        {expertNetworkFiles.filter(f => f.id.startsWith('pubmed_')).map((item) => (
                          <div key={item.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                            <Switch checked={item.enabled} onCheckedChange={() => setExpertNetworkFiles(prev => prev.map(f => f.id === item.id ? { ...f, enabled: !f.enabled } : f))} className="scale-75" />
                            {item.type === 'link' ? <ExternalLink className="w-4 h-4 text-blue-400" /> : <FileText className="w-4 h-4 text-blue-400" />}
                            <div className="flex-1 min-w-0">
                              <span className="text-xs text-gray-300 block truncate">{item.name}</span>
                              {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 truncate block">{item.url}</a>}
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setExpertNetworkFiles(prev => prev.filter(f => f.id !== item.id))} className="h-6 w-6 text-gray-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></Button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input placeholder="Article name" id="pubmed-name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Input placeholder="URL" id="pubmed-url" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Button size="sm" onClick={() => {
                            const name = (document.getElementById('pubmed-name') as HTMLInputElement)?.value;
                            const url = (document.getElementById('pubmed-url') as HTMLInputElement)?.value;
                            if (name && url) {
                              setExpertNetworkFiles(prev => [...prev, { id: 'pubmed_' + Date.now(), name, type: 'link', url, enabled: true }]);
                              (document.getElementById('pubmed-name') as HTMLInputElement).value = '';
                              (document.getElementById('pubmed-url') as HTMLInputElement).value = '';
                            }
                          }} className="h-8 px-3 bg-blue-600 hover:bg-blue-500"><Plus className="w-3 h-3" /></Button>
                        </div>
                        <label className="flex items-center gap-2 p-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-blue-500/50 hover:bg-blue-500/5 transition-all">
                          <Upload className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-400">Upload PubMed Files</span>
                          <input type="file" accept=".pdf,.docx,.doc" onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) setExpertNetworkFiles(prev => [...prev, { id: 'pubmed_' + Date.now(), name: file.name, type: 'file', fileName: file.name, enabled: true }]);
                          }} className="hidden" />
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* DrugBank - with links/files */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-orange-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">DrugBank</span>
                          <p className="text-xs text-gray-600">Drug & target database</p>
                        </div>
                      </div>
                      <Switch defaultChecked={true} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <p className="text-xs text-gray-500 mb-2">Add DrugBank links or upload drug data files</p>
                      <div className="space-y-2">
                        {expertNetworkFiles.filter(f => f.id.startsWith('drugbank_')).map((item) => (
                          <div key={item.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                            <Switch checked={item.enabled} onCheckedChange={() => setExpertNetworkFiles(prev => prev.map(f => f.id === item.id ? { ...f, enabled: !f.enabled } : f))} className="scale-75" />
                            {item.type === 'link' ? <ExternalLink className="w-4 h-4 text-orange-400" /> : <FileText className="w-4 h-4 text-orange-400" />}
                            <div className="flex-1 min-w-0">
                              <span className="text-xs text-gray-300 block truncate">{item.name}</span>
                              {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 truncate block">{item.url}</a>}
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setExpertNetworkFiles(prev => prev.filter(f => f.id !== item.id))} className="h-6 w-6 text-gray-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></Button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input placeholder="Drug name" id="drugbank-name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Input placeholder="URL" id="drugbank-url" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Button size="sm" onClick={() => {
                            const name = (document.getElementById('drugbank-name') as HTMLInputElement)?.value;
                            const url = (document.getElementById('drugbank-url') as HTMLInputElement)?.value;
                            if (name && url) {
                              setExpertNetworkFiles(prev => [...prev, { id: 'drugbank_' + Date.now(), name, type: 'link', url, enabled: true }]);
                              (document.getElementById('drugbank-name') as HTMLInputElement).value = '';
                              (document.getElementById('drugbank-url') as HTMLInputElement).value = '';
                            }
                          }} className="h-8 px-3 bg-orange-600 hover:bg-orange-500"><Plus className="w-3 h-3" /></Button>
                        </div>
                        <label className="flex items-center gap-2 p-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-orange-500/50 hover:bg-orange-500/5 transition-all">
                          <Upload className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-400">Upload DrugBank Files</span>
                          <input type="file" accept=".pdf,.docx,.doc,.csv,.xlsx" onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) setExpertNetworkFiles(prev => [...prev, { id: 'drugbank_' + Date.now(), name: file.name, type: 'file', fileName: file.name, enabled: true }]);
                          }} className="hidden" />
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Patent Databases - with name/link and file upload */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-pink-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">Patent Databases</span>
                          <p className="text-xs text-gray-600">Global patent archives (USPTO, EPO, WIPO)</p>
                        </div>
                      </div>
                      <Switch
                        checked={dataSources.patents}
                        onCheckedChange={(checked) => setDataSources({ ...dataSources, patents: checked })}
                      />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <p className="text-xs text-gray-500 mb-2">Add patent name with link or upload patent documents</p>
                      <div className="space-y-2">
                        {patentFiles.map((file) => (
                          <div key={file.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                            <FileText className="w-4 h-4 text-pink-400" />
                            <div className="flex-1 min-w-0">
                              <span className="text-xs text-gray-300 block truncate">{file.name}</span>
                              <span className="text-xs text-gray-500">{file.fileName}</span>
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => removePatentFile(file.id)} className="h-6 w-6 text-gray-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></Button>
                          </div>
                        ))}
                        {expertNetworkFiles.filter(f => f.id.startsWith('patent_')).map((item) => (
                          <div key={item.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                            <Switch checked={item.enabled} onCheckedChange={() => setExpertNetworkFiles(prev => prev.map(f => f.id === item.id ? { ...f, enabled: !f.enabled } : f))} className="scale-75" />
                            <ExternalLink className="w-4 h-4 text-pink-400" />
                            <div className="flex-1 min-w-0">
                              <span className="text-xs text-gray-300 block truncate">{item.name}</span>
                              {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 truncate block">{item.url}</a>}
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setExpertNetworkFiles(prev => prev.filter(f => f.id !== item.id))} className="h-6 w-6 text-gray-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></Button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input placeholder="Patent name" id="patent-name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Input placeholder="Patent URL" id="patent-url" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Button size="sm" onClick={() => {
                            const name = (document.getElementById('patent-name') as HTMLInputElement)?.value;
                            const url = (document.getElementById('patent-url') as HTMLInputElement)?.value;
                            if (name && url) {
                              setExpertNetworkFiles(prev => [...prev, { id: 'patent_' + Date.now(), name, type: 'link', url, enabled: true }]);
                              (document.getElementById('patent-name') as HTMLInputElement).value = '';
                              (document.getElementById('patent-url') as HTMLInputElement).value = '';
                            }
                          }} className="h-8 px-3 bg-pink-600 hover:bg-pink-500"><Plus className="w-3 h-3" /></Button>
                        </div>
                        <label className="flex items-center gap-2 p-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-pink-500/50 hover:bg-pink-500/5 transition-all">
                          <Upload className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-400">Upload Patent Files (PDF, DOCX)</span>
                          <input type="file" accept=".pdf,.docx,.doc" onChange={handlePatentFileUpload} className="hidden" />
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* FDA */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-purple-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">FDA (U.S. Food & Drug Administration)</span>
                          <p className="text-xs text-gray-600">Drug approvals & safety alerts</p>
                        </div>
                      </div>
                      <Switch defaultChecked={true} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <div className="flex gap-2">
                        <Input placeholder="Resource name" id="fda-name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Input placeholder="URL" id="fda-url" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Button size="sm" className="h-8 px-3 bg-purple-600 hover:bg-purple-500"><Plus className="w-3 h-3" /></Button>
                      </div>
                      <label className="flex items-center gap-2 p-2 mt-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-purple-500/50 hover:bg-purple-500/5 transition-all">
                        <Upload className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-400">Upload FDA Documents</span>
                        <input type="file" accept=".pdf,.docx,.doc" className="hidden" />
                      </label>
                    </div>
                  </div>

                  {/* EMA */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-yellow-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">EMA (European Medicines Agency)</span>
                          <p className="text-xs text-gray-600">European drug regulations</p>
                        </div>
                      </div>
                      <Switch defaultChecked={false} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <div className="flex gap-2">
                        <Input placeholder="Resource name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Input placeholder="URL" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Button size="sm" className="h-8 px-3 bg-yellow-600 hover:bg-yellow-500"><Plus className="w-3 h-3" /></Button>
                      </div>
                      <label className="flex items-center gap-2 p-2 mt-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-yellow-500/50 hover:bg-yellow-500/5 transition-all">
                        <Upload className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-400">Upload EMA Documents</span>
                        <input type="file" accept=".pdf,.docx,.doc" className="hidden" />
                      </label>
                    </div>
                  </div>

                  {/* WHO */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-cyan-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">WHO (World Health Organization)</span>
                          <p className="text-xs text-gray-600">Global health guidelines</p>
                        </div>
                      </div>
                      <Switch defaultChecked={false} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <div className="flex gap-2">
                        <Input placeholder="Resource name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Input placeholder="URL" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Button size="sm" className="h-8 px-3 bg-cyan-600 hover:bg-cyan-500"><Plus className="w-3 h-3" /></Button>
                      </div>
                      <label className="flex items-center gap-2 p-2 mt-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-cyan-500/50 hover:bg-cyan-500/5 transition-all">
                        <Upload className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-400">Upload WHO Documents</span>
                        <input type="file" accept=".pdf,.docx,.doc" className="hidden" />
                      </label>
                    </div>
                  </div>

                  {/* Market Reports */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-emerald-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">Market Reports</span>
                          <p className="text-xs text-gray-600">Industry analysis & forecasts</p>
                        </div>
                      </div>
                      <Switch checked={dataSources.market_reports} onCheckedChange={(checked) => setDataSources({ ...dataSources, market_reports: checked })} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <p className="text-xs text-gray-500 mb-2">Add market report links or upload files for enhanced analysis</p>
                      <div className="space-y-2">
                        {marketReportFiles.map((item) => (
                          <div key={item.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                            <Switch checked={item.enabled} onCheckedChange={() => setMarketReportFiles(prev => prev.map(f => f.id === item.id ? { ...f, enabled: !f.enabled } : f))} className="scale-75" />
                            {item.type === 'link' ? <ExternalLink className="w-4 h-4 text-emerald-400" /> : <FileText className="w-4 h-4 text-emerald-400" />}
                            <div className="flex-1 min-w-0">
                              <span className="text-xs text-gray-300 block truncate">{item.name}</span>
                              {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 truncate block">{item.url}</a>}
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setMarketReportFiles(prev => prev.filter(f => f.id !== item.id))} className="h-6 w-6 text-gray-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></Button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input placeholder="Report name" value={newMarketLinkName} onChange={(e) => setNewMarketLinkName(e.target.value)} className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Input placeholder="URL" value={newMarketLinkUrl} onChange={(e) => setNewMarketLinkUrl(e.target.value)} className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Button size="sm" onClick={addMarketReportLink} disabled={!newMarketLinkName.trim() || !newMarketLinkUrl.trim()} className="h-8 px-3 bg-emerald-600 hover:bg-emerald-500"><Plus className="w-3 h-3" /></Button>
                        </div>
                        <label className="flex items-center gap-2 p-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all">
                          <Upload className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-400">Upload Market Report Files</span>
                          <input type="file" accept=".pdf,.docx,.doc,.xlsx,.xls" onChange={handleMarketFileUpload} className="hidden" />
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Expert Networks */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-violet-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">Expert Networks</span>
                          <p className="text-xs text-gray-600">KOL insights & opinions</p>
                        </div>
                      </div>
                      <Switch checked={dataSources.expert_networks} onCheckedChange={(checked) => setDataSources({ ...dataSources, expert_networks: checked })} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <p className="text-xs text-gray-500 mb-2">Add expert network links or upload documents for enhanced analysis</p>
                      <div className="space-y-2">
                        {expertNetworkFiles.filter(f => !f.id.startsWith('pubmed_') && !f.id.startsWith('drugbank_') && !f.id.startsWith('patent_')).map((item) => (
                          <div key={item.id} className="flex items-center gap-2 p-2 bg-black/50 rounded border border-gray-800/50">
                            <Switch checked={item.enabled} onCheckedChange={() => setExpertNetworkFiles(prev => prev.map(f => f.id === item.id ? { ...f, enabled: !f.enabled } : f))} className="scale-75" />
                            {item.type === 'link' ? <ExternalLink className="w-4 h-4 text-violet-400" /> : <FileText className="w-4 h-4 text-violet-400" />}
                            <div className="flex-1 min-w-0">
                              <span className="text-xs text-gray-300 block truncate">{item.name}</span>
                              {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 truncate block">{item.url}</a>}
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setExpertNetworkFiles(prev => prev.filter(f => f.id !== item.id))} className="h-6 w-6 text-gray-400 hover:text-red-400"><Trash2 className="w-3 h-3" /></Button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input placeholder="Expert/Network name" value={newExpertLinkName} onChange={(e) => setNewExpertLinkName(e.target.value)} className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Input placeholder="URL" value={newExpertLinkUrl} onChange={(e) => setNewExpertLinkUrl(e.target.value)} className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                          <Button size="sm" onClick={addExpertNetworkLink} disabled={!newExpertLinkName.trim() || !newExpertLinkUrl.trim()} className="h-8 px-3 bg-violet-600 hover:bg-violet-500"><Plus className="w-3 h-3" /></Button>
                        </div>
                        <label className="flex items-center gap-2 p-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-violet-500/50 hover:bg-violet-500/5 transition-all">
                          <Upload className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-400">Upload Expert Documents</span>
                          <input type="file" accept=".pdf,.docx,.doc" onChange={handleExpertFileUpload} className="hidden" />
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* OpenFDA */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-red-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">OpenFDA</span>
                          <p className="text-xs text-gray-600">Adverse events & recalls</p>
                        </div>
                      </div>
                      <Switch defaultChecked={false} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <div className="flex gap-2">
                        <Input placeholder="Resource name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Input placeholder="URL" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Button size="sm" className="h-8 px-3 bg-red-600 hover:bg-red-500"><Plus className="w-3 h-3" /></Button>
                      </div>
                      <label className="flex items-center gap-2 p-2 mt-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-red-500/50 hover:bg-red-500/5 transition-all">
                        <Upload className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-400">Upload OpenFDA Documents</span>
                        <input type="file" accept=".pdf,.docx,.doc" className="hidden" />
                      </label>
                    </div>
                  </div>

                  {/* Cochrane Library */}
                  <div className="bg-black border border-gray-800 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3">
                      <div className="flex items-center gap-3">
                        <Globe className="w-4 h-4 text-teal-400" />
                        <div>
                          <span className="text-sm text-gray-300 font-medium">Cochrane Library</span>
                          <p className="text-xs text-gray-600">Systematic reviews & meta-analyses</p>
                        </div>
                      </div>
                      <Switch defaultChecked={false} />
                    </div>
                    <div className="border-t border-gray-800 p-3 bg-gray-900/30">
                      <div className="flex gap-2">
                        <Input placeholder="Resource name" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Input placeholder="URL" className="bg-gray-900 border-gray-700 text-gray-200 text-xs h-8 flex-1" />
                        <Button size="sm" className="h-8 px-3 bg-teal-600 hover:bg-teal-500"><Plus className="w-3 h-3" /></Button>
                      </div>
                      <label className="flex items-center gap-2 p-2 mt-2 border border-dashed border-gray-700 rounded cursor-pointer hover:border-teal-500/50 hover:bg-teal-500/5 transition-all">
                        <Upload className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-400">Upload Cochrane Documents</span>
                        <input type="file" accept=".pdf,.docx,.doc" className="hidden" />
                      </label>
                    </div>
                  </div>
                </div>

                {/* Custom Data Sources */}
                <div className="mt-6 pt-6 border-t border-gray-800">
                  <h4 className="text-gray-300 font-medium mb-4 flex items-center gap-2">
                    <Globe className="w-5 h-5 text-cyan-400" />
                    Custom Data Sources
                  </h4>
                  <p className="text-xs text-gray-500 mb-4">Add custom URLs for the agent to analyze</p>
                  <div className="space-y-2">
                    {customDataSources.map((source) => (
                      <div key={source.id} className="p-3 bg-black border border-gray-800 rounded-lg flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <Switch checked={source.enabled} onCheckedChange={() => toggleCustomDataSource(source.id)} />
                          <div className="flex-1 min-w-0">
                            <h4 className="text-gray-300 font-medium truncate text-sm">{source.name}</h4>
                            <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                              <ExternalLink className="w-3 h-3 flex-shrink-0" />
                              <span className="truncate">{source.url}</span>
                            </a>
                          </div>
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => removeCustomDataSource(source.id)} className="h-8 w-8 text-red-400 hover:text-red-300 hover:bg-red-500/10 flex-shrink-0"><Trash2 className="w-4 h-4" /></Button>
                      </div>
                    ))}
                    <div className="flex gap-2 mt-4">
                      <Input placeholder="Source name" value={newDataSourceName} onChange={(e) => setNewDataSourceName(e.target.value)} className="bg-black border-gray-800 text-gray-200 flex-1" />
                      <Input placeholder="URL" value={newDataSourceUrl} onChange={(e) => setNewDataSourceUrl(e.target.value)} className="bg-black border-gray-800 text-gray-200 flex-1" />
                      <Button onClick={addCustomDataSource} disabled={!newDataSourceName.trim() || !newDataSourceUrl.trim()} className="bg-cyan-600 hover:bg-cyan-500"><Plus className="w-4 h-4 mr-2" />Add</Button>
                    </div>
                  </div>
                </div>

                <Button onClick={handleSaveAgentSettings} disabled={loading} className="mt-4 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500">
                  {loading ? "Saving..." : "Save Data Sources"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Security Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password" className="text-gray-300">
                    Current Password
                  </Label>
                  <Input
                    id="current-password"
                    type="password"
                    className="bg-black border-gray-800 text-gray-200"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-password" className="text-gray-300">
                    New Password
                  </Label>
                  <Input
                    id="new-password"
                    type="password"
                    className="bg-black border-gray-800 text-gray-200"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password" className="text-gray-300">
                    Confirm Password
                  </Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    className="bg-black border-gray-800 text-gray-200"
                  />
                </div>
                <Button className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500">
                  Update Password
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rag">
            <Card className="bg-gray-900/30 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-400" />
                  RAG Feature Flags
                </CardTitle>
                <p className="text-sm text-gray-500">
                  Control Project RAG, Link Fetching, and Web Scraping features.
                  These features are disabled by default for safety with smaller models.
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Warning Banner */}
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-amber-400 mt-0.5" />
                    <div>
                      <h4 className="text-amber-400 font-medium mb-1">Healthcare Safety Notice</h4>
                      <p className="text-sm text-gray-400">
                        RAG features require larger models (≥14B/70B parameters) to work safely.
                        Current local model (Mistral 7B) cannot reliably handle RAG context,
                        which may lead to hallucinations in healthcare-critical applications.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Feature Flags */}
                <div className="space-y-4">
                  {/* Project RAG */}
                  <div className="bg-black border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <Database className="w-5 h-5 text-blue-400" />
                        <div>
                          <span className="text-gray-200 font-medium">Project RAG</span>
                          <p className="text-xs text-gray-500">Document retrieval for project chats</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400">
                          Disabled
                        </span>
                        <Switch
                          disabled
                          checked={false}
                          className="opacity-50 cursor-not-allowed"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 pl-8">
                      Requires larger models ≥14B or cloud models. Your current local model cannot safely perform this operation.
                    </p>
                  </div>

                  {/* Link Fetching */}
                  <div className="bg-black border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <Link className="w-5 h-5 text-purple-400" />
                        <div>
                          <span className="text-gray-200 font-medium">Link Fetching</span>
                          <p className="text-xs text-gray-500">Fetch and index web links</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400">
                          Disabled
                        </span>
                        <Switch
                          disabled
                          checked={false}
                          className="opacity-50 cursor-not-allowed"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 pl-8">
                      Links are saved for future use. Fetching requires larger models.
                    </p>
                  </div>

                  {/* Web Scraping */}
                  <div className="bg-black border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <Globe className="w-5 h-5 text-green-400" />
                        <div>
                          <span className="text-gray-200 font-medium">Web Scraping</span>
                          <p className="text-xs text-gray-500">Scrape web content for analysis</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400">
                          Disabled
                        </span>
                        <Switch
                          disabled
                          checked={false}
                          className="opacity-50 cursor-not-allowed"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 pl-8">
                      Web scraping requires larger models for reliable extraction.
                    </p>
                  </div>
                </div>

                {/* How to Enable */}
                <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-4">
                  <h4 className="text-gray-300 font-medium mb-2">How to Enable RAG Features</h4>
                  <ol className="text-sm text-gray-400 space-y-2 list-decimal list-inside">
                    <li>Install a larger model (≥14B parameters) in LM Studio</li>
                    <li>Update <code className="text-amber-400 bg-black px-1 rounded">backend/.env</code>:
                      <pre className="mt-1 p-2 bg-black rounded text-xs overflow-x-auto">
{`ENABLE_PROJECT_RAG=true
ENABLE_LINK_FETCH=true
ENABLE_WEB_SCRAPING=true`}
                      </pre>
                    </li>
                    <li>Restart the backend server</li>
                  </ol>
                </div>

                {/* Current Model Info */}
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Bot className="w-4 h-4" />
                  <span>Current Model: <code className="text-gray-400">mistral-7b-instruct-v0.3-q6_k</code></span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
