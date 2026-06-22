import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Button } from "./ui/button";
import { Slider } from "./ui/slider";
import { Progress } from "./ui/progress";
import { Paintbrush, Eraser, Wand2, Play, Check, User } from "lucide-react";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "./ui/tooltip";

type SegmentationMode = "auto" | "semi-manual" | "correction";

interface RightPanelProps {
  mode: SegmentationMode;
  onModeChange: (mode: SegmentationMode) => void;
  onRunSegmentation: () => void;
  metrics: {
    leftLungOfPatientArea: number;
    rightLungOfPatientArea: number;
    symmetryIndex: number;
    criticalAssymetric: boolean;
  };
  isProcessing: boolean;
  onOpenPatientInfo: () => void;
}

export function RightPanel({
  mode,
  onModeChange,
  onRunSegmentation,
  metrics,
  isProcessing,
  onOpenPatientInfo,
}: RightPanelProps) {
  const [brushSize, setBrushSize] = useState([10]);
  const [maskOpacity, setMaskOpacity] = useState([50]);
  const [correctionTool, setCorrectionTool] = useState<"brush" | "eraser" | "smooth">("brush");

  return (
    <div className="w-96 bg-sidebar border-l border-sidebar-border flex flex-col h-full">
      <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
        <h2>Contrôle & Analyse</h2>
        <Button variant="outline" size="sm" onClick={onOpenPatientInfo}>
          <User className="w-4 h-4 mr-2" />
          Patient
        </Button>
      </div>

      <Tabs defaultValue="segmentation" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-4 grid w-auto grid-cols-2">
          <TabsTrigger value="segmentation">Segmentation</TabsTrigger>
          <TabsTrigger value="metrics">Métriques</TabsTrigger>
        </TabsList>

        <TabsContent value="segmentation" className="flex-1 p-4 space-y-4 overflow-auto">
          <div>
            <label className="text-sm mb-3 block">Mode de Segmentation</label>
            <ToggleGroup
              type="single"
              value={mode}
              onValueChange={(v) => v && onModeChange(v as SegmentationMode)}
              className="flex flex-col gap-2"
            >
              <ToggleGroupItem value="auto" className="w-full justify-start">
                <Wand2 className="w-4 h-4 mr-2" />
                Automatique
              </ToggleGroupItem>
              <ToggleGroupItem value="semi-manual" className="w-full justify-start">
                <Play className="w-4 h-4 mr-2" />
                Semi-Manuel (Seeds)
              </ToggleGroupItem>
              <ToggleGroupItem value="correction" className="w-full justify-start">
                <Paintbrush className="w-4 h-4 mr-2" />
                Correction
              </ToggleGroupItem>
            </ToggleGroup>
          </div>

          {mode === "auto" && (
            <div className="space-y-4">
              <Button
                onClick={onRunSegmentation}
                disabled={isProcessing}
                className="w-full"
                size="lg"
              >
                {isProcessing ? "Traitement..." : "Lancer la Segmentation"}
              </Button>

              {isProcessing && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Segmentation en cours...</p>
                  <Progress value={65} className="h-2" />
                </div>
              )}
            </div>
          )}

          {mode === "semi-manual" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-card border border-border">
                <p className="text-xs text-muted-foreground mb-2">Instructions</p>
                <p className="text-xs text-muted-foreground mb-2">Pour avoir des résultats satisfaisants, il est conseiller de ne pas placer les points sur des côtes.</p>
                <ol className="text-sm space-y-1 list-decimal list-inside">
                  <li>Placer au moins un point dans le <span className="text-[#3B82F6]">poumon droit du patient</span></li>
                  <li>Placer au moins un point dans le <span className="text-[#3B82F6]">poumon gauche du patient</span></li>
                  <li>Lancer la propagation</li>
                </ol>
              </div>

              <Button
                onClick={onRunSegmentation}
                className="w-full"
                size="lg"
              >
              <Play className="w-4 h-4 mr-2" />
                Propager les Seeds
              </Button>
              {isProcessing && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Segmentation en cours...</p>
                  <Progress value={65} className="h-2" />
                </div>
              )}
            </div>
          )}

          {mode === "correction" && (
            <div className="space-y-4">
              <div>
                <label className="text-sm mb-3 block">Outils de Retouche</label>
                <ToggleGroup
                  type="single"
                  value={correctionTool}
                  onValueChange={(v) => v && setCorrectionTool(v as typeof correctionTool)}
                  className="grid grid-cols-3 gap-2"
                >
                  <ToggleGroupItem value="brush">
                    <Paintbrush className="w-4 h-4" />
                  </ToggleGroupItem>
                  <ToggleGroupItem value="eraser">
                    <Eraser className="w-4 h-4" />
                  </ToggleGroupItem>
                  <ToggleGroupItem value="smooth">
                    <Wand2 className="w-4 h-4" />
                  </ToggleGroupItem>
                </ToggleGroup>
              </div>

              <div>
                <label className="text-sm mb-3 block">Taille du Pinceau</label>
                <div className="flex items-center gap-3">
                  <Slider
                    value={brushSize}
                    onValueChange={setBrushSize}
                    min={5}
                    max={50}
                    step={1}
                    className="flex-1"
                  />
                  <span className="text-sm w-12 text-right">{brushSize[0]}px</span>
                </div>
              </div>

              <div>
                <label className="text-sm mb-3 block">Opacité du Masque</label>
                <div className="flex items-center gap-3">
                  <Slider
                    value={maskOpacity}
                    onValueChange={setMaskOpacity}
                    min={0}
                    max={100}
                    step={5}
                    className="flex-1"
                  />
                  <span className="text-sm w-12 text-right">{maskOpacity[0]}%</span>
                </div>
              </div>

              <Button className="w-full" variant="outline">
                <Check className="w-4 h-4 mr-2" />
                Valider les Modifications
              </Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="metrics" className="flex-1 p-4 space-y-4 overflow-auto">
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-card border border-border">
              <p className="text-xs text-muted-foreground mb-3">Surface Totale</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Poumon Gauche du patient</p>
                  <p className="text-2xl" style={{ color: "#10F4B1" }}>
                    {metrics.leftLungOfPatientArea.toFixed(1)}
                  </p>
                  <p className="text-xs text-muted-foreground">cm²</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Poumon Droit du patient</p>
                  <p className="text-2xl" style={{ color: "#10F4B1" }}>
                    {metrics.rightLungOfPatientArea.toFixed(1)}
                  </p>
                  <p className="text-xs text-muted-foreground">cm²</p>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-card border border-border">
              <p className="text-xs text-muted-foreground mb-3">Indice de Symétrie</p>
              <div className="flex items-center gap-3 mb-2">
                <Progress
                  value={metrics.symmetryIndex}
                  className="flex-1 h-4"
                  indicatorClassName={metrics.criticalAssymetric ? "bg-red-500" : "bg-[#10F4B1]"}
                  style={{
                    background: metrics.symmetryIndex > 90 && !metrics.criticalAssymetric
                      ? "rgba(16, 244, 177, 0.2)"
                      : "rgba(245, 158, 11, 0.2)"
                  }}
                />
                <span className="text-xl"style={{ color: metrics.criticalAssymetric ? "#EF4444" : "inherit" }}>
                    {metrics.symmetryIndex.toFixed(1)}%
                  </span> 
               </div>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <p className="text-xs text-muted-foreground cursor-help underline-offset-2 hover:underline">
                      {metrics.symmetryIndex > 90 && !metrics.criticalAssymetric
                        ? "✓ Symétrie normale"
                        : "⚠ Asymétrie détectée"}
                    </p>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-sm max-w-xs">
                      {metrics.symmetryIndex > 90 && !metrics.criticalAssymetric
                        ? "Les deux poumons ont une taille similaire, ce qui indique une morphologie normale."
                        : "Une différence significative de taille entre les deux poumons a été détectée. De plus, si l'indice de symétrie est élevé, cela peut indiquer une surface plus importante du poumon gauche que du poumon droit."}
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <div className="p-4 rounded-lg bg-card border border-border">
              <p className="text-xs text-muted-foreground mb-2">Surface Totale</p>
              <p className="text-2xl">
                {(metrics.leftLungOfPatientArea + metrics.rightLungOfPatientArea).toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">cm²</p>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
