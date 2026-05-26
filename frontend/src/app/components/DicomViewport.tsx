import { useState, useRef, useEffect } from "react";
import { RotateCw, ZoomIn, ZoomOut, Move, FlipHorizontal, Layers } from "lucide-react";
import { Button } from "./ui/button";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";

type ViewMode = "raw" | "mask" | "overlay";
type Seed = { x: number; y: number; type: "left" | "right" };

interface DicomViewportProps {
  imageData: string | null;
  maskData: string | null;
  mode: "auto" | "semi-manual" | "correction";
  onSeedPlaced?: (seeds: Seed[]) => void;
}

export function DicomViewport({ imageData, maskData, mode, onSeedPlaced }: DicomViewportProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("raw");
  const [rotation, setRotation] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [lastPos, setLastPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    drawCanvas();
  }, [imageData, maskData, viewMode, rotation, zoom, pan, seeds]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    ctx.translate(canvas.width / 2 + pan.x, canvas.height / 2 + pan.y);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.scale(zoom, zoom);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);

    if (imageData && viewMode !== "mask") {
      const img = new Image();
      img.src = imageData;
      ctx.globalAlpha = viewMode === "overlay" ? 0.7 : 1;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }

    if (maskData && (viewMode === "mask" || viewMode === "overlay")) {
      const maskImg = new Image();
      maskImg.src = maskData;
      ctx.globalAlpha = viewMode === "overlay" ? 0.5 : 1;
      ctx.drawImage(maskImg, 0, 0, canvas.width, canvas.height);
    }

    ctx.restore();

    seeds.forEach((seed) => {
      const color = seed.type === "left" ? "#3B82F6" : "#10F4B1";
      ctx.fillStyle = color;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(seed.x, seed.y, 8, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(seed.x, seed.y, 20, 0, 2 * Math.PI);
      ctx.strokeStyle = color + "40";
      ctx.lineWidth = 3;
      ctx.stroke();
    });
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (mode !== "semi-manual") return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const seedType = seeds.length % 2 === 0 ? "left" : "right";
    const newSeeds = [...seeds, { x, y, type: seedType }];
    setSeeds(newSeeds);
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

      <div className="flex-1 flex items-center justify-center p-8 bg-[#000000]">
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
          style={{ maxWidth: "100%", maxHeight: "100%" }}
        />
      </div>

      {mode === "semi-manual" && (
        <div className="p-3 border-t border-border bg-card/50 text-sm text-center">
          {seeds.length === 0 && "Cliquez pour placer le seed GAUCHE (bleu)"}
          {seeds.length === 1 && "Cliquez pour placer le seed DROIT (vert)"}
          {seeds.length >= 2 && `${seeds.length} seeds placés - Prêt pour segmentation`}
        </div>
      )}
    </div>
  );
}
