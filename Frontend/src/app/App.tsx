import { useState } from "react";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { FileUpload } from "./components/FileUpload";
import {
  FileList,
  FileItem,
  FileStatus,
} from "./components/FileList";
import { AnalysisConfig } from "./components/AnalysisConfig";
import { ProcessingStatus } from "./components/ProcessingStatus";
import { Results } from "./components/Results";
import { DownloadModal } from "./components/DownloadModal";
import { Footer } from "./components/Footer";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { CheckCircle2, XCircle } from "lucide-react";

type ProcessingPhase =
  | "idle"
  | "processing"
  | "completed"
  | "error";

const mockFiles = [
  {
    name: "Bases técnicas transporte inteligente.pdf",
    type: "PDF",
    sizeMB: 2.4,
  },
  {
    name: "Anexo sistema de cámaras.docx",
    type: "DOCX",
    sizeMB: 0.8,
  },
  {
    name: "Preguntas y respuestas cliente.xlsx",
    type: "XLSX",
    sizeMB: 0.3,
  },
];

const processingSteps = [
  { label: "Leyendo documentos", progress: 20 },
  { label: "Extrayendo requerimientos", progress: 40 },
  { label: "Consolidando información", progress: 60 },
  { label: "Generando entregables", progress: 80 },
  { label: "Proceso finalizado", progress: 100 },
];

const mockResults = [
  {
    id: "propuesta",
    title: "Propuesta técnica",
    description:
      "Propuesta técnica propositiva para SmartCities & Mobility",
    date: "04/06/2026",
    status: "ready" as const,
  },
  {
    id: "matriz",
    title: "Matriz de cumplimiento",
    description:
      "Tabla de cumplimiento técnico y legal detallada",
    date: "04/06/2026",
    status: "ready" as const,
  },
  {
    id: "cotizacion",
    title: "Solicitud de cotización",
    description:
      "Lista de equipos y materiales para cotización",
    date: "04/06/2026",
    status: "ready" as const,
  },
  {
    id: "resumen",
    title: "Resumen ejecutivo",
    description: "Resumen consolidado para revisión comercial",
    date: "04/06/2026",
    status: "ready" as const,
  },
  {
    id: "cambios",
    title: "Registro de cambios",
    description:
      "Cambios detectados en aclaraciones y circulares",
    date: "04/06/2026",
    status: "ready" as const,
  },
];

