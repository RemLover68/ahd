import { useState } from 'react';

interface ConfigOption {
  id: string;
  label: string;
  description: string;
}

const configOptions: ConfigOption[] = [
  {
    id: 'propuesta',
    label: 'Generar propuesta técnica propositiva',
    description: 'Crea una propuesta técnica adaptada a los requerimientos de SmartCities & Mobility',
  },
  {
    id: 'equipos',
    label: 'Extraer equipos para cotización',
    description: 'Identifica y lista todos los equipos, hardware y software requeridos',
  },
  {
    id: 'aclaraciones',
    label: 'Detectar cambios en aclaraciones',
    description: 'Analiza circulares y aclaraciones para identificar modificaciones importantes',
  },
  {
    id: 'matriz',
    label: 'Generar matriz de cumplimiento',
    description: 'Crea tabla de cumplimiento técnico y legal según bases de licitación',
  },
  {
    id: 'riesgos',
    label: 'Identificar riesgos técnicos',
    description: 'Detecta posibles riesgos técnicos, plazos ajustados y requerimientos complejos',
  },
  {
    id: 'clasificar',
    label: 'Clasificar requerimientos SmartCities & Mobility',
    description: 'Categoriza por área: transporte, movilidad, ITS, seguridad, fiscalización, etc.',
  },
];

interface AnalysisConfigProps {
  selectedOptions: string[];
  onOptionsChange: (options: string[]) => void;
}

export function AnalysisConfig({ selectedOptions, onOptionsChange }: AnalysisConfigProps) {
  const toggleOption = (id: string) => {
    if (selectedOptions.includes(id)) {
      onOptionsChange(selectedOptions.filter((opt) => opt !== id));
    } else {
      onOptionsChange([...selectedOptions, id]);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-8 py-8">
      <div className="bg-white rounded-lg border border-[#E4E4E4] p-6">
        <h3 className="text-xl font-medium text-[#000000] mb-6">
          Configuración del análisis
        </h3>
        <div className="space-y-4">
          {configOptions.map((option) => (
            <label
              key={option.id}
              className="flex items-start gap-4 p-4 rounded-lg hover:bg-[#E4E4E4] hover:bg-opacity-30 cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                checked={selectedOptions.includes(option.id)}
                onChange={() => toggleOption(option.id)}
                className="mt-1 w-5 h-5 accent-[#205DF5] cursor-pointer"
              />
              <div className="flex-1">
                <div className="text-base font-medium text-[#000000] mb-1">
                  {option.label}
                </div>
                <div className="text-sm text-[#666666]">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
