import { useState } from "react";
import { Upload, FileImage, Clock } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";

interface Patient {
  id: string;
  name: string;
  date: string;
  study: string;
}

export function LeftSidebar({ onFileUpload }: { onFileUpload: (file: File) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [recentPatients] = useState<Patient[]>([
    { id: "1", name: "Patient A", date: "2026-05-12", study: "CXR PA" },
    { id: "2", name: "Patient B", date: "2026-05-11", study: "CXR Lateral" },
    { id: "3", name: "Patient C", date: "2026-05-10", study: "CXR PA" },
  ]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileUpload(files[0]);
    }
  };

  return (
    <div className="w-80 bg-sidebar border-r border-sidebar-border flex flex-col h-full">
      <div className="p-6 border-b border-sidebar-border">
        <h1 className="flex items-center gap-2 mb-1">
          <FileImage className="w-6 h-6 text-primary" />
          PulmoMetric
        </h1>
        <p className="text-sm text-muted-foreground">Analyse & Segmentation CXR</p>
      </div>

      <div className="p-4">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-all
            ${isDragging
              ? "border-primary bg-primary/10"
              : "border-border hover:border-primary/50"
            }
          `}
        >
          <Upload className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
          <p className="mb-2 text-sm">Glisser-déposer DICOM</p>
          <p className="text-xs text-muted-foreground mb-4">ou</p>
          <input
            type="file"
            accept=".dcm,.dicom,image/*"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => document.getElementById("file-upload")?.click()}
          >
            Parcourir
          </Button>
        </div>
      </div>

      <div className="px-4 flex-1 overflow-hidden">
        <div className="flex items-center gap-2 mb-3">
          <Clock className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm">Examens récents</h3>
        </div>
        <ScrollArea className="h-[calc(100%-2rem)]">
          <div className="space-y-2">
            {recentPatients.map((patient) => (
              <button
                key={patient.id}
                className="w-full text-left p-3 rounded-lg bg-card hover:bg-accent/10 border border-border transition-colors"
              >
                <p className="text-sm mb-1">{patient.name}</p>
                <p className="text-xs text-muted-foreground">{patient.study}</p>
                <p className="text-xs text-muted-foreground mt-1">{patient.date}</p>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
