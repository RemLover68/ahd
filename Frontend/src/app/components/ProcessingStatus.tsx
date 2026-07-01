import { Loader2 } from 'lucide-react';

interface ProcessingStatusProps {
  currentStep: string;
  progress: number;
}

export function ProcessingStatus({ currentStep, progress }: ProcessingStatusProps) {
  return (
    <div className="w-full max-w-7xl mx-auto px-8 py-8">
      <div className="bg-white rounded-lg border border-[#E4E4E4] p-8">
        <div className="flex items-center gap-4 mb-6">
          <Loader2 className="w-6 h-6 text-[#205DF5] animate-spin" />
          <h3 className="text-xl font-medium text-[#000000]">Procesando documentos...</h3>
        </div>

        <div className="mb-4">
          <div className="flex justify-between text-sm text-[#666666] mb-2">
            <span>{currentStep}</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-2 bg-[#E4E4E4] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#205DF5] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <p className="text-sm text-[#666666]">
          Este proceso puede tomar algunos minutos dependiendo del tamaño y cantidad de documentos.
        </p>
      </div>
    </div>
  );
}
