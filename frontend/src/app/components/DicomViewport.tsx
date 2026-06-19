import { useState, useEffect } from "react";
import { RotateCw, ZoomIn, ZoomOut, Move, FlipHorizontal, Layers } from "lucide-react";
import { Button } from "./ui/button";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";

type ViewMode = "raw" | "mask" | "overlay";
type Seed = { x: number; y: number; type: "left" | "right" };

interface DicomViewportProps {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  imageData: string | null;
  maskData: string | null;
  mode: "auto" | "semi-manual" | "correction";
  onSeedPlaced?: (seeds: Seed[]) => void;
  dicomImageData: ImageData | null;
  message?: string | null;
  overlayData: string | null;
}

export function DicomViewport({ dicomImageData, canvasRef, imageData, maskData, overlayData, mode, onSeedPlaced, message: propsMessage }: DicomViewportProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("raw");
  const [rotation, setRotation] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [isPanning, setIsPanning] = useState(false);
  const [lastPos, setLastPos] = useState({ x: 0, y: 0 });
  const [localMessage, setLocalMessage] = useState<string | null>(null);

  const message = propsMessage ?? localMessage;

useEffect(() => {
    drawCanvas();
}, [dicomImageData, maskData, overlayData, viewMode, rotation, zoom, pan, seeds]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (dicomImageData && viewMode !== "mask") {
      canvas.width = dicomImageData.width;
      canvas.height = dicomImageData.height;
      ctx.putImageData(dicomImageData, 0, 0);
    }

    if (maskData && viewMode === "mask") {
      const maskImg = new Image();
      maskImg.onload = () => {
        canvas.width = maskImg.width;
        canvas.height = maskImg.height;
        ctx.drawImage(maskImg, 0, 0, canvas.width, canvas.height);
      };
      maskImg.src = maskData;
    }

    if (overlayData && viewMode === "overlay") {
      const overlayImg = new Image();
      overlayImg.onload = () => {
        canvas.width = overlayImg.width;
        canvas.height = overlayImg.height;
        ctx.drawImage(overlayImg, 0, 0, canvas.width, canvas.height);
      };
      overlayImg.src = overlayData;
    }

    if (viewMode === "raw" && mode === "semi-manual") {
      drawSeeds(ctx);
    }
  };

  const drawSeeds = (ctx: CanvasRenderingContext2D) => {
    seeds.forEach((seed) => {
      const color = seed.type === "left" ? "#3B82F6" : "#10F4B1";
      ctx.globalAlpha = 1;
      ctx.fillStyle = color;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(seed.x, seed.y, 38, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(seed.x, seed.y, 70, 0, 2 * Math.PI);
      ctx.strokeStyle = color + "80";
      ctx.lineWidth = 8;
      ctx.stroke();
    });
  };


  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (mode !== "semi-manual") return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();

    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    const seedType = seeds.length % 2 === 0 ? "left" : "right";
    const newSeeds: Seed[] = [...seeds, { x, y, type: seedType }];
    setSeeds(newSeeds);
    setLocalMessage(null);
    onSeedPlaced?.(newSeeds);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (mode === "semi-manual") return;
    setIsPanning(true);
    setLastPos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    const dx = e.clientX - lastPos.x;
    const dy = e.clientY - lastPos.y;
    setPan({ x: pan.x + dx, y: pan.y + dy });
    setLastPos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  return (
    <div className="flex-1 flex flex-col bg-background">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setRotation((r) => (r + 90) % 360)}
            title="Rotation"
          >
            <RotateCw className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setZoom((z) => Math.min(z + 0.2, 3))}
            title="Zoom +"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setZoom((z) => Math.max(z - 0.2, 0.5))}
            title="Zoom -"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
              setRotation(0);
            }}
            title="Pan"
          >
            <Move className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setRotation((r) => (r + 180) % 360)}
            title="Miroir"
          >
            <FlipHorizontal className="w-4 h-4" />
          </Button>
        </div>

        <ToggleGroup type="single" value={viewMode} onValueChange={(v) => v && setViewMode(v as ViewMode)}>
          <ToggleGroupItem value="raw" aria-label="Image brute">
            <Layers className="w-4 h-4 mr-2" />
            Brute
          </ToggleGroupItem>
          <ToggleGroupItem value="mask" aria-label="Masque seul">
            Masque
          </ToggleGroupItem>
          <ToggleGroupItem value="overlay" aria-label="Overlay">
            Overlay
          </ToggleGroupItem>
        </ToggleGroup>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-[#000000] overflow-hidden">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          onClick={handleCanvasClick}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="border border-border/30 rounded-lg cursor-crosshair"
          style={{  maxWidth: "100%", 
                    maxHeight: "100%",
                    objectFit: "contain",
                    width: "auto",
                    height: "auto", 
                  }}
        />
      </div>

      {mode === "semi-manual" && (
        <div className="p-3 border-t border-border bg-card/50 text-sm text-center">
          {message && seeds.length < 2 && <p className="text-red-500 mb-1">{message}</p>}
          {seeds.length >= 2 && `${seeds.length} seeds placés - Prêt pour segmentation`}
        </div>
      )}
    </div>
  );
}
