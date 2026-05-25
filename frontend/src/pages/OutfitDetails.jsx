import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { getOutfit } from "../utils/outfitStore";

export const OutfitDetails = () => {
  const { outfitId } = useParams();
  const navigate = useNavigate();

  // Load outfit details
  const outfit = getOutfit(outfitId);

  // States
  const [animateBars, setAnimateBars] = useState(false);
  const [isReserved, setIsReserved] = useState(false);

  // Scroll to top and trigger progress bar animations on mount
  useEffect(() => {
    window.scrollTo(0, 0);
    const mainEl = document.querySelector("main");
    if (mainEl) {
      mainEl.scrollTop = 0;
    }

    const timer = setTimeout(() => {
      setAnimateBars(true);
    }, 100);

    return () => clearTimeout(timer);
  }, [outfitId]);

  if (!outfit) {
    return (
      <Layout showBack={true} title="Manifest Error">
        <div className="text-center py-20">
          <span className="material-symbols-outlined text-5xl text-error mb-4">warning</span>
          <h3 className="font-display text-2xl italic text-on-surface mb-2">Outfit Not Found</h3>
          <p className="font-body-md text-xs text-on-surface-variant/70 mb-8">
            The curated outfit manifest could not be retrieved from the database.
          </p>
          <button
            onClick={() => navigate("/app/recommendations")}
            className="px-6 py-3 bg-on-surface text-background font-label-sm text-[10px] uppercase tracking-widest rounded font-bold"
          >
            Back to Recommendations
          </button>
        </div>
      </Layout>
    );
  }

  // Handle Acquire/Lock outfit
  const handleAcquire = () => {
    setIsReserved(true);

    // Create success toast notification
    const toast = document.createElement("div");
    toast.className = "fixed bottom-36 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[11px] uppercase tracking-[0.2em] shadow-2xl z-[99] border border-white/10 animate-fade-in flex items-center gap-2";
    toast.innerHTML = `<span class="material-symbols-outlined text-sm font-bold text-tertiary">today</span> Outfit Scheduled on Calendar Planner`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.classList.add("animate-fade-out");
      setTimeout(() => {
        toast.remove();
        navigate("/app/planner");
      }, 400);
    }, 2000);
  };

  return (
    <Layout showBack={true} title="Curation Manifest">
      <div className="w-full relative pb-20 max-w-container-max mx-auto animate-fade-in">
        
        {/* Top Hero Image Spotlight */}
        <section className="relative w-full aspect-[4/5] sm:aspect-[16/7] md:rounded-2xl overflow-hidden mb-8 group border border-white/5 shadow-2xl">
          <img
            className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-103"
            src={outfit.heroImage}
            alt={outfit.name}
          />
          {/* Bottom text overlays */}
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent opacity-80 z-10"></div>
          <div className="absolute bottom-6 left-6 z-20 max-w-lg select-none">
            <span className="font-label-sm text-[10px] text-tertiary uppercase tracking-[0.25em] mb-1 block font-bold">
              {outfit.subtitle}
            </span>
            <h2 className="font-display text-3xl sm:text-4xl text-white italic luxury-text-gradient mb-2 leading-none">
              {outfit.name}
            </h2>
            <p className="hidden sm:block font-body-md text-xs text-on-surface-variant/80 font-light leading-relaxed">
              {outfit.description}
            </p>
          </div>
        </section>

        {/* 2-column e-commerce grid splits */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
          
          {/* Left Column: VOGUE Score & AI reasoning (col-span-4) */}
          <div className="lg:col-span-4 flex flex-col gap-gutter lg:sticky lg:top-32">
            
            {/* VOGUE Score Card */}
            <div className="glass p-6 rounded-2xl shadow-xl border border-white/5">
              <div className="flex items-center justify-between mb-8 select-none">
                <h3 className="font-display text-xl italic text-on-surface">VOGUE Score</h3>
                <span className="font-display text-4xl vogue-gradient font-bold">{outfit.vogueScore}</span>
              </div>

              {/* Animated Progress Bars */}
              <div className="space-y-5">
                {[
                  { label: "Color Harmony", value: outfit.metrics.colorHarmony },
                  { label: "Style Alignment", value: outfit.metrics.styleAlignment },
                  { label: "Occasion Context", value: outfit.metrics.occasionContext },
                  { label: "Formality Balance", value: outfit.metrics.formalityBalance },
                  { label: "Season Appropriateness", value: outfit.metrics.seasonAppropriateness }
                ].map((item, index) => (
                  <div key={index} className="space-y-1.5 select-none">
                    <div className="flex justify-between font-label-sm text-[9px] uppercase tracking-wider text-on-surface-variant font-semibold">
                      <span>{item.label}</span>
                      <span className="text-tertiary font-bold">{item.value}</span>
                    </div>
                    <div className="h-[2px] w-full bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-tertiary rounded-full"
                        style={{
                          width: animateBars ? `${item.value}%` : "0%",
                          transition: "width 1.5s cubic-bezier(0.65, 0, 0.35, 1)"
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Reasoning Panel */}
            <div className="glass p-6 rounded-2xl border-l-2 border-tertiary/40 shadow-xl border border-white/5">
              <h3 className="font-display text-lg italic text-on-surface mb-6 flex items-center gap-2 select-none">
                <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>
                  auto_awesome
                </span>
                AI Reasoning Analysis
              </h3>
              
              <ul className="space-y-4">
                {outfit.reasoning.map((item, index) => (
                  <li key={index} className="flex gap-3 items-start select-none">
                    <span className="text-tertiary mt-2 shrink-0">
                      <svg fill="currentColor" height="5" viewBox="0 0 6 6" width="5">
                        <circle cx="3" cy="3" r="3"></circle>
                      </svg>
                    </span>
                    <p className="font-body-md text-xs text-on-surface-variant/80 font-light leading-relaxed">
                      {item}
                    </p>
                  </li>
                ))}
              </ul>
            </div>

          </div>

          {/* Right Column: Curation Manifest of Wardrobe Items (col-span-8) */}
          <div className="lg:col-span-8">
            <div className="flex flex-col gap-gutter">
              
              {/* Manifest Header */}
              <div className="flex justify-between items-end border-b border-white/5 pb-4 select-none">
                <h3 className="font-display text-xl italic text-on-surface">Curation Manifest</h3>
                <span className="font-label-sm text-[9px] text-on-surface-variant uppercase tracking-widest font-semibold">
                  {outfit.items.length} Items Total
                </span>
              </div>

              {/* Items Card List */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {outfit.items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => navigate(`/app/item/${item.categoryId}/${item.id}`)}
                    className="group relative overflow-hidden rounded-xl bg-surface-container-low border border-white/5 p-4 flex gap-4 hover:bg-white/[0.02] hover:border-white/15 transition-all duration-300 shadow-md cursor-pointer active:scale-[0.99]"
                  >
                    {/* Thumbnail Image */}
                    <div className="w-20 h-24 rounded bg-background overflow-hidden shrink-0 border border-white/5 shadow-inner">
                      <img
                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                        src={item.image}
                        alt={item.name}
                      />
                    </div>
                    {/* Item Information */}
                    <div className="flex flex-col justify-center overflow-hidden">
                      <p className="font-label-sm text-[8px] text-tertiary uppercase tracking-widest mb-1 font-semibold select-none">
                        {item.categoryLabel}
                      </p>
                      <h4 className="font-display text-[15px] text-on-surface leading-tight mb-1.5 italic group-hover:text-tertiary transition-colors truncate">
                        {item.name}
                      </h4>
                      <p className="text-on-surface-variant/60 text-[11px] font-light leading-snug truncate">
                        {item.textile}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Reserve Outfit Action Card */}
              <div className="mt-4 glass p-8 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 border border-tertiary/20 shadow-2xl relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-r from-tertiary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
                <div className="select-none">
                  <h4 className="font-display text-xl italic text-on-surface mb-1">Schedule this Look</h4>
                  <p className="font-body-md text-xs text-on-surface-variant/75 font-light leading-relaxed">
                    Map this curated outfit directly into your capsule calendar.
                  </p>
                </div>
                <button
                  onClick={handleAcquire}
                  disabled={isReserved}
                  className="bg-on-surface text-background px-8 py-4 font-label-sm text-[10px] uppercase tracking-widest rounded-lg hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 transform active:scale-95 font-bold shadow-lg cursor-pointer disabled:opacity-50"
                >
                  {isReserved ? "Outfit Scheduled" : "Acquire Outfit"}
                </button>
              </div>

            </div>
          </div>

        </div>

      </div>
    </Layout>
  );
};

export default OutfitDetails;
