import { X } from 'lucide-react';

export type FileStatus = 'pending' | 'uploading' | 'processing' | 'ready' | 'error';

export interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  status: FileStatus;
  // Archivo real seleccionado por el usuario, necesario para subirlo al backend.
  file?: File;
}

interface FileListProps {
  files: FileItem[];
  onRemoveFile: (id: string) => void;
}

const statusConfig = {
  pending: { label: 'Pendiente', color: 'bg-[#E4E4E4] text-[#666666]' },
  uploading: { label: 'Cargando', color: 'bg-[#205DF5] bg-opacity-10 text-[#205DF5]' },
  processing: { label: 'Procesando', color: 'bg-[#205DF5] bg-opacity-10 text-[#205DF5]' },
  ready: { label: 'Listo', color: 'bg-green-100 text-green-700' },
  error: { label: 'Error', color: 'bg-red-100 text-red-700' },
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export function FileList({ files, onRemoveFile }: FileListProps) {
  if (files.length === 0) return null;

  return (
    <div className="w-full max-w-7xl mx-auto px-8 py-4">
      <div className="bg-white rounded-lg border border-[#E4E4E4] overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#E4E4E4] bg-opacity-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-[#3D3D3D]">
                Nombre del archivo
              </th>
              <th className="px-6 py-3 text-left text-sm font-medium text-[#3D3D3D]">
                Tipo
              </th>
              <th className="px-6 py-3 text-left text-sm font-medium text-[#3D3D3D]">
                Tamaño
              </th>
              <th className="px-6 py-3 text-left text-sm font-medium text-[#3D3D3D]">
                Estado
              </th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E4E4E4]">
            {files.map((file) => (
              <tr key={file.id} className="hover:bg-[#E4E4E4] hover:bg-opacity-30 transition-colors">
                <td className="px-6 py-4 text-sm text-[#000000]">{file.name}</td>
                <td className="px-6 py-4 text-sm text-[#666666]">{file.type}</td>
                <td className="px-6 py-4 text-sm text-[#666666]">{formatFileSize(file.size)}</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs ${statusConfig[file.status].color}`}
                  >
                    {statusConfig[file.status].label}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => onRemoveFile(file.id)}
                    className="text-[#666666] hover:text-[#205DF5] transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
