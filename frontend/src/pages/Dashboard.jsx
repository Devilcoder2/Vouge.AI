import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { 
  apiGetEditorialLook, 
  apiGetTrends, 
  apiGetStyleProfile 
} from "../utils/dashboardStore";
import { apiGetWardrobeStats } from "../utils/wardrobeStore";

export const Dashboard = () => {
  const navigate = useNavigate();

  // Async States
  const [stats, setStats] = useState({ syncPercentage: 84, totalPieces: 1248 });
  const [editorialLook, setEditorialLook] = useState(null);
  const [trends, setTrends] = useState([]);
  const [styleProfile, setStyleProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // Activate scroll-reveal animations on dashboard mount
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("active");
        }
      });
    }, observerOptions);

    const revealElements = document.querySelectorAll(".reveal");
    revealElements.forEach((el) => observer.observe(el));

    return () => {
      revealElements.forEach((el) => observer.unobserve(el));
    };
  }, [loading]);

  // Load live Dashboard metrics on mount
  useEffect(() => {
    const loadDashboardData = async () => {
      setLoading(true);
      try {
        // 1. Fetch Wardrobe Sync Stats
        const statsData = await apiGetWardrobeStats();
        if (statsData) {
          setStats(statsData);
        }

        // 2. Fetch User Style Profile
        const profileData = await apiGetStyleProfile();
        if (profileData) {
          setStyleProfile(profileData);
        }

        // 3. Fetch runway trends matching style persona
        const persona = profileData?.preferred_styles?.[0] || "minimalist";
        const trendsData = await apiGetTrends(persona, 3);
        if (trendsData) {
          setTrends(trendsData);
        }

        // 4. Fetch Today's Curation Spotlight Look
        const lookData = await apiGetEditorialLook();
        if (lookData) {
          setEditorialLook(lookData);
        }
      } catch (err) {
        console.error("Failed loading fashion intelligence indices:", err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Format Total items count into clean K-notation (e.g. 1248 -> 1.2K)
  const formatCount = (count) => {
    if (!count) return "0";
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  const currentTrend = trends[0] || {
    trend_id: "monochromatic-discipline",
    title: "The Monochromatic Discipline",
    source: "Paris Fashion Week",
    category: "Trending",
    image_url: "/assets/monochrome_trend.png",
    description: "Elevating basics through strict color discipline. A global shift towards high-contrast minimalism is emerging."
  };

  return (
    <Layout>
      <div className="space-y-12 pb-16">
        
        {/* ==================== HERO SECTION LOADING SKELETON / PLOT ==================== */}
        {loading || !editorialLook ? (
          <section className="relative w-full aspect-[4/5] md:aspect-[21/9] rounded-2xl overflow-hidden glass border border-white/5 animate-pulse flex flex-col justify-end p-6 md:p-12 lg:p-16">
            <div className="max-w-2xl space-y-6">
              <div className="h-6 w-48 bg-white/[0.04] rounded-full"></div>
              <div className="h-10 w-80 bg-white/[0.05] rounded-full"></div>
              <div className="h-4 w-full bg-white/[0.03] rounded-full"></div>
              <div className="h-12 w-40 bg-white/[0.05] rounded-full"></div>
            </div>
          </section>
        ) : (
          /* Hero Curated Spotlight Look */
          <section 
            className="relative w-full aspect-[4/5] md:aspect-[21/9] rounded-2xl overflow-hidden group shadow-2xl hero-reveal select-none"
            style={{ animationDelay: "0.1s" }}
          >
            <img
              alt={editorialLook.name}
              className="absolute inset-0 w-full h-full object-cover group-hover:scale-103 transition-transform duration-[2000ms] ease-out"
              style={{ objectPosition: "center 15%" }}
              src={editorialLook.heroImage}
            />
            <div className="absolute inset-0 hero-gradient"></div>
            <div className="absolute inset-0 p-6 md:p-12 lg:p-16 flex flex-col justify-end">
              <div className="max-w-2xl">
                <div 
                  className="flex items-center gap-3 mb-6 hero-reveal"
                  style={{ animationDelay: "0.2s" }}
                >
                  <div className="px-3 py-1 glass-panel rounded-full flex items-center gap-2">
                    <span className="material-symbols-outlined text-tertiary text-sm">filter_drama</span>
                    <span className="font-label-sm text-[10px] text-tertiary uppercase tracking-[0.2em]">
                      London • 12°C • Overcast
                    </span>
                  </div>
                </div>
                
                <span className="font-label-sm text-[10px] text-tertiary uppercase tracking-[0.25em] mb-1.5 block font-bold hero-reveal" style={{ animationDelay: "0.25s" }}>
                  {editorialLook.subtitle}
                </span>

                <h2 
                  className="font-display text-4xl md:text-5xl lg:text-6xl mb-6 leading-tight italic text-on-surface hero-reveal"
                  style={{ animationDelay: "0.3s" }}
                >
                  {editorialLook.name}
                </h2>
                
                <p 
                  className="font-body text-[14px] md:text-[16px] text-on-surface/85 mb-8 max-w-md font-light leading-relaxed hero-reveal"
                  style={{ animationDelay: "0.4s" }}
                >
                  {editorialLook.description}
                </p>
                
                <div 
                  className="flex gap-4 hero-reveal"
                  style={{ animationDelay: "0.5s" }}
                >
                  <button
                    onClick={() => navigate(`/app/outfit/${editorialLook.id}`, { state: { outfit: editorialLook } })}
                    className="bg-on-surface text-surface font-label-sm text-xs px-6 md:px-8 py-3.5 md:py-4 rounded-full uppercase tracking-[0.2em] hover:bg-tertiary hover:text-on-tertiary transition-all duration-500 shadow-lg cursor-pointer font-bold active:scale-95"
                  >
                    View Ensemble
                  </button>
                  <button
                    onClick={() => navigate("/app/chat")}
                    className="glass-panel text-on-surface font-label-sm text-xs px-6 md:px-8 py-3.5 md:py-4 rounded-full uppercase tracking-[0.2em] hover:bg-white/10 transition-all duration-500 cursor-pointer font-bold active:scale-95 border border-white/5"
                  >
                    Ask Assistant
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ==================== STATS & FAST OPTIONS BAR ==================== */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch reveal">
          
          {/* Sync Stats Gauges */}
          <div className="lg:col-span-4 grid grid-cols-2 gap-4 select-none">
            <Link
              to="/app/wardrobe"
              className="glass-panel p-8 rounded-2xl flex flex-col items-start justify-between ai-glow group hover:border-tertiary/30 transition-all duration-300 hover:scale-[1.02] border border-white/5"
            >
              <span className="material-symbols-outlined text-tertiary/40 mb-6 group-hover:text-tertiary transition-colors text-2xl">
                cloud_done
              </span>
              <div>
                <span className="font-display text-3xl mb-1 font-semibold block">
                  {stats.syncPercentage ? stats.syncPercentage.toFixed(1) : "0.0"}<span className="text-tertiary text-lg">%</span>
                </span>
                <p className="font-label-sm text-[10px] text-on-surface-variant uppercase tracking-[0.15em] font-semibold">
                  Wardrobe Sync
                </p>
              </div>
            </Link>

            <Link
              to="/app/wardrobe"
              className="glass-panel p-8 rounded-2xl flex flex-col items-start justify-between ai-glow group hover:border-tertiary/30 transition-all duration-300 hover:scale-[1.02] border border-white/5"
            >
              <span className="material-symbols-outlined text-tertiary/40 mb-6 group-hover:text-tertiary transition-colors text-2xl">
                checkroom
              </span>
              <div>
                <span className="font-display text-3xl mb-1 font-semibold block">
                  {formatCount(stats.totalPieces)}
                </span>
                <p className="font-label-sm text-[10px] text-on-surface-variant uppercase tracking-[0.15em] font-semibold">
                  Total Items
                </p>
              </div>
            </Link>
          </div>

          {/* Premium Style Engine Fast Actions */}
          <div className="lg:col-span-8 glass-panel p-8 rounded-2xl flex flex-col justify-center shadow-lg border border-white/5 select-none">
            <div className="flex items-center justify-between mb-8">
              <h3 className="font-label-sm text-xs tracking-widest uppercase text-on-surface font-bold">
                Style Engine
              </h3>
              <div className="h-px flex-1 bg-outline-variant/10 mx-6"></div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 md:gap-6">
              <Link
                to="/app/chat"
                className="flex flex-col items-center gap-4 p-4 rounded-xl hover:bg-white/5 transition-all group text-center"
              >
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center bg-surface-container group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-500 shadow-inner border border-white/5">
                  <span className="material-symbols-outlined text-2xl">auto_awesome</span>
                </div>
                <span className="font-label-sm text-[9px] md:text-[10px] uppercase tracking-widest text-on-surface-variant group-hover:text-on-surface transition-colors font-semibold">
                  Ask Stylist
                </span>
              </Link>

              <Link
                to="/app/camera"
                className="flex flex-col items-center gap-4 p-4 rounded-xl hover:bg-white/5 transition-all group text-center"
              >
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center bg-surface-container group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-500 shadow-inner border border-white/5">
                  <span className="material-symbols-outlined text-2xl">add_a_photo</span>
                </div>
                <span className="font-label-sm text-[9px] md:text-[10px] uppercase tracking-widest text-on-surface-variant group-hover:text-on-surface transition-colors font-semibold">
                  Upload Item
                </span>
              </Link>

              <Link
                to="/app/analysis"
                className="flex flex-col items-center gap-4 p-4 rounded-xl hover:bg-white/5 transition-all group text-center"
              >
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center bg-surface-container group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-500 shadow-inner border border-white/5">
                  <span className="material-symbols-outlined text-2xl">troubleshoot</span>
                </div>
                <span className="font-label-sm text-[9px] md:text-[10px] uppercase tracking-widest text-on-surface-variant group-hover:text-on-surface transition-colors font-semibold">
                  Gap Analysis
                </span>
              </Link>
            </div>
          </div>
        </section>

        {/* ==================== ALGORITHMIC STYLE INTELLIGENCE FEED ==================== */}
        <section className="reveal">
          <div className="flex items-center gap-4 mb-10 select-none">
            <h3 className="font-display text-3xl italic">Intelligence Feed</h3>
            <div className="flex-1 h-px bg-outline-variant/20"></div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            
            {/* Global Runway Trends */}
            <Link
              to="/app/recommendations"
              className="group relative rounded-2xl overflow-hidden aspect-[4/3] md:aspect-auto md:h-[400px] block shadow-xl border border-white/5 select-none"
            >
              <img
                alt={currentTrend.title}
                className="absolute inset-0 w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-[1500ms] ease-out object-[center_30%]"
                src={currentTrend.image_url}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent opacity-90"></div>
              <div className="absolute inset-0 p-8 md:p-10 flex flex-col justify-between z-10">
                <span className="inline-block px-4 py-1.5 glass-panel text-[9px] uppercase tracking-[0.2em] rounded-full w-max text-on-surface font-bold border border-white/5">
                  {currentTrend.category} • {currentTrend.source}
                </span>
                <div>
                  <h4 className="font-display text-2xl md:text-3xl mb-4 text-on-surface italic leading-tight">
                    {currentTrend.title}
                  </h4>
                  <p className="font-body text-[13px] md:text-[14px] text-on-surface/75 leading-relaxed max-w-sm font-light">
                    {currentTrend.description}
                  </p>
                </div>
              </div>
            </Link>

            {/* Personal Analytics Insight Card (Color Overreliance Index) */}
            <div className="glass-panel p-8 md:p-10 rounded-2xl ai-glow flex flex-col justify-between border border-white/5 border-tertiary/10 min-h-[350px] md:min-h-[400px] shadow-xl">
              <div>
                <div className="flex items-center justify-between mb-8 select-none">
                  <span className="px-4 py-1.5 bg-tertiary/10 text-tertiary text-[9px] uppercase tracking-[0.2em] rounded-full font-bold border border-tertiary/20">
                    Personal Insight
                  </span>
                  <span className="material-symbols-outlined text-tertiary text-2xl">
                    analytics
                  </span>
                </div>
                
                <h4 className="font-display text-2xl md:text-3xl mb-6 italic text-on-surface select-none">
                  {styleProfile?.color_overreliance_index?.color_name 
                    ? `${styleProfile.color_overreliance_index.color_name} Over-Reliance` 
                    : "Color Over-Reliance"}
                </h4>
                
                <p className="font-body text-[15px] md:text-[16px] text-on-surface/85 leading-relaxed font-light mb-8">
                  {styleProfile?.color_overreliance_index?.advice ? (
                    styleProfile.color_overreliance_index.advice
                  ) : (
                    "Analyzing dominant color blocks in your digital closet... Upload more pieces to unlock targeting styling and color metrics."
                  )}
                </p>
                
                {/* Visual Palette blocks represent preferred colors */}
                <div className="flex gap-2 mb-4 select-none">
                  {styleProfile?.preferred_colors?.slice(0, 3).map((col, idx) => (
                    <div 
                      key={idx} 
                      className={`h-1.5 rounded-full transition-all ${
                        idx === 0 ? "w-12 bg-tertiary" : idx === 1 ? "w-8 bg-outline/40" : "w-6 bg-outline/25"
                      }`}
                      title={col}
                    ></div>
                  )) || (
                    <>
                      <div className="w-12 h-1.5 rounded-full bg-tertiary"></div>
                      <div className="w-8 h-1.5 rounded-full bg-outline/30"></div>
                      <div className="w-6 h-1.5 rounded-full bg-outline/20"></div>
                    </>
                  )}
                </div>
              </div>
              
              <Link
                to="/app/social/explore"
                className="group self-start flex items-center gap-3 text-tertiary hover:text-on-surface transition-all duration-300"
              >
                <span className="font-label-sm text-[11px] uppercase tracking-[0.2em] font-bold">
                  Explore Semantic Palettes
                </span>
                <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">
                  arrow_forward
                </span>
              </Link>
            </div>

          </div>
        </section>

      </div>
    </Layout>
  );
};

export default Dashboard;
