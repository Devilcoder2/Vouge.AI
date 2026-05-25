import React, { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const Dashboard = () => {
  const navigate = useNavigate();

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
  }, []);

  return (
    <Layout>
      <div className="space-y-12">
        {/* Hero: Today's Curated Look (High-Fashion Editorial) */}
        <section 
          className="relative w-full aspect-[4/5] md:aspect-[21/9] rounded-2xl overflow-hidden group shadow-2xl hero-reveal"
          style={{ animationDelay: "0.1s" }}
        >
          <img
            alt="Today's Look Recommendation"
            className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-[2000ms] ease-out"
            style={{ objectPosition: "center 15%" }}
            src="/assets/modern_noir_hero.png"
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
              
              <h2 
                className="font-display text-4xl md:text-5xl lg:text-6xl mb-6 leading-tight italic text-on-surface hero-reveal"
                style={{ animationDelay: "0.3s" }}
              >
                The Editorial Edit:<br />Modern Noir
              </h2>
              
              <p 
                className="font-body text-[14px] md:text-[16px] text-on-surface/85 mb-8 max-w-md font-light leading-relaxed hero-reveal"
                style={{ animationDelay: "0.4s" }}
              >
                A cinematic approach to your Monday. Your charcoal wool trench meets a crisp ivory knit for an aesthetic that commands the room.
              </p>
              
              <div 
                className="flex gap-4 hero-reveal"
                style={{ animationDelay: "0.5s" }}
              >
                <button
                  onClick={() => navigate("/app/outfit/modern-minimalist")}
                  className="bg-on-surface text-surface font-label-sm text-xs px-6 md:px-8 py-3.5 md:py-4 rounded-full uppercase tracking-[0.2em] hover:bg-tertiary hover:text-on-tertiary transition-all duration-500 shadow-lg cursor-pointer font-bold active:scale-95"
                >
                  View Ensemble
                </button>
                <button
                  onClick={() => navigate("/app/chat")}
                  className="glass-panel text-on-surface font-label-sm text-xs px-6 md:px-8 py-3.5 md:py-4 rounded-full uppercase tracking-[0.2em] hover:bg-white/10 transition-all duration-500 cursor-pointer font-bold active:scale-95"
                >
                  Refine Look
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Stats & Intelligence Action Bar */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch reveal">
          {/* Refined Stats Cards */}
          <div className="lg:col-span-4 grid grid-cols-2 gap-4">
            <Link
              to="/app/wardrobe"
              className="glass-panel p-8 rounded-2xl flex flex-col items-start justify-between ai-glow group hover:border-tertiary/30 transition-all duration-300 hover:scale-[1.02]"
            >
              <span className="material-symbols-outlined text-tertiary/40 mb-6 group-hover:text-tertiary transition-colors text-2xl">
                cloud_done
              </span>
              <div>
                <span className="font-display text-3xl mb-1 font-semibold block">
                  84<span className="text-tertiary text-lg">%</span>
                </span>
                <p className="font-label-sm text-[10px] text-on-surface-variant uppercase tracking-[0.15em] font-semibold">
                  Wardrobe Sync
                </p>
              </div>
            </Link>

            <Link
              to="/app/wardrobe"
              className="glass-panel p-8 rounded-2xl flex flex-col items-start justify-between ai-glow group hover:border-tertiary/30 transition-all duration-300 hover:scale-[1.02]"
            >
              <span className="material-symbols-outlined text-tertiary/40 mb-6 group-hover:text-tertiary transition-colors text-2xl">
                checkroom
              </span>
              <div>
                <span className="font-display text-3xl mb-1 font-semibold block">
                  1.2K
                </span>
                <p className="font-label-sm text-[10px] text-on-surface-variant uppercase tracking-[0.15em] font-semibold">
                  Total Items
                </p>
              </div>
            </Link>
          </div>

          {/* Premium Style Engine Tools */}
          <div className="lg:col-span-8 glass-panel p-8 rounded-2xl flex flex-col justify-center shadow-lg">
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
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center bg-surface-container group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-500 shadow-inner">
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
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center bg-surface-container group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-500 shadow-inner">
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
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center bg-surface-container group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-500 shadow-inner">
                  <span className="material-symbols-outlined text-2xl">troubleshoot</span>
                </div>
                <span className="font-label-sm text-[9px] md:text-[10px] uppercase tracking-widest text-on-surface-variant group-hover:text-on-surface transition-colors font-semibold">
                  Gap Analysis
                </span>
              </Link>
            </div>
          </div>
        </section>

        {/* Algorithmic Insights Feed */}
        <section className="reveal">
          <div className="flex items-center gap-4 mb-10">
            <h3 className="font-display text-3xl italic">Intelligence Feed</h3>
            <div className="flex-1 h-px bg-outline-variant/20"></div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            {/* Global Trends Card */}
            <Link
              to="/app/recommendations"
              className="group relative rounded-2xl overflow-hidden aspect-[4/3] md:aspect-auto md:h-[400px] block shadow-xl"
            >
              <img
                alt="Minimalist Monochrome"
                className="absolute inset-0 w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-[1500ms] ease-out object-[center_30%]"
                src="/assets/monochrome_trend.png"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent opacity-90"></div>
              <div className="absolute inset-0 p-8 md:p-10 flex flex-col justify-between z-10">
                <span className="inline-block px-4 py-1.5 glass-panel text-[9px] uppercase tracking-[0.2em] rounded-full w-max text-on-surface font-bold">
                  Trending • Paris Fashion Week
                </span>
                <div>
                  <h4 className="font-display text-2xl md:text-3xl mb-4 text-on-surface italic">
                    The Monochromatic Discipline
                  </h4>
                  <p className="font-body text-[13px] md:text-[14px] text-on-surface/75 leading-relaxed max-w-sm font-light">
                    Elevating basics through strict color discipline. A global shift towards high-contrast minimalism is emerging.
                  </p>
                </div>
              </div>
            </Link>

            {/* Personal Analytics Card */}
            <div className="glass-panel p-8 md:p-10 rounded-2xl ai-glow flex flex-col justify-between border-tertiary/10 min-h-[350px] md:min-h-[400px] shadow-xl">
              <div>
                <div className="flex items-center justify-between mb-8">
                  <span className="px-4 py-1.5 bg-tertiary/10 text-tertiary text-[9px] uppercase tracking-[0.2em] rounded-full font-bold border border-tertiary/20">
                    Personal Insight
                  </span>
                  <span className="material-symbols-outlined text-tertiary text-2xl">
                    analytics
                  </span>
                </div>
                
                <h4 className="font-display text-2xl md:text-3xl mb-6 italic text-on-surface">
                  Color Over-Reliance
                </h4>
                
                <p className="font-body text-[15px] md:text-[16px] text-on-surface/85 leading-relaxed font-light mb-8">
                  Our engine detected a <span className="text-tertiary font-semibold italic">40% dependency</span> on Navy tones this month. Your style evolution would benefit from introducing warm earth tones to soften your professional silhouette.
                </p>
                
                {/* Simplified Visual Palette */}
                <div className="flex gap-2 mb-4 select-none">
                  <div className="w-12 h-1.5 rounded-full bg-tertiary"></div>
                  <div className="w-8 h-1.5 rounded-full bg-outline/30"></div>
                  <div className="w-6 h-1.5 rounded-full bg-outline/20"></div>
                </div>
              </div>
              
              <Link
                to="/app/aesthetic"
                className="group self-start flex items-center gap-3 text-tertiary hover:text-on-surface transition-all duration-300"
              >
                <span className="font-label-sm text-[11px] uppercase tracking-[0.2em] font-bold">
                  Explore New Palettes
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
