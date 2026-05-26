import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import SocialLayout from "../components/layout/SocialLayout";
import {
  apiGetRecreateStats, apiGetRecreateHistory
} from "../utils/socialStore";

export const RecreateFit = () => {
  const { postId } = useParams();
  const navigate = useNavigate();

  // Active recreation stats states
  const [activeStats, setActiveStats] = useState(null);
  const [loadingActive, setLoadingActive] = useState(false);
  const [activeError, setActiveError] = useState("");

  // History timeline states
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Load recreation stats for prefilled post
  const loadPrefilledRecreation = async (targetPostId) => {
    setLoadingActive(true);
    setActiveStats(null);
    setActiveError("");
    try {
      const stats = await apiGetRecreateStats(targetPostId);
      setActiveStats(stats);
      
      // Reload history logs to capture the newly logged recreation event!
      loadHistoryLogs();
    } catch (e) {
      console.error(e);
      setActiveError("Failed to calculate outfit compatibility parameters.");
    } finally {
      setLoadingActive(false);
    }
  };

  // Load history list from FastAPI backend (or local caching fallbacks)
  const loadHistoryLogs = async () => {
    setLoadingHistory(true);
    try {
      const hist = await apiGetRecreateHistory();
      setHistoryList(hist);
    } catch (e) {
      console.error("Error loading recreation history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistoryLogs();
  }, []);

  useEffect(() => {
    if (postId) {
      loadPrefilledRecreation(postId);
      window.scrollTo(0, 0);
    } else {
      setActiveStats(null);
    }
  }, [postId]);

  return (
    <SocialLayout title="Recreate Fit">
      <div className="w-full relative pb-20 select-text max-w-2xl mx-auto">
        
        {/* Title Header */}
        <div className="mb-8 select-none">
          <h2 className="font-display text-2xl italic luxury-text-gradient mb-1">Recreation Engine</h2>
          <p className="text-[7px] uppercase tracking-[0.2em] text-on-surface-variant/40 font-semibold">
            Evaluate garment compatibility & review previously matched fits
          </p>
        </div>

        {/* ==================== ACTIVE RECREATION PANEL ==================== */}
        {postId ? (
          <section className="glass rounded-2xl border border-white/[0.08] p-6 shadow-2xl mb-10 animate-fade-in relative overflow-hidden">
            <div className="absolute top-0 right-0 w-44 h-44 bg-tertiary/10 rounded-full blur-[70px] pointer-events-none select-none"></div>
            
            <div className="flex justify-between items-center mb-6 select-none border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary font-bold animate-pulse">auto_awesome</span>
                <h3 className="font-display text-sm italic text-white">Prefilled Fit Calculations</h3>
              </div>
              
              <button
                onClick={() => navigate("/app/social/recreate")}
                className="text-[8px] uppercase tracking-widest text-on-surface-variant/60 hover:text-white font-bold"
              >
                Clear Active
              </button>
            </div>

            {loadingActive ? (
              <div className="flex flex-col items-center justify-center py-12 text-center select-none">
                <span className="material-symbols-outlined text-3xl text-tertiary animate-spin mb-3">
                  sync
                </span>
                <p className="font-body-md text-xs text-on-surface-variant/60 tracking-wider">
                  Analyzing wardrobe similarity & circular HSL colors...
                </p>
              </div>
            ) : activeError ? (
              <div className="text-center py-6 select-none text-error text-xs">
                {activeError}
              </div>
            ) : activeStats ? (
              <div className="flex flex-col gap-6">
                {/* Gauge Summary row */}
                <div className="p-4 bg-white/[0.02] border border-white/5 rounded-xl flex items-center justify-between gap-6 select-none">
                  <div>
                    <span className="text-[7px] text-on-surface-variant/50 uppercase tracking-[0.2em] block font-bold mb-1">
                      Compatibility Index
                    </span>
                    <h4 className="font-display text-xl text-white italic">
                      {activeStats.overall_match_percentage}% Match
                    </h4>
                    <p className="font-body-md text-[9px] text-on-surface-variant/75 mt-1 leading-relaxed max-w-[280px]">
                      {activeStats.overall_match_percentage >= 80 
                        ? "Excellent closet readiness! You have the perfect items to recreate this styled look."
                        : activeStats.overall_match_percentage >= 50
                        ? "Great options available. Minor substitutions will fit the aesthetic beautifully."
                        : "A few wardrobe gaps detected. Check out the recommended shoppable substitutes."}
                    </p>
                  </div>

                  <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle cx="32" cy="32" r="26" stroke="rgba(255,255,255,0.05)" strokeWidth="5" fill="transparent"/>
                      <circle 
                        cx="32" 
                        cy="32" 
                        r="26" 
                        stroke="#adc6ff" 
                        strokeWidth="5" 
                        fill="transparent"
                        strokeDasharray={2 * Math.PI * 26}
                        strokeDashoffset={2 * Math.PI * 26 * (1 - activeStats.overall_match_percentage / 100)}
                        style={{ transition: "stroke-dashoffset 1s ease" }}
                      />
                    </svg>
                    <span className="absolute font-display text-[10px] italic text-white font-bold">
                      {Math.round(activeStats.overall_match_percentage)}%
                    </span>
                  </div>
                </div>

                {/* Slots Match Breakdown */}
                <div className="flex flex-col gap-3">
                  <h4 className="font-display text-xs italic text-white select-none">Garment Slots Breakdown</h4>
                  <div className="flex flex-col gap-2.5">
                    {activeStats.slots && activeStats.slots.map(slot => (
                      <div 
                        key={slot.tagged_item_id}
                        className="p-3 bg-white/5 border border-white/5 rounded-xl flex items-center justify-between gap-4 shadow-sm"
                      >
                        <div className="flex-1 min-w-0">
                          <span className="font-label-sm text-[7px] text-on-surface-variant/40 uppercase tracking-widest font-bold block mb-1">
                            {slot.role} slot
                          </span>
                          <h5 className="font-display text-xs text-white italic truncate">
                            {slot.tagged_item_name}
                          </h5>

                          {slot.match_status !== "Missing" && slot.matched_item ? (
                            <div className="flex items-center gap-1.5 mt-2 text-on-surface-variant/80 select-none">
                              <span className="material-symbols-outlined text-[11px] text-tertiary">check_circle</span>
                              <span className="font-body-md text-[8px] truncate">
                                Owned: {slot.matched_item.name} ({Math.round(slot.similarity_score * 100)}% Sim)
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5 mt-2 text-error select-none">
                              <span className="material-symbols-outlined text-[11px]">info</span>
                              <span className="font-body-md text-[8px] font-semibold">
                                Garment gap detected
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col items-end shrink-0 gap-1.5 select-none">
                          <span className={`px-2 py-0.5 rounded-full font-label-sm text-[6px] uppercase tracking-wider font-semibold ${
                            slot.match_status === "Perfect Match" 
                              ? "bg-tertiary/20 text-tertiary border border-tertiary/30" 
                              : slot.match_status === "Substitute"
                              ? "bg-primary/20 text-primary border border-primary/30"
                              : "bg-error/15 text-error border border-error/25"
                          }`}>
                            {slot.match_status}
                          </span>

                          {slot.buy_link && (
                            <a
                              href={slot.buy_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 px-2.5 py-1 bg-white text-background font-label-sm text-[7px] uppercase tracking-widest rounded font-bold hover:bg-tertiary hover:text-on-tertiary transition-all shadow-md"
                            >
                              Shop
                              <span className="material-symbols-outlined text-[8px]">shopping_cart</span>
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            ) : (
              <p className="text-center text-xs opacity-50 py-10 select-none">Prefilled details failed to resolve.</p>
            )}
          </section>
        ) : (
          <div className="text-center py-10 px-6 glass rounded-2xl border border-white/5 select-none mb-10">
            <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-2">
              auto_awesome
            </span>
            <h4 className="font-display text-sm italic text-on-surface mb-0.5">No Active Fit Prefilled</h4>
            <p className="font-body-md text-[10px] text-on-surface-variant/50 max-w-sm mx-auto leading-relaxed">
              Tapping "Recreate Fit" on any feed post will automatically evaluate its compatibility parameters and log it here!
            </p>
          </div>
        )}

        {/* ==================== RECREATION HISTORY TIMELINE ==================== */}
        <section className="animate-fade-in select-none">
          <h3 className="font-display text-base italic text-white mb-5 select-none">Recreation Log History</h3>

          {loadingHistory ? (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-2xl text-tertiary animate-spin mb-2">
                sync
              </span>
              <p className="font-body-md text-[9px] text-on-surface-variant/40 uppercase tracking-widest">
                Retrieving history timelines...
              </p>
            </div>
          ) : historyList.length === 0 ? (
            <div className="text-center py-12 px-6 glass rounded-2xl border border-white/5">
              <span className="material-symbols-outlined text-3xl text-on-surface-variant/30 mb-2">
                history
              </span>
              <h4 className="font-display text-sm italic text-on-surface mb-0.5">No History Found</h4>
              <p className="font-body-md text-[10px] text-on-surface-variant/50 max-w-xs mx-auto leading-relaxed">
                Log recreation events to populate this styling history board!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {historyList.map(item => (
                <div
                  key={item.id}
                  onClick={() => navigate(`/app/social/recreate/${item.post_id}`)}
                  className="glass rounded-xl border border-white/5 overflow-hidden flex cursor-pointer hover:border-white/15 hover:scale-[1.01] transition-all duration-300 shadow-md"
                >
                  {/* Small post thumbnail image */}
                  {item.post_image_url && (
                    <div className="w-20 md:w-24 shrink-0 bg-black/20 relative">
                      <img src={item.post_image_url} alt="Post" className="w-full h-full object-cover" />
                      
                      <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-black/60 backdrop-blur-md rounded text-[6px] font-label-sm font-bold text-tertiary uppercase border border-white/5">
                        {item.overall_match_percentage}%
                      </div>
                    </div>
                  )}

                  {/* Recreation log details */}
                  <div className="p-3 flex-1 min-w-0 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-display italic text-[10px] text-white truncate">
                          @{item.post_username}
                        </span>
                        <span className="text-[7px] text-on-surface-variant/30 font-semibold font-mono shrink-0 ml-2">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      
                      <p className="font-body-md text-[9px] text-on-surface-variant/75 leading-relaxed truncate font-light">
                        {item.post_caption || "Curated outfit look checking."}
                      </p>
                    </div>

                    <div className="flex justify-between items-center mt-3 pt-2 border-t border-white/5">
                      <span className="font-label-sm text-[6.5px] uppercase tracking-widest text-tertiary font-bold">
                        Calculated stats
                      </span>
                      <span className="material-symbols-outlined text-xs text-on-surface-variant/40 hover:text-white">
                        arrow_forward
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </SocialLayout>
  );
};

export default RecreateFit;