export default function App() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<
    string[]
  >(["propuesta", "equipos", "matriz"]);
  const [processingPhase, setProcessingPhase] =
    useState<ProcessingPhase>("idle");
  const [currentStep, setCurrentStep] = useState(0);
  const [showDownloadModal, setShowDownloadModal] =
    useState(false);
  const [results, setResults] = useState<typeof mockResults>(
    [],
  );

  const handleFilesSelected = (newFiles: File[]) => {
    const fileItems: FileItem[] = newFiles.map(
      (file, index) => ({
        id: `${Date.now()}-${index}`,
        name: file.name,
        type:
          file.name.split(".").pop()?.toUpperCase() || "FILE",
        size: file.size,
        status: "pending" as FileStatus,
      }),
    );

    setFiles((prev) => [...prev, ...fileItems]);
    toast.success("Archivos agregados correctamente", {
      description: `${newFiles.length} archivo(s) agregado(s)`,
    });
  };

  const handleRemoveFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleProcess = async () => {
    if (files.length === 0) {
      toast.error("No hay archivos para procesar", {
        description:
          "Por favor, sube al menos un archivo antes de continuar",
      });
      return;
    }

    setProcessingPhase("processing");
    setFiles((prev) =>
      prev.map((f) => ({
        ...f,
        status: "uploading" as FileStatus,
      })),
    );

    for (let i = 0; i < processingSteps.length; i++) {
      setCurrentStep(i);
      await new Promise((resolve) => setTimeout(resolve, 1500));

      if (i === 1) {
        setFiles((prev) =>
          prev.map((f) => ({
            ...f,
            status: "processing" as FileStatus,
          })),
        );
      }
    }

    setFiles((prev) =>
      prev.map((f) => ({
        ...f,
        status: "ready" as FileStatus,
      })),
    );
    setProcessingPhase("completed");
    setResults(mockResults);

    toast.success("Documentos procesados correctamente", {
      description:
        "Los entregables están listos para descargar",
      icon: <CheckCircle2 className="w-5 h-5 text-green-600" />,
    });
  };

  const handleClear = () => {
    setFiles([]);
    setSelectedOptions([]);
    setProcessingPhase("idle");
    setCurrentStep(0);
    setResults([]);
    toast.info("Selección limpiada");
  };

  const handleViewDetail = (id: string) => {
    const result = results.find((r) => r.id === id);
    toast.info(`Ver detalle: ${result?.title}`, {
      description:
        "Esta función abrirá el documento en vista previa",
    });
  };

  const handleDownloadSingle = (id: string) => {
    const result = results.find((r) => r.id === id);
    toast.success(`Descargando: ${result?.title}`, {
      description: "El archivo se descargará en breve",
    });
  };

  const handleDownloadFromModal = (format: string) => {
    const formatNames: Record<string, string> = {
      word: "Propuesta técnica (Word)",
      excel: "Matriz de cumplimiento (Excel)",
      pdf: "Resumen ejecutivo (PDF)",
      zip: "Paquete completo (ZIP)",
    };

    toast.success(`Descargando: ${formatNames[format]}`, {
      description: "El archivo se descargará en breve",
    });
    setShowDownloadModal(false);
  };

  const handleUseMockFiles = () => {
    const fileItems: FileItem[] = mockFiles.map(
      (file, index) => ({
        id: `mock-${Date.now()}-${index}`,
        name: file.name,
        type: file.type,
        size: file.sizeMB * 1024 * 1024,
        status: "pending" as FileStatus,
      }),
    );

    setFiles(fileItems);
    toast.success("Archivos de ejemplo cargados", {
      description:
        "Puedes proceder a configurar y procesar los documentos",
    });
  };

  return (
    <>
      <Toaster />
      <div className="min-h-screen flex flex-col bg-[#F9F9F9]">
        <Header />

        <Hero />

        {files.length === 0 && processingPhase === "idle" && (
          <div className="w-full max-w-7xl mx-auto px-8 pb-4">
            <button
              onClick={handleUseMockFiles}
              className="text-sm text-[#205DF5] hover:underline"
            >
              O haz clic aquí para cargar archivos de ejemplo
            </button>
          </div>
        )}

        <FileUpload
          onFilesSelected={handleFilesSelected}
          disabled={processingPhase === "processing"}
        />

        <FileList
          files={files}
          onRemoveFile={handleRemoveFile}
        />

        {files.length > 0 && processingPhase === "idle" && (
          <AnalysisConfig
            selectedOptions={selectedOptions}
            onOptionsChange={setSelectedOptions}
          />
        )}

        {files.length > 0 && processingPhase === "idle" && (
          <div className="w-full max-w-7xl mx-auto px-8 py-4">
            <div className="flex gap-4">
              <button
                onClick={handleProcess}
                disabled={files.length === 0}
                className="px-8 py-3 bg-[#205DF5] text-white rounded-lg hover:bg-opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Procesar documentos
              </button>
              <button
                onClick={handleClear}
                className="px-8 py-3 border border-[#205DF5] text-[#205DF5] rounded-lg hover:bg-[#205DF5] hover:bg-opacity-5 transition-colors"
              >
                Limpiar selección
              </button>
            </div>
          </div>
        )}

        {processingPhase === "processing" && (
          <ProcessingStatus
            currentStep={processingSteps[currentStep].label}
            progress={processingSteps[currentStep].progress}
          />
        )}

        {processingPhase === "completed" && (
          <>
            <Results
              results={results}
              onViewDetail={handleViewDetail}
              onDownload={handleDownloadSingle}
            />

            <div className="w-full max-w-7xl mx-auto px-8 py-8">
              <div className="bg-white rounded-lg border border-[#E4E4E4] p-6">
                <h3 className="text-xl font-medium text-[#000000] mb-4">
                  Descargar resultados
                </h3>
                <p className="text-sm text-[#666666] mb-6">
                  Formato corporativo SONDA: Word, Excel, PDF o
                  ZIP.
                </p>
                <button
                  onClick={() => setShowDownloadModal(true)}
                  className="px-8 py-3 bg-[#205DF5] text-white rounded-lg hover:bg-opacity-90 transition-all"
                >
                  Descargar resultados
                </button>
              </div>
            </div>
          </>
        )}

        <DownloadModal
          isOpen={showDownloadModal}
          onClose={() => setShowDownloadModal(false)}
          onDownload={handleDownloadFromModal}
        />

        <Footer />
      </div>
    </>
  );
}