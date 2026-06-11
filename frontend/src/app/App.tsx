import { useState } from "react";
import { LeftSidebar } from "./components/LeftSidebar";
import { DicomViewport } from "./components/DicomViewport";
import { RightPanel } from "./components/RightPanel";

type SegmentationMode = "auto" | "semi-manual" | "correction";

export default function App() {
  const [mode, setMode] = useState<SegmentationMode>("auto");
  const [imageData, setImageData] = useState<string | null>(null);
  const [maskData, setMaskData] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [metrics, setMetrics] = useState({
    leftLungArea: 0,
    rightLungArea: 0,
    symmetryIndex: 0,
    confidenceScore: 0,
  });

  const handleFileUpload = async (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setImageData(result);

      generateMockXRayImage();
    };
    reader.readAsDataURL(file);
  };

  const generateMockXRayImage = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 600;
    const ctx = canvas.getContext("2d");

    if (ctx) {
      const gradient = ctx.createRadialGradient(400, 300, 50, 400, 300, 400);
      gradient.addColorStop(0, "#1a1a1a");
      gradient.addColorStop(0.5, "#2d2d2d");
      gradient.addColorStop(1, "#0a0a0a");

      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 800, 600);

      ctx.fillStyle = "rgba(255, 255, 255, 0.15)";
      ctx.beginPath();
      ctx.ellipse(300, 300, 120, 180, 0, 0, 2 * Math.PI);
      ctx.fill();

      ctx.beginPath();
      ctx.ellipse(500, 300, 130, 190, 0, 0, 2 * Math.PI);
      ctx.fill();

      ctx.fillStyle = "rgba(100, 100, 100, 0.3)";
      ctx.beginPath();
      ctx.arc(400, 250, 60, 0, 2 * Math.PI);
      ctx.fill();

      for (let i = 0; i < 12; i++) {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(400, 150 + i * 30, 350, 0.3, 2.84);
        ctx.stroke();
      }

      setImageData(canvas.toDataURL());
    }
  };

  const handleRunSegmentation = () => {
    setIsProcessing(true);

    setTimeout(() => {
      generateMockMask();

      setMetrics({
        leftLungArea: 145.3 + Math.random() * 20,
        rightLungArea: 156.8 + Math.random() * 20,
        symmetryIndex: 92 + Math.random() * 6,
        confidenceScore: 88 + Math.random() * 10,
      });

      setIsProcessing(false);
    }, 2000);
  };

  const generateMockMask = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 600;
    const ctx = canvas.getContext("2d");

    if (ctx) {
      ctx.fillStyle = "rgba(59, 130, 246, 0.4)";
      ctx.beginPath();
      ctx.ellipse(300, 300, 120, 180, 0, 0, 2 * Math.PI);
      ctx.fill();

      ctx.strokeStyle = "#3B82F6";
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.fillStyle = "rgba(16, 244, 177, 0.4)";
      ctx.beginPath();
      ctx.ellipse(500, 300, 130, 190, 0, 0, 2 * Math.PI);
      ctx.fill();

      ctx.strokeStyle = "#10F4B1";
      ctx.lineWidth = 3;
      ctx.stroke();

      setMaskData(canvas.toDataURL());
    }
  };

  return (
    <div className="size-full flex bg-background text-foreground">
      <LeftSidebar onFileUpload={handleFileUpload} />

      <DicomViewport
        imageData={imageData}
        maskData={maskData}
        mode={mode}
        onSeedPlaced={() => {}}
      />

      <RightPanel
        mode={mode}
        onModeChange={setMode}
        onRunSegmentation={handleRunSegmentation}
        metrics={metrics}
        isProcessing={isProcessing}
      />
    </div>
  );
}