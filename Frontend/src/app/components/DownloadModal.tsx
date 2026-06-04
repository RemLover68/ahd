import { X, FileText, Download } from 'lucide-react';

interface DownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownload: (format: string) => void;
}

const downloadOptions = [
  {
    id: 'word',
    title: 'Propuesta técnica',
    format: 'Word (.docx)',
    description: 'Documento completo con propuesta técnica propositiva',
  },
  {
    id: 'excel',
    title: 'Matriz de cumplimiento',
    format: 'Excel (.xlsx)',
    description: 'Tabla detallada de cumplimiento técnico y legal',
  },
  {
    id: 'pdf',
    title: 'Resumen ejecutivo',
    format: 'PDF',
    description: 'Resumen consolidado para revisión comercial',
  },
  {
    id: 'zip',
    title: 'Paquete completo',
    format: 'ZIP',
    description: 'Todos los entregables en formato corporativo SONDA',
  },
];

export function DownloadModal({ isOpen, onClose, onDownload }: DownloadModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
        <div className="sticky top-0 bg-white border-b border-[#E4E4E4] px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-medium text-[#000000]">
            Descargar resultados
          </h2>
          <button
            onClick={onClose}
            className="text-[#666666] hover:text-[#000000] transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          <p className="text-sm text-[#666666] mb-6">
            Selecciona el formato que deseas descargar. Todos los archivos están en formato corporativo SONDA.
          </p>

          <div className="space-y-4">
            {downloadOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => onDownload(option.id)}
                className="w-full p-4 border border-[#E4E4E4] rounded-lg hover:border-[#205DF5] hover:bg-[#205DF5] hover:bg-opacity-5 transition-all text-left group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-[#E4E4E4] group-hover:bg-[#205DF5] group-hover:bg-opacity-10 rounded-lg flex items-center justify-center transition-colors">
                    <FileText className="w-6 h-6 text-[#666666] group-hover:text-[#205DF5] transition-colors" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-base font-medium text-[#000000]">
                        {option.title}
                      </h4>
                      <span className="text-xs text-[#666666] bg-[#E4E4E4] px-2 py-1 rounded">
                        {option.format}
                      </span>
                    </div>
                    <p className="text-sm text-[#666666]">{option.description}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-[#E4E4E4] flex gap-4">
            <button
              onClick={() => onDownload('zip')}
              className="flex-1 px-6 py-3 bg-[#205DF5] text-white rounded-lg hover:bg-opacity-90 transition-colors flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Descargar paquete completo
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 border border-[#E4E4E4] text-[#3D3D3D] rounded-lg hover:bg-[#E4E4E4] hover:bg-opacity-30 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
