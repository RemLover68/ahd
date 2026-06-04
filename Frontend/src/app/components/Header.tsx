export function Header() {
  return (
    <header className="w-full bg-white border-b border-[#E4E4E4] px-8 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div>
            <div className="text-2xl font-bold text-[#205DF5]" style={{ fontFamily: 'Kumbh Sans, sans-serif' }}>
              SONDA
            </div>
            <div className="text-xs text-[#666666] -mt-1">make it easy</div>
          </div>
        </div>
        <div className="text-sm text-[#3D3D3D]" style={{ fontFamily: 'Kumbh Sans, sans-serif' }}>
          SmartCities & Mobility · Asistente de licitaciones
        </div>
      </div>
    </header>
  );
}
