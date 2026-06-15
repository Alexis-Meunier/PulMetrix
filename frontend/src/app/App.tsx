import { useRef, useState } from "react";
import { LeftSidebar } from "./components/LeftSidebar";
import { DicomViewport } from "./components/DicomViewport";
import { RightPanel } from "./components/RightPanel";
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

const canvasRef = useRef<HTMLCanvasElement>(null);


const handleFileUpload = async (file: File) => {
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
      <div id="dwv-container" style={{display:"none"}} />
      <LeftSidebar onFileUpload={handleFileUpload} />

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
      />
    </div>
  );
}