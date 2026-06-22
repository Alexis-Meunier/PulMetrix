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
export type Seed = { x: number; y: number; };
export type Analysis = { id: string; login: string; age: number | null; timestamp: string | null };

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export const handleFetch = async (url: string, payload: any, method: string) => {
  try {
    return fetch(url, {
      method: method,
      mode: "cors",
      headers: {
        "Content-Type": "application/json",
      },
      body: payload ? JSON.stringify(payload) : null,
    });
  } catch (error) {
    console.error("Erreur lors de la requête fetch:", error);
    return null;
  }
};

export default function App() {
  const [mode, setMode] = useState<SegmentationMode>("auto");
  const [imageData, setImageData] = useState<string | null>(null);
  const [maskData, setMaskData] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [metrics, setMetrics] = useState({
    rightLungOfPatientArea: 0,
    leftLungOfPatientArea: 0,
    symmetryIndex: 0,
    criticalAssymetric: false,
  });
  const [dicomImageData, setDicomImageData] = useState<ImageData | null>(null);
  const [dicomBase64, setDicomBase64] = useState<string | null>(null);
  const [patientName, setPatientName] = useState("");
  const [patientAge, setPatientAge] = useState("");
  const [patientDate, setPatientDate] = useState("");
  const [isInfoDialogOpen, setIsInfoDialogOpen] = useState(false);
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [overlayData, setOverlayData] = useState<string | null>(null);

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

  const convertDicomFile = async (file: any) => {
    const arrayBuffer = await file.arrayBuffer();
    const byteArray = new Uint8Array(arrayBuffer);

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
  }


  const handleFileUpload = async (file: File) => {
    await convertDicomFile(file);
    const base64 = await fileToBase64(file);
    setDicomBase64(base64);
    setIsInfoDialogOpen(true);
  };

  const abs = (x: number) => (x < 0 ? -x : x);

  const handleRunSegmentation = async () => {
    if (!dicomBase64) {
      console.warn("Aucun DICOM chargé pour l'analyse");
      return;
    }

    let timestampIso = null;
    if (patientDate)
      timestampIso = parseDateFrToIso(patientDate);

    setIsProcessing(true);

    console.log("Envoi des données au backend pour la segmentation...");

    try {
      if (mode === "semi-manual" && seeds.length < 2) {
          setMessage(`Vous avez moins de 2 seeds placés. Ajoutez en ${2 - seeds.length} pour lancer la segmentation`);
          return;
      }

      const payload = {
        image: dicomBase64,
        login: patientName,
        age: Number(patientAge) || null,
        timestamp: timestampIso,
        seeds: seeds.map((seed) => ({ x: Math.round(seed.x), y: Math.round(seed.y) })),
      };

      const response_id = await handleFetch(`${BACKEND_URL}/compute`, payload, "POST");

      if (!response_id || !response_id.ok) {
        throw new Error("Échec backend pour la segmentation");
      }

      const result_id = await response_id.json();
      console.log("Résultat compute :", result_id);

      const response_mask = await handleFetch(`${BACKEND_URL}/analysis/${result_id}/mask`, null, "GET");

      if (!response_mask || !response_mask.ok) {
        throw new Error("Échec backend pour le masque");
      }

      const maskBlob = await response_mask.blob();
      const maskUrl = URL.createObjectURL(maskBlob);
      setMaskData(maskUrl);
      console.log("Résultat mask :", maskBlob);

      const response_overlay = await handleFetch(`${BACKEND_URL}/analysis/${result_id}/overlay`, null, "GET");

      if (!response_overlay || !response_overlay.ok) {
        throw new Error("Échec backend pour l'overlay");
      }

      const overlayBlob = await response_overlay.blob();
      const overlayUrl = URL.createObjectURL(overlayBlob);
      setOverlayData(overlayUrl);
      console.log("Résultat overlay :", overlayBlob);

      
      const response_metrics = await handleFetch(`${BACKEND_URL}/analysis/${result_id}/metrics`, null, "GET");

      if (!response_metrics || !response_metrics.ok) {
        throw new Error("Échec backend pour les métriques");
      }

      const result_metrics = await response_metrics.json();
      console.log("Résultat metrics :", result_metrics);

      setMetrics({
        leftLungOfPatientArea: result_metrics.area_left_lung,
        rightLungOfPatientArea: result_metrics.area_right_lung,
        symmetryIndex: (1 - abs(result_metrics.asymmetry_score)) * 100,
        criticalAssymetric: result_metrics.is_asymmetry_critical,
      });
    } catch (error) {
      console.error("Erreur de segmentation :", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadAnalysis = async (analysisId: string) => {
    try {

      setSeeds([]);
      const response_image = await handleFetch(`${BACKEND_URL}/analysis/${analysisId}/original-image`, null, "GET");
      if (!response_image || !response_image.ok) {
        throw new Error("Échec backend pour l'image originale");
      }
      await convertDicomFile(response_image);

      const response_mask = await handleFetch(`${BACKEND_URL}/analysis/${analysisId}/mask`, null, "GET");
      if (response_mask && response_mask.ok) {
        const maskBlob = await response_mask.blob();
        setMaskData(URL.createObjectURL(maskBlob));
      }

      const response_overlay = await handleFetch(`${BACKEND_URL}/analysis/${analysisId}/overlay`, null, "GET");
      if (response_overlay && response_overlay.ok) {
        const overlayBlob = await response_overlay.blob();
        setOverlayData(URL.createObjectURL(overlayBlob));
      }

      const response_metrics = await handleFetch(`${BACKEND_URL}/analysis/${analysisId}/metrics`, null, "GET");

      if (!response_metrics || !response_metrics.ok) {
        throw new Error("Échec backend pour les métriques");
      }

      const result_metrics = await response_metrics.json();

      setMetrics({
        leftLungOfPatientArea: result_metrics.area_left_lung,
        rightLungOfPatientArea: result_metrics.area_right_lung,
        symmetryIndex: (1 - abs(result_metrics.asymmetry_score)) * 100,
        criticalAssymetric: result_metrics.is_asymmetry_critical,
      });
    } catch (error) {
      console.error("Erreur lors du chargement de l'analyse :", error);
    }
  };

  const handlePatientInfoSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

  if (!patientName.trim() || !patientAge.trim() || 
      !patientDate.trim() || !isDateFrValid(patientDate)) {
      return;
    }

    setIsInfoDialogOpen(false);
  };

  return (
    <div className="size-full flex bg-background text-foreground">
      <div id="dwv-container" style={{display:"none"}} />
      <LeftSidebar onFileUpload={handleFileUpload} onSelectAnalysis={handleLoadAnalysis} />

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
        onSeedPlaced={setSeeds}
        message={message}
        overlayData={overlayData}
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