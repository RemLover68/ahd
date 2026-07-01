import { Upload } from 'lucide-react';
import { useRef } from 'react';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export function FileUpload({ onFilesSelected, disabled }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    onFilesSelected(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      onFilesSelected(files);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-8 py-8">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-[#E4E4E4] rounded-lg p-12 bg-white hover:border-[#205DF5] transition-colors cursor-pointer"
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-[#205DF5] bg-opacity-10 rounded-full flex items-center justify-center">
            <Upload className="w-8 h-8 text-[#205DF5]" />
          </div>
          <div className="text-center">
            <h3 className="text-xl font-medium text-[#000000] mb-2">
              Sube tus documentos
            </h3>
            <p className="text-sm text-[#666666] mb-4">
              Arrastra bases técnicas, anexos, preguntas, respuestas, circulares o planillas.
            </p>
            <div className="flex gap-2 justify-center flex-wrap">
              {['PDF', 'DOCX', 'XLSX', 'ZIP'].map((format) => (
                <span
                  key={format}
                  className="px-3 py-1 bg-[#E4E4E4] text-[#3D3D3D] rounded-full text-xs"
                >
                  {format}
                </span>
              ))}
            </div>
          </div>
          <button
            className="mt-4 px-6 py-3 bg-[#205DF5] text-white rounded-lg hover:bg-opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={disabled}
          >
            Subir archivos
          </button>
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.xlsx,.zip"
        onChange={handleFileInput}
        className="hidden"
      />
    </div>
  );
}
