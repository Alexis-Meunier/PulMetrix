import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import { RotateCw, ZoomIn, ZoomOut, Move, FlipHorizontal, Layers } from "lucide-react";
import { Button } from "./ui/button";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";
import { Seed } from "../App";

type ViewMode = "raw" | "mask" | "overlay";
type CorrectionTool = "brush" | "eraser";

interface DicomViewportProps {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  imageData: string | null;
  maskData: string | null;
  mode: "auto" | "semi-manual" | "correction";
  onSeedPlaced?: (seeds: Seed[]) => void;
  dicomImageData: ImageData | null;
  message?: string | null;
  overlayData: string | null;
  onMaskCorrected?: (newMaskBlob: Blob) => void;
  brushSize?: number;
  correctionTool?: CorrectionTool;
}

export interface DicomViewportRef {
  validateCorrection: () => Promise<void>;
}

export const DicomViewport = forwardRef<DicomViewportRef, DicomViewportProps>(
  ({ dicomImageData, 
    canvasRef, 
    imageData, 
    maskData, 
    overlayData, 
    mode, 
    onSeedPlaced, 
    message: propsMessage, 
    onMaskCorrected, 
    brushSize = 10, 
    correctionTool = "brush" }, 
    ref) => {
  const [viewMode, setViewMode] = useState<ViewMode>("raw");
  const [rotation, setRotation] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [isPanning, setIsPanning] = useState(false);
  const [lastPos, setLastPos] = useState({ x: 0, y: 0 });
  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  const drawCanvasRef = useRef<HTMLCanvasElement | null>(null); 
  const overlayImgRef = useRef<HTMLImageElement | null>(null);
  const maskImgRef = useRef<HTMLImageElement | null>(null);

  const message = propsMessage ?? localMessage;

  useEffect(() => {
    if (!overlayData) {
      overlayImgRef.current = null;
      return;
    }
    const img = new Image();
    img.onload = () => {
      overlayImgRef.current = img;
      drawCanvas(); 
    };
    img.src = overlayData;
  }, [overlayData]);

  useEffect(() => {
    if (!maskData) {
      maskImgRef.current = null;
      return;
    }
    const img = new Image();
    img.onload = () => {
      maskImgRef.current = img;
      drawCanvas();
    };
    img.src = maskData;
  }, [maskData]);

  useEffect(() => {
    setSeeds([]);
  }, [dicomImageData]);

  useEffect(() => {
      if (!dicomImageData) return;
      const drawCanvas = document.createElement("canvas");
      drawCanvas.width = dicomImageData.width;
      drawCanvas.height = dicomImageData.height;
      drawCanvasRef.current = drawCanvas;
    }, [dicomImageData]);

  useEffect(() => {
      drawCanvas();
  }, [dicomImageData, maskData, overlayData, viewMode, rotation, zoom, pan, seeds]);

  useImperativeHandle(ref, () => ({
      validateCorrection: handleValidateCorrection,
  }));

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const handleDrawStart = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (mode !== "correction") return;
    setIsDrawing(true);
    drawAt(e);
  };

  const handleDrawMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (mode !== "correction" || !isDrawing) return;
    drawAt(e);
  };

  const handleDrawEnd = () => {
    setIsDrawing(false);
    drawCanvas(); 
  };

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
      const maskImg = maskImgRef.current;
      if (!maskImg) return;
      canvas.width = maskImg.width;
      canvas.height = maskImg.height;
      ctx.drawImage(maskImg, 0, 0, canvas.width, canvas.height);
      drawCorrectionLayer(ctx);
    }

    if (overlayData && viewMode === "overlay") {
        const overlayImg = overlayImgRef.current;
        if (!overlayImg) return;
        canvas.width = overlayImg.width;
        canvas.height = overlayImg.height;
        ctx.drawImage(overlayImg, 0, 0, canvas.width, canvas.height);
        drawCorrectionLayer(ctx);
    }

    if (viewMode === "raw" && mode === "semi-manual") {
      drawSeeds(ctx);
    }
  };

  const drawAt = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const draw_Canvas = drawCanvasRef.current;
    if (!draw_Canvas) return;
    const ctx = draw_Canvas.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCanvasCoords(e);

    ctx.globalCompositeOperation = correctionTool === "eraser" ? "destination-out" : "source-over";
    ctx.fillStyle = "#0404f3";
    ctx.beginPath();
    ctx.arc(x, y, brushSize, 0, 2 * Math.PI);
    ctx.fill();

    drawCanvas();
  };

  const drawCorrectionLayer = (ctx: CanvasRenderingContext2D) => {
    const drawCanvas = drawCanvasRef.current;
    if (!drawCanvas || mode !== "correction") return;
    ctx.globalAlpha = 0.6;
    ctx.drawImage(drawCanvas, 0, 0);
    ctx.globalAlpha = 1;
  };

  const validateCorrection = async (): Promise<Blob | null> => {
    if (!maskData || !drawCanvasRef.current) return null;

    const baseMaskImg = new Image();
    await new Promise((resolve) => {
      baseMaskImg.onload = resolve;
      baseMaskImg.src = maskData;
    });

    const mergeCanvas = document.createElement("canvas");
    mergeCanvas.width = baseMaskImg.width;
    mergeCanvas.height = baseMaskImg.height;
    const mergeCtx = mergeCanvas.getContext("2d")!;

    mergeCtx.drawImage(baseMaskImg, 0, 0);
    mergeCtx.drawImage(drawCanvasRef.current, 0, 0);

    return new Promise((resolve) => {
      mergeCanvas.toBlob((blob) => resolve(blob), "image/png");
    });
  };

  const handleValidateCorrection = async () => {
    const blob = await validateCorrection();
    if (blob && onMaskCorrected) {
      onMaskCorrected(blob);
      const drawCanvas = drawCanvasRef.current;
      if (drawCanvas) {
        const ctx = drawCanvas.getContext("2d");
        ctx?.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
      }
    }
  };

  const drawSeeds = (ctx: CanvasRenderingContext2D) => {
    seeds.forEach((seed) => {
      const color = "#3B82F6";
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

    const newSeeds: Seed[] = [...seeds, { x, y }];
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
          onMouseDown={(e) => mode === "correction" ? handleDrawStart(e) : handleMouseDown(e)}
          onMouseMove={(e) => mode === "correction" ? handleDrawMove(e) : handleMouseMove(e)}
          onMouseUp={() => mode === "correction" ? handleDrawEnd() : handleMouseUp()}
          onMouseLeave={() => mode === "correction" ? handleDrawEnd() : handleMouseUp()}
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
});
