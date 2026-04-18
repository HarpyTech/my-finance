import React, { useState } from 'react';

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
  const [goal, setGoal] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [aiResponse, setAiResponse] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleGenerateAdvice = async () => {
    if (!goal.trim()) {
      setErrorMsg("Please enter a financial goal first.");
      return;
    }

    setIsGenerating(true);
    setErrorMsg("");
    setAiResponse("");

    const apiKey = ""; // API key is injected by the environment
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
    
    const systemInstruction = `You are the FinTrackr AI Assistant. Your brand philosophy is "Track. Grow. Simplify your finances." 
    The user will provide a financial goal or situation. 
    Your task: Break down their complex goal into exactly 3 simple, actionable, and trackable steps. 
    Keep the tone encouraging, highly professional, and brief. 
    Format the output as a numbered list. Do not use markdown bolding (**) in your response, just plain text with numbers.`;

    const payload = {
      contents: [{ parts: [{ text: `My financial goal is: ${goal}` }] }],
      systemInstruction: { parts: [{ text: systemInstruction }] }
    };

    let delay = 1000;
    const maxRetries = 5;
    let success = false;

    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
        
        if (text) {
          setAiResponse(text);
          success = true;
          break;
        } else {
          throw new Error("No text returned from Gemini");
        }
      } catch (err) {
        if (i === maxRetries - 1) {
          setErrorMsg("Oops! Our AI is taking a quick break. Please try again in a moment.");
          console.error("Gemini API Error:", err);
        } else {
          await new Promise(res => setTimeout(res, delay));
          delay *= 2;
        }
      }
    }
    
    setIsGenerating(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans text-slate-800">
      
      <header className="mb-12 text-center max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">FinTrackr Brand & Product Demo</h1>
        <p className="text-slate-500">
          Scroll down to see the brand assets and try the new AI-powered financial simplifier.
        </p>
      </header>

      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* 1. Full Stacked Logo */}
        <section className="bg-white rounded-2xl p-6 md:p-10 shadow-sm border border-slate-100 flex flex-col items-center">
          <div className="w-full flex justify-between items-center mb-10 border-b border-slate-100 pb-4">
            <h2 className="text-lg font-semibold text-slate-700">1. Main Brand Logo</h2>
            <span className="text-xs font-medium px-3 py-1 bg-slate-100 text-slate-500 rounded-full">Primary Use</span>
          </div>
          
          <div className="flex flex-col items-center justify-center py-8">
            <FinTrackrIcon className="w-32 h-32 mb-6 drop-shadow-sm" />
            <div className="text-5xl md:text-6xl font-extrabold tracking-tight mb-4 text-center">
              <span className="text-blue-900">Fin</span>
              <span className="text-emerald-500">Trackr</span>
            </div>
            <p className="text-lg md:text-xl text-slate-500 font-medium tracking-wide text-center">
              Track. Grow. Simplify your finances.
            </p>
          </div>
        </section>

        {/* ✨ NEW GEMINI API FEATURE SECTION ✨ */}
        <section className="bg-gradient-to-br from-blue-900 via-blue-800 to-emerald-900 rounded-2xl p-1 shadow-lg">
          <div className="bg-white rounded-xl p-6 md:p-10 h-full w-full">
            <div className="flex flex-col md:flex-row gap-8 items-start">
              
              <div className="flex-1 space-y-6">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-semibold mb-2 border border-emerald-100">
                  <span>✨ Powered by Gemini</span>
                </div>
                <h2 className="text-3xl font-bold text-slate-900">
                  Simplify Your Financial Goals
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Tell our AI assistant what you're trying to achieve. We'll apply the FinTrackr philosophy to break your complex goal down into three simple, trackable steps.
                </p>
                
                <div className="space-y-4">
                  <textarea 
                    className="w-full p-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all resize-none"
                    rows="3"
                    placeholder="E.g., I want to save $10,000 for a house down payment in the next 18 months..."
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                  />
                  
                  {errorMsg && <p className="text-red-500 text-sm font-medium">{errorMsg}</p>}
                  
                  <button 
                    onClick={handleGenerateAdvice}
                    disabled={isGenerating}
                    className="w-full md:w-auto px-8 py-3 bg-blue-900 hover:bg-blue-800 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Simplifying...
                      </>
                    ) : (
                      "Simplify My Goal ✨"
                    )}
                  </button>
                </div>
              </div>

              {/* AI Response Card */}
              <div className="flex-1 w-full bg-slate-50 rounded-2xl p-6 md:p-8 border border-slate-100 min-h-[300px] flex flex-col justify-center relative overflow-hidden">
                {!aiResponse && !isGenerating && (
                  <div className="text-center text-slate-400">
                    <FinTrackrIcon className="w-16 h-16 mx-auto mb-4 opacity-20 grayscale" />
                    <p>Your personalized, simplified plan will appear here.</p>
                  </div>
                )}

                {isGenerating && (
                  <div className="text-center space-y-4">
                    <div className="flex justify-center gap-2">
                      <div className="w-3 h-3 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-3 h-3 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <p className="text-slate-500 text-sm animate-pulse">Analyzing your finances...</p>
                  </div>
                )}

                {aiResponse && !isGenerating && (
                  <div className="relative z-10 animate-fade-in-up">
                    <h3 className="text-lg font-bold text-blue-900 mb-4 border-b border-slate-200 pb-2">Your Trackable Plan</h3>
                    <div className="text-slate-700 whitespace-pre-wrap leading-relaxed space-y-4">
                      {aiResponse}
                    </div>
                  </div>
                )}
                
                {/* Decorative Background for AI Card */}
                <div className="absolute top-0 right-0 -mr-16 -mt-16 opacity-5 pointer-events-none">
                  <FinTrackrIcon className="w-64 h-64" />
                </div>
              </div>

            </div>
          </div>
        </section>


        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          
          {/* 2. Horizontal Header Logo */}
          <section className="bg-white rounded-2xl p-6 md:p-10 shadow-sm border border-slate-100">
             <div className="w-full flex justify-between items-center mb-10 border-b border-slate-100 pb-4">
              <h2 className="text-lg font-semibold text-slate-700">2. Horizontal Layout</h2>
              <span className="text-xs font-medium px-3 py-1 bg-slate-100 text-slate-500 rounded-full">Website Navbars</span>
            </div>
            
            {/* Dark Mode Horizontal Logo */}
            <div className="w-full bg-slate-900 rounded-xl p-4 md:p-6 flex items-center justify-between mb-8 overflow-hidden">
              <div className="flex items-center gap-2 md:gap-3">
                <FinTrackrIcon className="w-8 h-8 md:w-10 md:h-10" />
                <div className="text-xl md:text-2xl font-extrabold tracking-tight">
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
            <div className="w-full bg-white border border-slate-200 rounded-xl p-4 md:p-6 flex items-center justify-between overflow-hidden">
              <div className="flex items-center gap-2 md:gap-3">
                <FinTrackrIcon className="w-8 h-8 md:w-10 md:h-10" />
                <div className="text-xl md:text-2xl font-extrabold tracking-tight">
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
          <section className="bg-white rounded-2xl p-6 md:p-10 shadow-sm border border-slate-100">
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