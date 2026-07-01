import { FileText, Download, Eye, CheckCircle2 } from 'lucide-react';

interface ResultItem {
  id: string;
  title: string;
  description: string;
  date: string;
  status: 'ready' | 'processing';
}

interface ResultsProps {
  results: ResultItem[];
  onViewDetail: (id: string) => void;
  onDownload: (id: string) => void;
}

export function Results({ results, onViewDetail, onDownload }: ResultsProps) {
  if (results.length === 0) return null;

  return (
    <div className="w-full max-w-7xl mx-auto px-8 py-8">
      <h3 className="text-2xl font-medium text-[#000000] mb-6">Resultados</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {results.map((result) => (
          <div
            key={result.id}
            className="bg-white rounded-lg border border-[#E4E4E4] p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 bg-[#205DF5] bg-opacity-10 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-[#205DF5]" />
              </div>
              {result.status === 'ready' && (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              )}
            </div>

            <h4 className="text-lg font-medium text-[#000000] mb-2">
              {result.title}
            </h4>

            <p className="text-sm text-[#666666] mb-4">
              {result.description}
            </p>

            <div className="text-xs text-[#666666] mb-4">
              Generado: {result.date}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => onViewDetail(result.id)}
                className="flex-1 px-4 py-2 border border-[#205DF5] text-[#205DF5] rounded-lg hover:bg-[#205DF5] hover:bg-opacity-5 transition-colors flex items-center justify-center gap-2"
              >
                <Eye className="w-4 h-4" />
                Ver detalle
              </button>
              <button
                onClick={() => onDownload(result.id)}
                className="flex-1 px-4 py-2 bg-[#205DF5] text-white rounded-lg hover:bg-opacity-90 transition-colors flex items-center justify-center gap-2"
                disabled={result.status !== 'ready'}
              >
                <Download className="w-4 h-4" />
                Descargar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
