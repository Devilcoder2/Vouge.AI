import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { getOutfits } from "../utils/outfitStore";

export const Suggestions = () => {
  const navigate = useNavigate();
  const outfits = getOutfits();

  // Swiper Deck States (Mobile)
  const [currentIndex, setCurrentIndex] = useState(0);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState(null); // 'keep' or 'discard' or null
  const [toastMsg, setToastMsg] = useState("");

  const startPos = useRef({ x: 0, y: 0 });
  const cardRef = useRef(null);

  // Desktop Specific States (Grid View States)
  const [desktopStates, setDesktopStates] = useState({});

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const currentOutfit = outfits[currentIndex] || null;

  // Swipe Action Handlers (Mobile)
  const handleSwipe = (direction) => {
    setSwipeDirection(direction);
    
    // Create toast notification
    if (direction === "keep") {
      setToastMsg(`Added "${outfits[currentIndex].name}" to Saved Wardrobe`);
    } else {
      setToastMsg(`Skipped "${outfits[currentIndex].name}"`);
    }

    setTimeout(() => {
      setToastMsg("");
    }, 1500);

    // Animate out and increment index
    setTimeout(() => {
      setCurrentIndex((prev) => prev + 1);
      setDragOffset({ x: 0, y: 0 });
      setSwipeDirection(null);
    }, 300);
  };

  // Drag Events (Mobile Mouse and Touch support)
  const handleDragStart = (clientX, clientY) => {
    if (swipeDirection) return;
    setIsDragging(true);
    startPos.current = { x: clientX, y: clientY };
  };

  const handleDragMove = (clientX, clientY) => {
    if (!isDragging) return;
    const xDiff = clientX - startPos.current.x;
    const yDiff = clientY - startPos.current.y;
    setDragOffset({ x: xDiff, y: yDiff });
  };

  const handleDragEnd = () => {
    if (!isDragging) return;
    setIsDragging(false);

    const threshold = 120;
    if (dragOffset.x > threshold) {
      handleSwipe("keep");
    } else if (dragOffset.x < -threshold) {
      handleSwipe("discard");
    } else {
      // Spring back to center
      setDragOffset({ x: 0, y: 0 });
    }
  };

  // Event bridges for Mouse (Mobile)
  const onMouseDown = (e) => handleDragStart(e.clientX, e.clientY);
  const onMouseMove = (e) => handleDragMove(e.clientX, e.clientY);
  const onMouseUp = () => handleDragEnd();

  // Event bridges for Touch (Mobile)
  const onTouchStart = (e) => handleDragStart(e.touches[0].clientX, e.touches[0].clientY);
  const onTouchMove = (e) => handleDragMove(e.touches[0].clientX, e.touches[0].clientY);
  const onTouchEnd = () => handleDragEnd();

  // Calculate card styling during drag or swipe animation (Mobile)
  const getCardStyle = () => {
    if (swipeDirection) {
      const transformX = swipeDirection === "keep" ? 600 : -600;
      const rotateDeg = swipeDirection === "keep" ? 25 : -25;
      return {
        transform: `translateX(${transformX}px) rotate(${rotateDeg}deg)`,
        opacity: 0,
        transition: "all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
      };
    }

    if (isDragging) {
      const rotateDeg = dragOffset.x / 15;
      return {
        transform: `translateX(${dragOffset.x}px) translateY(${dragOffset.y}px) rotate(${rotateDeg}deg)`,
        transition: "none"
      };
    }

    return {
      transform: "translateX(0px) translateY(0px) rotate(0deg)",
      transition: "all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
    };
  };

  // Desktop Curation Actions
  const handleDesktopLike = (id, name) => {
    const isCurrentlyLiked = !!desktopStates[id]?.liked;
    setDesktopStates((prev) => ({
      ...prev,
      [id]: { ...prev[id], liked: !isCurrentlyLiked },
    }));
    setToastMsg(
      isCurrentlyLiked
        ? `Removed "${name}" from Saved Wardrobe`
        : `Added "${name}" to Saved Wardrobe`
    );
    setTimeout(() => {
      setToastMsg("");
    }, 1500);
  };

  const handleDesktopSkip = (id, name) => {
    const isCurrentlySkipped = !!desktopStates[id]?.skipped;
    setDesktopStates((prev) => ({
      ...prev,
      [id]: { ...prev[id], skipped: !isCurrentlySkipped },
    }));
    setToastMsg(isCurrentlySkipped ? `Restored "${name}"` : `Skipped "${name}"`);
    setTimeout(() => {
      setToastMsg("");
    }, 1500);
  };

  return (
    <Layout title="Recommended Outfits">
      <div className="relative w-full min-h-[calc(100vh-140px)] flex flex-col items-center justify-center -mt-4">
        
        {/* Background Atmospheric Blur Glows */}
        <div className="absolute inset-0 z-0 opacity-20 pointer-events-none select-none">
          <div className="absolute top-1/4 -left-20 w-80 h-80 bg-tertiary-fixed-dim rounded-full blur-[120px]"></div>
          <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-primary rounded-full blur-[120px]"></div>
        </div>

        {/* Global Toast Message Feedback */}
        {toastMsg && (
          <div className="fixed top-24 left-1/2 -translate-x-1/2 bg-on-surface text-background px-6 py-3 rounded-full font-label-sm text-[10px] uppercase tracking-[0.2em] shadow-2xl z-[70] border border-white/10 animate-fade-in flex items-center gap-2 select-none">
            <span className="material-symbols-outlined text-sm font-bold text-tertiary">
              {toastMsg.includes("Added") || toastMsg.includes("Restored") ? "favorite" : "close"}
            </span>
            {toastMsg}
          </div>
        )}

        {/* ==================== DESKTOP LAYOUT (Grid list of all outfits) ==================== */}
        <div className="hidden md:block w-full max-w-container-max mx-auto px-4 py-8 pb-24 z-10 animate-fade-in">
          <div className="mb-10 select-none">
            <h2 className="font-display text-4xl italic luxury-text-gradient mb-2">Recommended Outfits</h2>
            <p className="font-body-md text-on-surface-variant/40 tracking-[0.2em] uppercase text-[9px] font-semibold">
              AI-suggested ensembles curated from your wardrobe collection
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {outfits.map((outfit) => {
              const state = desktopStates[outfit.id] || { liked: false, skipped: false };
              return (
                <div
                  key={outfit.id}
                  className={`relative rounded-2xl overflow-hidden glass border border-white/[0.08] flex flex-col h-[520px] shadow-xl group transition-all duration-500 ${
                    state.skipped ? "opacity-35 scale-[0.97] grayscale" : "hover:border-white/15 hover:scale-[1.01]"
                  }`}
                >
                  {/* Skip Overlay */}
                  {state.skipped && (
                    <div className="absolute inset-0 bg-background/85 backdrop-blur-sm z-30 flex flex-col items-center justify-center p-6 text-center animate-fade-in pointer-events-auto">
                      <span className="material-symbols-outlined text-4xl text-on-surface-variant/40 mb-3 select-none">
                        visibility_off
                      </span>
                      <h4 className="font-display text-lg italic text-on-surface-variant mb-1 select-none">
                        Curation Discarded
                      </h4>
                      <p className="font-body-md text-[11px] text-on-surface-variant/60 mb-6 max-w-[200px] leading-relaxed select-none">
                        This styling suggestion has been skipped.
                      </p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDesktopSkip(outfit.id, outfit.name);
                        }}
                        className="px-6 py-2.5 bg-white text-background font-label-sm text-[9px] uppercase tracking-widest rounded hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-lg cursor-pointer"
                      >
                        Restore Outfit
                      </button>
                    </div>
                  )}

                  {/* Card Spotlight Image (Top 50%) */}
                  <div className="relative h-[260px] overflow-hidden shrink-0 border-b border-white/5">
                    <img
                      src={outfit.heroImage}
                      alt={outfit.name}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-103"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent z-10"></div>
                    
                    {/* Badge Overlays */}
                    <div className="absolute bottom-4 left-4 z-20 flex gap-2">
                      <div className="bg-[#1A1A1A]/70 backdrop-blur-xl border border-white/10 px-2.5 py-1 rounded-full flex items-center gap-1">
                        <span className="material-symbols-outlined text-[12px] text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>
                          wb_sunny
                        </span>
                        <span className="font-label-sm text-[8px] text-on-surface uppercase tracking-wider font-semibold">
                          {outfit.weather}
                        </span>
                      </div>
                      <div className="bg-[#1A1A1A]/70 backdrop-blur-xl border border-white/10 px-2.5 py-1 rounded-full flex items-center gap-1">
                        <span className="material-symbols-outlined text-[12px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
                          event
                        </span>
                        <span className="font-label-sm text-[8px] text-on-surface uppercase tracking-wider font-semibold">
                          {outfit.occasion}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Card Content (Bottom 50%) */}
                  <div className="p-6 flex flex-col justify-between flex-1 select-none">
                    <div>
                      <span className="font-label-sm text-[9px] text-tertiary/80 uppercase tracking-[0.2em] block font-bold mb-1">
                        {outfit.subtitle}
                      </span>
                      <h3 className="font-display text-xl text-white mb-2 italic">
                        {outfit.name}
                      </h3>
                      <p className="font-body-md text-xs text-on-surface-variant/75 line-clamp-3 leading-relaxed font-light mb-6">
                        {outfit.description}
                      </p>
                    </div>

                    {/* Actions Panel */}
                    <div className="flex gap-3 mt-auto">
                      <button
                        onClick={() => navigate(`/app/outfit/${outfit.id}`)}
                        className="flex-1 bg-white text-background font-label-sm text-[10px] uppercase py-3.5 rounded-lg tracking-widest hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-md cursor-pointer"
                      >
                        View Details
                      </button>

                      {/* Like Action */}
                      <button
                        onClick={() => handleDesktopLike(outfit.id, outfit.name)}
                        className={`w-12 h-12 rounded-lg flex items-center justify-center border transition-all duration-300 shadow-md cursor-pointer ${
                          state.liked 
                            ? "bg-tertiary border-tertiary text-on-tertiary" 
                            : "bg-white/5 border-white/10 text-primary hover:bg-white/10"
                        }`}
                        title={state.liked ? "Remove from Saved" : "Save Outfit"}
                      >
                        <span 
                          className="material-symbols-outlined text-lg" 
                          style={{ fontVariationSettings: state.liked ? "'FILL' 1" : "'FILL' 0" }}
                        >
                          favorite
                        </span>
                      </button>

                      {/* Skip Action */}
                      <button
                        onClick={() => handleDesktopSkip(outfit.id, outfit.name)}
                        className="w-12 h-12 bg-white/5 border border-white/10 rounded-lg flex items-center justify-center text-primary hover:bg-error/15 hover:border-error/30 hover:text-error transition-all duration-300 shadow-md cursor-pointer"
                        title="Skip Curation"
                      >
                        <span className="material-symbols-outlined text-lg">
                          close
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ==================== MOBILE LAYOUT (Tinder Swipe deck) ==================== */}
        <div className="md:hidden w-full flex-1 flex flex-col items-center justify-center z-10 overflow-hidden">
          {currentOutfit ? (
            <div className="w-full flex items-center justify-center relative select-none animate-fade-in">
              
              {/* Swipe Indicators */}
              <div 
                className={`absolute left-4 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 indicator-pulse transition-opacity duration-300 ${
                  dragOffset.x < -40 ? "opacity-100 scale-105" : "opacity-30"
                }`}
              >
                <span className="material-symbols-outlined text-primary text-3xl font-light">chevron_left</span>
                <span className="text-[9px] uppercase tracking-[0.2em] transform -rotate-90 origin-center translate-y-6 font-semibold text-primary">
                  Discard
                </span>
              </div>

              <div 
                className={`absolute right-4 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 indicator-pulse transition-opacity duration-300 ${
                  dragOffset.x > 40 ? "opacity-100 scale-105" : "opacity-30"
                }`}
              >
                <span className="material-symbols-outlined text-primary text-3xl font-light">chevron_right</span>
                <span className="text-[9px] uppercase tracking-[0.2em] transform rotate-90 origin-center translate-y-6 font-semibold text-primary">
                  Keep
                </span>
              </div>

              {/* Swipe Card Deck */}
              <div 
                className="relative w-[calc(100%-40px)] max-w-[380px] aspect-[4/5.6] z-20 cursor-grab active:cursor-grabbing"
                onMouseDown={onMouseDown}
                onMouseMove={onMouseMove}
                onMouseUp={onMouseUp}
                onMouseLeave={onMouseUp}
                onTouchStart={onTouchStart}
                onTouchMove={onTouchMove}
                onTouchEnd={onTouchEnd}
              >
                <div
                  ref={cardRef}
                  style={getCardStyle()}
                  className="swipe-card absolute inset-0 rounded-2xl overflow-hidden shadow-2xl glass border border-white/[0.08]"
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/35 to-transparent z-10"></div>
                  
                  <img
                    alt={currentOutfit.name}
                    className="w-full h-full object-cover pointer-events-none select-none"
                    src={currentOutfit.heroImage}
                  />

                  <div className="absolute bottom-0 left-0 w-full p-6 z-20 flex flex-col justify-end">
                    <div className="flex items-center gap-2 mb-4 flex-wrap select-none">
                      <div className="bg-[#1A1A1A]/40 backdrop-blur-xl border border-white/10 px-3 py-1 rounded-full flex items-center gap-1.5 shadow-md">
                        <span className="material-symbols-outlined text-[13px] text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>
                          wb_sunny
                        </span>
                        <span className="font-label-sm text-[9px] text-on-surface uppercase tracking-wider font-semibold">
                          {currentOutfit.weather}
                        </span>
                      </div>
                      <div className="bg-[#1A1A1A]/40 backdrop-blur-xl border border-white/10 px-3 py-1 rounded-full flex items-center gap-1.5 shadow-md">
                        <span className="material-symbols-outlined text-[13px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
                          event
                        </span>
                        <span className="font-label-sm text-[9px] text-on-surface uppercase tracking-wider font-semibold">
                          {currentOutfit.occasion}
                        </span>
                      </div>
                    </div>

                    <span className="font-label-sm text-[9px] text-tertiary/80 uppercase tracking-[0.2em] block font-bold mb-1 select-none">
                      {currentOutfit.subtitle}
                    </span>
                    <h2 className="font-display text-2xl text-white mb-2 italic">
                      {currentOutfit.name}
                    </h2>
                    <p className="font-body-md text-xs text-on-surface-variant/75 line-clamp-2 mb-6 font-light leading-relaxed">
                      {currentOutfit.description}
                    </p>

                    <div className="flex gap-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/app/outfit/${currentOutfit.id}`);
                        }}
                        className="flex-1 bg-white text-background font-label-sm text-[10px] uppercase py-4 rounded-lg tracking-widest hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-lg active:scale-[0.98] cursor-pointer"
                      >
                        View Details
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSwipe("keep");
                        }}
                        className="w-14 h-14 bg-white/5 backdrop-blur-md border border-white/10 rounded-lg flex items-center justify-center text-primary hover:bg-primary hover:text-surface group transition-all duration-300 active:scale-95 cursor-pointer shadow-lg"
                        title="Keep Curation"
                      >
                        <span className="material-symbols-outlined text-lg group-hover:scale-110 transition-transform">
                          favorite
                        </span>
                      </button>
                    </div>
                  </div>
                </div>

                {outfits[currentIndex + 1] && (
                  <div className="absolute inset-0 bg-surface-container-high rounded-2xl -z-10 translate-y-4 scale-[0.96] opacity-50 border border-white/5 transition-transform"></div>
                )}
                {outfits[currentIndex + 2] && (
                  <div className="absolute inset-0 bg-surface-container-low rounded-2xl -z-20 translate-y-8 scale-[0.92] opacity-30 border border-white/5 transition-transform"></div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-16 px-8 max-w-sm glass rounded-2xl shadow-2xl border border-white/5 animate-fade-in z-20">
              <span className="material-symbols-outlined text-5xl text-tertiary mb-4 animate-bounce">
                auto_awesome
              </span>
              <h3 className="font-display text-2xl text-on-surface mb-2 italic luxury-text-gradient">
                Curation Deck Refreshed
              </h3>
              <p className="font-body-md text-xs text-on-surface-variant/70 leading-relaxed mb-8">
                Your personal style analyzer has synced your capsule library. Click refresh to review and evaluate curations again.
              </p>
              <button
                onClick={() => setCurrentIndex(0)}
                className="px-8 py-3.5 bg-on-surface text-background rounded-lg font-label-sm text-[10px] uppercase tracking-widest font-bold hover:bg-tertiary hover:text-on-tertiary transition-all cursor-pointer shadow-lg active:scale-95"
              >
                Refresh Deck
              </button>
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
};

export default Suggestions;
