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
import { CheckCircle2 } from "lucide-react";

type ProcessingPhase =
  | "idle"
  | "processing"
  | "completed"
  | "error";

interface ResultItem {
  id: string;
  title: string;
  description: string;
  filename: string;
  date: string;
  status: "ready";
}

// Espera entre cada consulta de estado al backend (polling).
const POLL_MS = 1500;

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

// Dispara la descarga de un .docx generado por el backend.
function descargar(jobId: string, resultId: string) {
  const a = document.createElement("a");
  a.href = `/api/download/${jobId}/${resultId}`;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export default function App() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<
    string[]
  >(["propuesta", "equipos", "matriz"]);
  const [processingPhase, setProcessingPhase] =
    useState<ProcessingPhase>("idle");
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState(
    "Preparando",
  );
  const [showDownloadModal, setShowDownloadModal] =
    useState(false);
  const [results, setResults] = useState<ResultItem[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);

  const handleFilesSelected = (newFiles: File[]) => {
    const fileItems: FileItem[] = newFiles.map(
      (file, index) => ({
        id: `${Date.now()}-${index}`,
        name: file.name,
        type:
          file.name.split(".").pop()?.toUpperCase() || "FILE",
        size: file.size,
        status: "pending" as FileStatus,
        file,
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

  const setAllStatus = (status: FileStatus) =>
    setFiles((prev) => prev.map((f) => ({ ...f, status })));

  const handleProcess = async () => {
    if (files.length === 0) {
      toast.error("No hay archivos para procesar", {
        description:
          "Por favor, sube al menos un archivo antes de continuar",
      });
      return;
    }

    setProcessingPhase("processing");
    setProgress(0);
    setStatusMessage("Subiendo documentos");
    setAllStatus("uploading");

    try {
      // 1. Subir los archivos y arrancar el trabajo en el backend.
      const formData = new FormData();
      files.forEach((f) => {
        if (f.file) formData.append("files", f.file, f.name);
      });

      const res = await fetch("/api/process", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`El backend respondió ${res.status}`);
      }
      const { job_id } = await res.json();
      setJobId(job_id);
      setAllStatus("processing");

      // 2. Polling del estado hasta que termine o falle.
      while (true) {
        await sleep(POLL_MS);
        const sres = await fetch(`/api/status/${job_id}`);
        if (!sres.ok) {
          throw new Error(`Estado no disponible (${sres.status})`);
        }
        const estado = await sres.json();
        setProgress(estado.progress ?? 0);
        setStatusMessage(estado.message ?? "Procesando");

        if (estado.phase === "completed") {
          const items: ResultItem[] = (estado.results ?? []).map(
            (r: Omit<ResultItem, "status">) => ({
              ...r,
              status: "ready" as const,
            }),
          );
          setResults(items);
          setAllStatus("ready");
          setProcessingPhase("completed");
          toast.success("Documentos procesados correctamente", {
            description: `Licitación ${estado.licitacion}: entregables listos para descargar`,
            icon: (
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            ),
          });
          break;
        }

        if (estado.phase === "error") {
          throw new Error(estado.error ?? "Error desconocido");
        }
      }
    } catch (err) {
      setProcessingPhase("error");
      setAllStatus("error");
      toast.error("No se pudo completar el procesamiento", {
        description:
          err instanceof Error ? err.message : String(err),
      });
    }
  };

  const handleClear = () => {
    setFiles([]);
    setSelectedOptions([]);
    setProcessingPhase("idle");
    setProgress(0);
    setResults([]);
    setJobId(null);
    toast.info("Selección limpiada");
  };

  const handleViewDetail = (id: string) => {
    // Sin vista previa por ahora: descargamos el documento.
    handleDownloadSingle(id);
  };

  const handleDownloadSingle = (id: string) => {
    if (!jobId) return;
    const result = results.find((r) => r.id === id);
    descargar(jobId, id);
    toast.success(`Descargando: ${result?.title ?? id}`, {
      description: result?.filename,
    });
  };

  const handleDownloadFromModal = (id: string) => {
    handleDownloadSingle(id);
    setShowDownloadModal(false);
  };

  return (
    <>
      <Toaster />
      <div className="min-h-screen flex flex-col bg-[#F9F9F9]">
        <Header />

        <Hero />

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
            currentStep={statusMessage}
            progress={progress}
          />
        )}

        {processingPhase === "error" && (
          <div className="w-full max-w-7xl mx-auto px-8 py-8">
            <div className="bg-white rounded-lg border border-red-200 p-6">
              <h3 className="text-xl font-medium text-red-700 mb-2">
                Ocurrió un error
              </h3>
              <p className="text-sm text-[#666666] mb-6">
                {statusMessage}. Revisa que el backend esté corriendo
                y que hayas iniciado sesión en NotebookLM.
              </p>
              <button
                onClick={handleClear}
                className="px-8 py-3 bg-[#205DF5] text-white rounded-lg hover:bg-opacity-90 transition-all"
              >
                Volver a empezar
              </button>
            </div>
          </div>
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
                  Documentos generados en formato Word (.docx).
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
          files={results}
          onClose={() => setShowDownloadModal(false)}
          onDownload={handleDownloadFromModal}
        />

        <Footer />
      </div>
    </>
  );
}
