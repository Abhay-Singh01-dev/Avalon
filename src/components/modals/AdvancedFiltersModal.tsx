import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Filter, X } from "lucide-react";

export default function AdvancedFiltersModal({
  isOpen,
  onClose,
  onApplyFilters,
}) {
  const [filters, setFilters] = React.useState({
    name: "",
    about: "",
    dateFrom: "",
    dateTo: "",
  });

  const handleApply = () => {
    onApplyFilters(filters);
    onClose();
  };

  const handleClear = () => {
    setFilters({
      name: "",
      about: "",
      dateFrom: "",
      dateTo: "",
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-gray-900 border-gray-800 max-w-md">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Filter className="w-5 h-5 text-cyan-400" />
            Advanced Filters
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Name Filter */}
          <div className="space-y-2">
            <Label htmlFor="filter-name" className="text-gray-300 text-sm">
              Report Name
            </Label>
            <Input
              id="filter-name"
              value={filters.name}
              onChange={(e) => setFilters({ ...filters, name: e.target.value })}
              placeholder="Filter by report name..."
              className="bg-black border-gray-800 text-gray-200 placeholder:text-gray-600"
            />
          </div>

          {/* About Filter */}
          <div className="space-y-2">
            <Label htmlFor="filter-about" className="text-gray-300 text-sm">
              About
            </Label>
            <Input
              id="filter-about"
              value={filters.about}
              onChange={(e) =>
                setFilters({ ...filters, about: e.target.value })
              }
              placeholder="Filter by topic or description..."
              className="bg-black border-gray-800 text-gray-200 placeholder:text-gray-600"
            />
          </div>

          {/* Date Range */}
          <div className="space-y-2">
            <Label className="text-gray-300 text-sm">Date Range</Label>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="date-from" className="text-xs text-gray-500">
                  From
                </Label>
                <Input
                  id="date-from"
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) =>
                    setFilters({ ...filters, dateFrom: e.target.value })
                  }
                  className="bg-black border-gray-800 text-gray-200"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="date-to" className="text-xs text-gray-500">
                  To
                </Label>
                <Input
                  id="date-to"
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) =>
                    setFilters({ ...filters, dateTo: e.target.value })
                  }
                  className="bg-black border-gray-800 text-gray-200"
                />
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="mt-6 flex gap-2">
          <Button
            variant="outline"
            onClick={handleClear}
            className="border-gray-700 text-gray-400 hover:bg-gray-800"
          >
            <X className="w-4 h-4 mr-2" />
            Clear All
          </Button>
          <Button
            onClick={handleApply}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
          >
            <Filter className="w-4 h-4 mr-2" />
            Apply Filters
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
