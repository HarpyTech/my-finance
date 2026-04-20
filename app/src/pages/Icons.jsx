import React from 'react';

// --- Reusable SVG Icon Component ---
const FinTrackrIcon = ({ className = "w-16 h-16", variant = "colorful" }) => {
  const isWhite = variant === "white";
  
  return (
    <svg 
      className={className} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="gradBlue" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={isWhite ? "#ffffff" : "#1e3a8a"} />
          <stop offset="100%" stopColor={isWhite ? "#e2e8f0" : "#3b82f6"} />
        </linearGradient>
        <linearGradient id="gradGreen" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={isWhite ? "#ffffff" : "#059669"} />
          <stop offset="100%" stopColor={isWhite ? "#f8fafc" : "#10b981"} />
        </linearGradient>
      </defs>

      {/* Background Circle (Optional, for structure) */}
      {!isWhite && (
         <circle cx="50" cy="50" r="48" fill="#f0fdf4" opacity="0.5" />
      )}

      {/* Bar Chart representing "Track" */}
      <rect x="22" y="55" width="14" height="25" rx="3" fill="url(#gradBlue)" opacity={isWhite ? 0.7 : 0.85} />
      <rect x="44" y="38" width="14" height="42" rx="3" fill="url(#gradBlue)" opacity={isWhite ? 0.85 : 0.95} />
      <rect x="66" y="20" width="14" height="60" rx="3" fill="url(#gradBlue)" opacity="1" />

      {/* Dynamic Arrow representing "Grow" */}
      <path 
        d="M 12 72 L 34 48 L 52 62 L 85 24" 
        stroke="url(#gradGreen)" 
        strokeWidth="8" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        fill="none" 
      />
      
      {/* Arrow Head */}
      <path 
        d="M 65 24 L 85 24 L 85 44" 
        stroke="url(#gradGreen)" 
        strokeWidth="8" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        fill="none" 
      />
    </svg>
  );
};


// --- Presentation Layout ---
export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-800">
      
      <header className="mb-12 text-center max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">FinTrackr Brand Assets</h1>
        <p className="text-slate-500">
          Scalable, vector-based logo variations ready for web and app implementation. 
          Built with React and SVG.
        </p>
      </header>

      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* 1. Full Stacked Logo */}
        <section className="bg-white rounded-2xl p-10 shadow-sm border border-slate-100 flex flex-col items-center">
          <div className="w-full flex justify-between items-center mb-10 border-b border-slate-100 pb-4">
            <h2 className="text-lg font-semibold text-slate-700">1. Main Brand Logo</h2>
            <span className="text-xs font-medium px-3 py-1 bg-slate-100 text-slate-500 rounded-full">Primary Use</span>
          </div>
          
          <div className="flex flex-col items-center justify-center py-12">
            <FinTrackrIcon className="w-32 h-32 mb-6 drop-shadow-sm" />
            <div className="text-6xl font-extrabold tracking-tight mb-4">
              <span className="text-blue-900">Fin</span>
              <span className="text-emerald-500">Trackr</span>
            </div>
            <p className="text-xl text-slate-500 font-medium tracking-wide">
              Track. Grow. Simplify your finances.
            </p>
          </div>
        </section>


        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          
          {/* 2. Horizontal Header Logo */}
          <section className="bg-white rounded-2xl p-10 shadow-sm border border-slate-100">
             <div className="w-full flex justify-between items-center mb-10 border-b border-slate-100 pb-4">
              <h2 className="text-lg font-semibold text-slate-700">2. Horizontal Layout</h2>
              <span className="text-xs font-medium px-3 py-1 bg-slate-100 text-slate-500 rounded-full">Website Navbars</span>
            </div>
            
            {/* Example Navbar Context */}
            <div className="w-full bg-slate-900 rounded-xl p-6 flex items-center justify-between mb-8">
              {/* Dark Mode Horizontal Logo */}
              <div className="flex items-center gap-3">
                <FinTrackrIcon className="w-10 h-10" />
                <div className="text-2xl font-extrabold tracking-tight">
                  <span className="text-white">Fin</span>
                  <span className="text-emerald-400">Trackr</span>
                </div>
              </div>
              <div className="hidden sm:flex gap-4 text-sm text-slate-300">
                <span>Features</span>
                <span>Pricing</span>
              </div>
            </div>

            {/* Light Mode Horizontal Logo */}
            <div className="w-full bg-white border border-slate-200 rounded-xl p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FinTrackrIcon className="w-10 h-10" />
                <div className="text-2xl font-extrabold tracking-tight">
                  <span className="text-blue-900">Fin</span>
                  <span className="text-emerald-500">Trackr</span>
                </div>
              </div>
              <div className="hidden sm:flex gap-4 text-sm text-slate-500">
                <span>Features</span>
                <span>Pricing</span>
              </div>
            </div>
          </section>


          {/* 3. App Icon / Favicon */}
          <section className="bg-white rounded-2xl p-10 shadow-sm border border-slate-100">
            <div className="w-full flex justify-between items-center mb-10 border-b border-slate-100 pb-4">
              <h2 className="text-lg font-semibold text-slate-700">3. App Icon & Favicon</h2>
              <span className="text-xs font-medium px-3 py-1 bg-slate-100 text-slate-500 rounded-full">Mobile & Tab</span>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-12 py-8">
              
              {/* iOS Style App Icon */}
              <div className="flex flex-col items-center gap-4">
                <div className="w-32 h-32 rounded-3xl bg-gradient-to-br from-blue-900 via-blue-800 to-emerald-600 p-5 shadow-xl flex items-center justify-center">
                   <FinTrackrIcon className="w-full h-full drop-shadow-md" variant="white" />
                </div>
                <span className="text-sm font-medium text-slate-400">iOS App Icon</span>
              </div>

              {/* Favicon Style */}
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-xl bg-white shadow-md border border-slate-100 flex items-center justify-center p-2">
                   <FinTrackrIcon className="w-full h-full" variant="colorful" />
                </div>
                <span className="text-sm font-medium text-slate-400">Favicon (64x64)</span>
              </div>

            </div>
          </section>

        </div>
      </div>
    </div>
  );
}