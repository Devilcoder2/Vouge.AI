import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import {
  apiGenerateOutfits,
  apiSaveOutfit,
  apiDeleteSavedOutfit,
  apiSubmitFeedback
} from "../utils/outfitStore";
import { ModelTryOn } from "../components/ui/ModelTryOn";

const OCCASIONS = [
  { value: "casual", label: "Casual" },
  { value: "work", label: "Office" },
  { value: "evening", label: "Cocktail" },
  { value: "gym", label: "Athletic" },
  { value: "wedding", label: "Formal" }
];

const SEASONS = [
  { value: "spring", label: "Spring" },
  { value: "summer", label: "Summer" },
  { value: "autumn", label: "Autumn" },
  { value: "winter", label: "Winter" }
];

export const Suggestions = () => {
  const navigate = useNavigate();

  // Filter States
  const [selectedOccasion, setSelectedOccasion] = useState("casual");
  const [selectedSeason, setSelectedSeason] = useState("autumn");

  // Outfits List Async State
  const [outfits, setOutfits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false); // Distinguishes expensive AI sweeps

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

  // Fetch Recommended Outfits based on Selected Occasion/Season
  const fetchOutfits = async (forceRegenerate = false) => {
    // API Call Lock: Prevent duplicate overlapping calls
    if (forceRegenerate) {
      if (regenerating) return;
      setRegenerating(true);
    } else {
      if (loading && outfits.length > 0) return; // Already loading
      setLoading(true);
    }
    
    setCurrentIndex(0);
    try {
      const data = await apiGenerateOutfits({
        user_id: "default_user",
        occasion: selectedOccasion,
        season: selectedSeason,
        force_regenerate: forceRegenerate
      });
      setOutfits(data || []);
    } catch (err) {
      console.error("Failed fetching curation manifest:", err);
    } finally {
      setLoading(false);
      setRegenerating(false);
    }
  };

  // Changing dropdowns triggers instant local cache lookup (force_regenerate: false)
  useEffect(() => {
    fetchOutfits(false);
  }, [selectedOccasion, selectedSeason]);

  const currentOutfit = outfits[currentIndex] || null;

  // Swipe Action Handlers (Mobile)
  const handleSwipe = async (direction) => {
    const outfit = outfits[currentIndex];
    if (!outfit) return;

    setSwipeDirection(direction);
    
    if (direction === "keep") {
      setToastMsg(`Added "${outfit.name}" to Saved Wardrobe`);
      try {
        await apiSaveOutfit({
          user_id: "default_user",
          name: outfit.name,
          occasion: selectedOccasion,
          season: selectedSeason,
          score: outfit.vogueScore,
          reasoning: outfit.reasoning,
          clothing_item_ids: outfit.items.map(it => it.id),
          preview_url: outfit.preview_url || null
        });
        await apiSubmitFeedback({
          user_id: "default_user",
          outfit_item_ids: outfit.items.map(it => it.id),
          feedback_type: "like"
        });
      } catch (err) {
        console.error("Error saving swipe keep outfit:", err);
      }
    } else {
      setToastMsg(`Skipped "${outfit.name}"`);
      try {
        await apiSubmitFeedback({
          user_id: "default_user",
          outfit_item_ids: outfit.items.map(it => it.id),
          feedback_type: "skip"
        });
      } catch (err) {
        console.error("Error logging swipe skip feedback:", err);
      }
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
  const handleDesktopLike = async (outfit) => {
    const isCurrentlyLiked = !!desktopStates[outfit.id]?.liked;
    const newLiked = !isCurrentlyLiked;
    
    setDesktopStates((prev) => ({
      ...prev,
      [outfit.id]: { ...prev[outfit.id], liked: newLiked },
    }));

    setToastMsg(
      newLiked
        ? `Added "${outfit.name}" to Saved Wardrobe`
        : `Removed "${outfit.name}" from Saved Wardrobe`
    );
    setTimeout(() => setToastMsg(""), 1500);

    try {
      if (newLiked) {
        const saved = await apiSaveOutfit({
          user_id: "default_user",
          name: outfit.name,
          occasion: selectedOccasion,
          season: selectedSeason,
          score: outfit.vogueScore,
          reasoning: outfit.reasoning,
          clothing_item_ids: outfit.items.map(it => it.id),
          preview_url: outfit.preview_url || null
        });
        
        setDesktopStates((prev) => ({
          ...prev,
          [outfit.id]: { ...prev[outfit.id], dbId: saved.id },
        }));
      } else {
        const dbId = desktopStates[outfit.id]?.dbId;
        if (dbId) {
          await apiDeleteSavedOutfit(dbId);
        }
      }

      await apiSubmitFeedback({
        user_id: "default_user",
        outfit_item_ids: outfit.items.map(it => it.id),
        feedback_type: newLiked ? "like" : "dismiss"
      });
    } catch (err) {
      console.error("Failed desktop save transaction:", err);
    }
  };

  const handleDesktopSkip = async (outfit) => {
    const isCurrentlySkipped = !!desktopStates[outfit.id]?.skipped;
    const newSkipped = !isCurrentlySkipped;
    
    setDesktopStates((prev) => ({
      ...prev,
      [outfit.id]: { ...prev[outfit.id], skipped: newSkipped },
    }));
    
    setToastMsg(newSkipped ? `Skipped "${outfit.name}"` : `Restored "${outfit.name}"`);
    setTimeout(() => setToastMsg(""), 1500);

    try {
      await apiSubmitFeedback({
        user_id: "default_user",
        outfit_item_ids: outfit.items.map(it => it.id),
        feedback_type: newSkipped ? "skip" : "like"
      });
    } catch (err) {
      console.error("Failed feedback logging:", err);
    }
  };

  return (
    <Layout title="Recommended Outfits">
      <div className="relative w-full min-h-[calc(100vh-140px)] flex flex-col items-center justify-start -mt-4 pb-20">
        
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

        {/* ==================== PREMIUM FILTERS BAR ==================== */}
        <div className="w-full max-w-container-max mx-auto px-4 pt-6 pb-2 z-10 flex flex-col md:flex-row gap-4 items-center justify-between border-b border-white/5 select-none animate-fade-in">
          <div className="text-center md:text-left">
            <h2 className="font-display text-2xl luxury-text-gradient italic font-bold">Augmented Curations</h2>
            <p className="font-body-md text-[9px] text-on-surface-variant/40 tracking-wider uppercase font-semibold">
              Select Parameters to Feed Curation Engines
            </p>
          </div>

          <div className="flex flex-wrap justify-center items-center gap-3">
            {/* Occasions Dropdown */}
            <div className="relative glass rounded-lg border border-white/10 px-3 py-2 flex items-center gap-2 text-xs">
              <span className="material-symbols-outlined text-[14px] text-tertiary">theater_comedy</span>
              <select
                value={selectedOccasion}
                disabled={loading || regenerating}
                onChange={(e) => setSelectedOccasion(e.target.value)}
                className="bg-transparent border-none text-on-surface focus:ring-0 focus:outline-none font-bold uppercase tracking-wider text-[10px] cursor-pointer disabled:opacity-50"
              >
                {OCCASIONS.map(occ => (
                  <option key={occ.value} value={occ.value} className="bg-surface text-on-surface">{occ.label}</option>
                ))}
              </select>
            </div>

            {/* Seasons Dropdown */}
            <div className="relative glass rounded-lg border border-white/10 px-3 py-2 flex items-center gap-2 text-xs">
              <span className="material-symbols-outlined text-[14px] text-primary">filter_drama</span>
              <select
                value={selectedSeason}
                disabled={loading || regenerating}
                onChange={(e) => setSelectedSeason(e.target.value)}
                className="bg-transparent border-none text-on-surface focus:ring-0 focus:outline-none font-bold uppercase tracking-wider text-[10px] cursor-pointer disabled:opacity-50"
              >
                {SEASONS.map(sea => (
                  <option key={sea.value} value={sea.value} className="bg-surface text-on-surface">{sea.label}</option>
                ))}
              </select>
            </div>

            {/* Premium Regenerate with AI Button */}
            <button
              onClick={() => fetchOutfits(true)}
              disabled={loading || regenerating}
              className={`relative rounded-lg px-4 py-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider transition-all select-none border shadow-md active:scale-95 cursor-pointer ${
                regenerating 
                  ? "bg-tertiary/10 border-tertiary/40 text-tertiary" 
                  : "bg-white/[0.02] border-tertiary/20 hover:border-tertiary/50 text-tertiary hover:bg-tertiary/5"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
              title="Run high-fidelity Gemini AI curation over current database"
            >
              <span className={`material-symbols-outlined text-[15px] ${regenerating ? "animate-spin" : ""}`}>
                {regenerating ? "progress_activity" : "auto_awesome"}
              </span>
              <span>{regenerating ? "Re-Curating..." : "Regenerate with AI"}</span>
            </button>
          </div>
        </div>

        {/* ==================== EXPENSIVE AI REGENERATION SCREEN OVERLAY ==================== */}
        {regenerating ? (
          <div className="flex-grow w-full max-w-md mx-auto flex flex-col items-center justify-center p-12 text-center z-10 select-none animate-fade-in">
            <div className="relative w-32 h-32 mb-8 flex items-center justify-center">
              {/* Outer pulse borders */}
              <div className="absolute inset-0 rounded-full border border-tertiary/20 animate-ping opacity-60"></div>
              <div className="absolute inset-2 rounded-full border-2 border-primary/10 animate-pulse"></div>
              <div className="w-20 h-20 rounded-full bg-white/[0.01] border border-white/5 shadow-2xl flex items-center justify-center relative overflow-hidden group">
                <span className="material-symbols-outlined text-4xl text-tertiary animate-spin" style={{ animationDuration: "3s" }}>
                  sync
                </span>
              </div>
            </div>
            
            <h3 className="font-display text-2xl text-white italic luxury-text-gradient mb-3">
              Running Curation Models
            </h3>
            <p className="font-body-md text-xs text-on-surface-variant/40 tracking-[0.2em] uppercase font-bold mb-6">
              Vogue.AI High-fidelity Deep Analysis
            </p>
            
            <div className="glass p-5 rounded-xl border border-white/5 space-y-2 max-w-sm">
              <p className="font-mono text-[9px] text-tertiary/80 uppercase tracking-widest text-left">
                &gt; Querying embedding similarity caches...
              </p>
              <p className="font-mono text-[9px] text-primary/70 uppercase tracking-widest text-left">
                &gt; Aligning silhouette balance proportions...
              </p>
              <p className="font-mono text-[9px] text-on-surface-variant/60 uppercase tracking-widest text-left">
                &gt; Calling Gemini stylist explainers...
              </p>
            </div>
          </div>
        ) : loading ? (
          /* ==================== STANDARD SKELETON LOADER ==================== */
          <div className="w-full max-w-container-max mx-auto px-4 py-12 z-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 select-none">
            {[1, 2, 3].map(n => (
              <div key={n} className="rounded-2xl overflow-hidden glass border border-white/5 flex flex-col h-[520px] shadow-xl animate-pulse">
                <div className="h-[260px] bg-white/[0.03] border-b border-white/5"></div>
                <div className="p-6 flex flex-col justify-between flex-1 space-y-4">
                  <div className="space-y-3">
                    <div className="h-2 w-16 bg-white/[0.04] rounded-full"></div>
                    <div className="h-4 w-40 bg-white/[0.05] rounded-full"></div>
                    <div className="h-2 w-full bg-white/[0.03] rounded-full"></div>
                    <div className="h-2 w-5/6 bg-white/[0.03] rounded-full"></div>
                  </div>
                  <div className="h-10 w-full bg-white/[0.05] rounded-lg"></div>
                </div>
              </div>
            ))}
          </div>
        ) : outfits.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center max-w-md mx-auto z-10 select-none">
            <span className="material-symbols-outlined text-6xl text-on-surface-variant/20 mb-4 animate-pulse">
              folder_open
            </span>
            <h3 className="font-display text-2xl text-on-surface italic luxury-text-gradient mb-2">
              No Matches Found
            </h3>
            <p className="font-body-md text-xs text-on-surface-variant/60 leading-relaxed mb-6">
              Vogue.AI requires diverse wardrobe items to generate recommended outfits. Add items to your closet category grids to run candidates.
            </p>
            <button
              onClick={() => navigate("/app/wardrobe")}
              className="px-6 py-3 bg-white text-background rounded-lg font-label-sm text-[10px] uppercase tracking-widest font-bold hover:bg-tertiary hover:text-on-tertiary transition-all cursor-pointer shadow-lg active:scale-95"
            >
              Go Digitise Wardrobe
            </button>
          </div>
        ) : (
          <>
            {/* ==================== DESKTOP LAYOUT (Grid list of all outfits) ==================== */}
            <div className="hidden md:block w-full max-w-container-max mx-auto px-4 py-8 pb-12 z-10 animate-fade-in">
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
                              handleDesktopSkip(outfit);
                            }}
                            className="px-6 py-2.5 bg-white text-background font-label-sm text-[9px] uppercase tracking-widest rounded hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-lg cursor-pointer"
                          >
                            Restore Outfit
                          </button>
                        </div>
                      )}

                      {/* Card Spotlight Image (Top 50%) */}
                      <div className="relative h-[260px] overflow-hidden shrink-0 border-b border-white/5 flex items-center justify-center bg-[#0d0e12]">
                        <ModelTryOn
                          items={outfit.items}
                          showLabels={false}
                          className="!aspect-square !h-[260px] !rounded-none !border-none max-w-full"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent z-10 pointer-events-none"></div>
                        
                        {/* Vogue Score Badge */}
                        <div className="absolute top-4 right-4 z-20 bg-background/85 backdrop-blur-xl border border-white/10 px-3 py-1.5 rounded-xl flex flex-col items-center shadow-lg">
                          <span className="font-display text-xs text-on-surface-variant font-medium select-none uppercase tracking-wider text-[8px]">VOGUE</span>
                          <span className="font-display text-lg text-tertiary font-bold leading-none">{outfit.vogueScore}</span>
                        </div>

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
                            onClick={() => navigate(`/app/outfit/${outfit.id}`, { state: { outfit } })}
                            className="flex-1 bg-white text-background font-label-sm text-[10px] uppercase py-3.5 rounded-lg tracking-widest hover:bg-tertiary hover:text-on-tertiary transition-all duration-300 font-bold shadow-md cursor-pointer"
                          >
                            View Details
                          </button>

                          {/* Like Action */}
                          <button
                            onClick={() => handleDesktopLike(outfit)}
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
                            onClick={() => handleDesktopSkip(outfit)}
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
            <div className="md:hidden w-full flex-1 flex flex-col items-center justify-center z-10 overflow-hidden pt-8">
              {currentOutfit ? (
                <div className="w-full flex items-center justify-center relative select-none animate-fade-in">
                  
                  {/* Swipe Indicators */}
                  <div 
                    className={`absolute left-4 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 indicator-pulse transition-opacity duration-300 ${
                      dragOffset.x < -40 ? "opacity-100 scale-105" : "opacity-35"
                    }`}
                  >
                    <span className="material-symbols-outlined text-primary text-3xl font-light">chevron_left</span>
                    <span className="text-[9px] uppercase tracking-[0.2em] transform -rotate-90 origin-center translate-y-6 font-semibold text-primary">
                      Discard
                    </span>
                  </div>

                  <div 
                    className={`absolute right-4 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 indicator-pulse transition-opacity duration-300 ${
                      dragOffset.x > 40 ? "opacity-100 scale-105" : "opacity-35"
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
                      
                      <ModelTryOn
                        items={currentOutfit.items}
                        showLabels={false}
                        className="!aspect-square sm:!aspect-[4/5.6] !rounded-none !border-none max-w-full pointer-events-none select-none"
                      />

                      {/* Vogue Score Badge */}
                      <div className="absolute top-4 right-4 z-20 bg-background/85 backdrop-blur-xl border border-white/10 px-3 py-1.5 rounded-xl flex flex-col items-center shadow-lg select-none">
                        <span className="font-display text-xs text-on-surface-variant font-medium uppercase tracking-wider text-[8px]">VOGUE</span>
                        <span className="font-display text-lg text-tertiary font-bold leading-none">{currentOutfit.vogueScore}</span>
                      </div>

                      <div className="absolute bottom-0 left-0 w-full p-6 z-20 flex flex-col justify-end">
                        <div className="flex items-center gap-2 mb-4 flex-wrap select-none">
                          <div className="bg-[#1A1A1A]/40 backdrop-blur-xl border border-white/10 px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-md">
                            <span className="material-symbols-outlined text-[13px] text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>
                              wb_sunny
                            </span>
                            <span className="font-label-sm text-[9px] text-on-surface uppercase tracking-wider font-semibold">
                              {currentOutfit.weather}
                            </span>
                          </div>
                          <div className="bg-[#1A1A1A]/40 backdrop-blur-xl border border-white/10 px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-md">
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
                              navigate(`/app/outfit/${currentOutfit.id}`, { state: { outfit: currentOutfit } });
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
                <div className="text-center py-16 px-8 max-w-sm glass rounded-2xl shadow-2xl border border-white/5 animate-fade-in z-20 select-none">
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
          </>
        )}

      </div>
    </Layout>
  );
};

export default Suggestions;
