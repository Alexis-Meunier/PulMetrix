import { FormEvent, useRef, useState } from "react";
import { LeftSidebar } from "./components/LeftSidebar";
import { DicomViewport } from "./components/DicomViewport";
import { RightPanel } from "./components/RightPanel";
import { Button } from "./components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./components/ui/dialog";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import dicomParser from "dicom-parser";
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
  const [dicomImageData, setDicomImageData] = useState<ImageData | null>(null);
  const [dicomBase64, setDicomBase64] = useState<string | null>(null);
  const [patientName, setPatientName] = useState("");
  const [patientAge, setPatientAge] = useState("");
  const [patientDate, setPatientDate] = useState("");
  const [isInfoDialogOpen, setIsInfoDialogOpen] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);

  const parseDateFrToIso = (dateFr: string): string | null => {
    const match = dateFr.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return null;
    const [, day, month, year] = match;
    return `${year}-${month}-${day}`;
  };

  const isDateFrValid = (dateFr: string) => Boolean(parseDateFrToIso(dateFr));

  const fileToBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
      } else {
        reject(new Error("Impossible de lire le fichier DICOM"));
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });

  const handleFileUpload = async (file: File) => {
    const arrayBuffer = await file.arrayBuffer();
    const byteArray = new Uint8Array(arrayBuffer);
    const base64 = await fileToBase64(file);
    setDicomBase64(base64);
    setIsInfoDialogOpen(true);
    
    const dataSet = dicomParser.parseDicom(byteArray);
    
    const width = dataSet.uint16("x00280011")!;
    const height = dataSet.uint16("x00280010")!;
    const bitsAllocated = dataSet.uint16("x00280100") || 16;
    
    const windowCenter = dataSet.floatString("x00281050") || 40;
    const windowWidth = dataSet.floatString("x00281051") || 400;

    const pixelDataElement = dataSet.elements.x7fe00010;
    
    const pixelData = bitsAllocated === 16
      ? new Int16Array(byteArray.buffer, pixelDataElement.dataOffset, pixelDataElement.length / 2)
      : new Uint8Array(byteArray.buffer, pixelDataElement.dataOffset, pixelDataElement.length);

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = width;
    canvas.height = height;

    const imageDataObj = ctx.createImageData(width, height);

    const low = windowCenter - windowWidth / 2;
    const high = windowCenter + windowWidth / 2;

    for (let i = 0; i < width * height; i++) {
      let val = pixelData[i];

      if (val <= low) val = 0;
      else if (val >= high) val = 255;
      else val = ((val - low) / windowWidth) * 255;

      imageDataObj.data[i * 4] = val;
      imageDataObj.data[i * 4 + 1] = val;
      imageDataObj.data[i * 4 + 2] = val;
      imageDataObj.data[i * 4 + 3] = 255;
    }

    ctx.putImageData(imageDataObj, 0, 0);
    setDicomImageData(imageDataObj);
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

  const handlePatientInfoSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

  if (!patientName.trim() || !patientAge.trim() || 
      !patientDate.trim() || !isDateFrValid(patientDate)) {
      return;
    }

    setIsInfoDialogOpen(false);
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
      <div id="dwv-container" style={{display:"none"}} />
      <LeftSidebar onFileUpload={handleFileUpload} />

      <Dialog open={isInfoDialogOpen} onOpenChange={setIsInfoDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Informations du patient</DialogTitle>
            <DialogDescription>
              Merci de renseigner les informations du patient, vous pouvez modifier ou compléter les champs dans le panneau de contrôle.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handlePatientInfoSubmit} className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="patient-name">Nom du patient</Label>
              <Input
                id="patient-name"
                value={patientName}
                onChange={(event) => setPatientName(event.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="patient-age">Âge</Label>
              <Input
                id="patient-age"
                type="number"
                value={patientAge}
                onChange={(event) => setPatientAge(event.target.value)}
                min={0}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="patient-date">Date de la radiographie</Label>
              <Input
                id="patient-date"
                type="text"
                placeholder="JJ/MM/AAAA"
                value={patientDate}
                onChange={(event) => setPatientDate(event.target.value)}
                required
              />
            </div>
            <DialogFooter>
              <Button type="submit" className="w-full sm:w-auto">
                Valider
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <DicomViewport
        dicomImageData={dicomImageData}
        canvasRef={canvasRef}
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
        onOpenPatientInfo={() => setIsInfoDialogOpen(true)}
      />
    </div>
  );
}