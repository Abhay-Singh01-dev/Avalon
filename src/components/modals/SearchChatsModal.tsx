import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Search, MessageSquare, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppContext } from "@/context/AppContext";
import { useNavigate } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";

export default function SearchChatsModal({ isOpen, onClose }) {
  const { chats, selectConversation } = useAppContext();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = React.useState("");

  const filteredChats = chats.filter((chat) =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelectChat = async (chatId: string) => {
    await selectConversation(chatId);
    navigate("/chat");
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-gradient-to-br from-gray-950 to-black border-gray-800/50 max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-cyan-400" />
            Search All Chats
          </DialogTitle>
        </DialogHeader>

        {/* Search Input */}
        <div className="relative mt-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your conversations..."
            className="pl-10 bg-black border-gray-800 text-gray-200 placeholder:text-gray-600"
          />
        </div>

        {/* Chat List */}
        <ScrollArea className="h-[50vh] mt-4">
          <div className="space-y-2">
            {filteredChats.length > 0 ? (
              filteredChats.map((chat, idx) => (
                <Button
                  key={`${chat.id}-${idx}`}
                  variant="ghost"
                  className="w-full justify-start p-4 h-auto hover:bg-gray-800/50 transition-colors"
                  onClick={() => handleSelectChat(chat.id)}
                >
                  <div className="flex items-start gap-3 w-full">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center flex-shrink-0">
                      <MessageSquare className="w-5 h-5 text-blue-400" />
                    </div>
                    <div className="flex-1 text-left">
                      <h4 className="text-sm font-medium text-white mb-1">
                        {chat.title}
                      </h4>
                      <div className="flex items-center gap-1 mt-2">
                        <Clock className="w-3 h-3 text-gray-600" />
                        <span className="text-xs text-gray-600">
                          {chat.updated_at
                            ? formatDistanceToNow(new Date(chat.updated_at), {
                                addSuffix: true,
                              })
                            : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>
                </Button>
              ))
            ) : (
              <div className="text-center py-12">
                <MessageSquare className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                <p className="text-gray-500">
                  No chats found matching your search
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="text-xs text-gray-600 text-center pt-4 border-t border-gray-800">
          Found {filteredChats.length} of {chats.length} conversations
        </div>
      </DialogContent>
    </Dialog>
  );
}
