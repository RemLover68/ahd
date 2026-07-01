export function Footer() {
  return (
    <footer className="w-full bg-white border-t border-[#E4E4E4] px-8 py-6 mt-auto">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <p className="text-sm text-[#666666]">
          SONDA S.A. · SmartCities & Mobility · Herramienta interna de apoyo a licitaciones
        </p>
        <a
          href="#"
          className="text-sm text-[#205DF5] hover:underline"
          onClick={(e) => e.preventDefault()}
        >
          Confidencialidad y uso interno
        </a>
      </div>
    </footer>
  );
}
