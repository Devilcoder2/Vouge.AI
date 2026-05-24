import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const Wardrobe = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  // Scroll reveal Intersection Observer on mount
  useEffect(() => {
    const observerOptions = {
      threshold: 0.05,
      rootMargin: "0px 0px -40px 0px",
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

  const categories = [
    {
      id: "tops",
      name: "Tops",
      subtitle: "Essentials",
      count: 42,
      status: "Sync Complete",
      image: "/assets/tops_category.png",
      path: "/app/inventory/tops",
    },
    {
      id: "bottoms",
      name: "Bottoms",
      subtitle: "Structured",
      count: 28,
      status: "12 Available",
      image: "/assets/bottoms_category.png",
      path: "/app/inventory/bottoms",
    },
    {
      id: "outerwear",
      name: "Outerwear",
      subtitle: "Layering",
      count: 15,
      status: "Season Ready",
      image: "/assets/outerwear_category.png",
      path: "/app/inventory/outerwear",
    },
    {
      id: "footwear",
      name: "Shoes",
      subtitle: "Footwear",
      count: 24,
      status: "Verified",
      image: "/assets/shoes_category.png",
      path: "/app/inventory/footwear",
    },
    {
      id: "accessories",
      name: "Accessories",
      subtitle: "Details",
      count: 56,
      status: "Scanning...",
      image: "/assets/curation_collage_feature.png",
      path: "/app/inventory/accessories",
    },
  ];

  const filteredCategories = categories.filter(
    (cat) =>
      cat.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cat.subtitle.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter relative">
        {/* Content Area */}
        <div className="lg:col-span-8 xl:col-span-9 space-y-12">
          {/* Enhanced Search Bar */}
          <section className="relative hero-reveal" style={{ animationDelay: "0.1s" }}>
            <div className="flex flex-col md:flex-row gap-4 items-center">
              <div className="relative flex-grow w-full glass-panel rounded-xl overflow-hidden flex items-center px-6 py-4 focus-within:ring-1 focus-within:ring-white/20 transition-all shadow-lg">
                <span className="material-symbols-outlined text-on-surface-variant/40 mr-4 select-none">
                  search
                </span>
                <input
                  className="bg-transparent border-none w-full text-on-surface font-body-md text-body-md focus:ring-0 focus:outline-none placeholder-on-surface-variant/30"
                  placeholder="Search your digital wardrobe..."
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="text-on-surface-variant/50 hover:text-on-surface transition-colors mr-3 cursor-pointer"
                    aria-label="Clear search"
                  >
                    <span className="material-symbols-outlined text-lg">close</span>
                  </button>
                )}

                <div className="flex items-center gap-3 ml-4 border-l border-white/10 pl-4 select-none">
                  <button 
                    onClick={() => navigate("/app/camera")}
                    className="text-on-surface-variant/50 hover:text-tertiary transition-colors flex items-center gap-2 group cursor-pointer" 
                    title="Visual Search"
                  >
                    <span className="material-symbols-outlined text-xl">photo_camera</span>
                    <span className="hidden md:inline font-label-sm text-[9px] uppercase tracking-widest group-hover:text-tertiary">
                      Visual
                    </span>
                  </button>
                  <button 
                    onClick={() => navigate("/app/analysis")}
                    className="text-on-surface-variant/50 hover:text-tertiary transition-colors flex items-center gap-2 group cursor-pointer" 
                    title="Style Filter"
                  >
                    <span className="material-symbols-outlined text-xl">tune</span>
                    <span className="hidden md:inline font-label-sm text-[9px] uppercase tracking-widest group-hover:text-tertiary">
                      Filter
                    </span>
                  </button>
                </div>
              </div>
              
              <button 
                onClick={() => navigate("/app/outfit")}
                className="hidden md:flex px-10 py-4 glass-panel bg-white/5 hover:bg-white/10 text-on-surface rounded-xl font-label-sm text-[10px] uppercase tracking-[0.2em] transition-all border border-white/10 active:scale-95 cursor-pointer font-bold shadow-lg"
              >
                Find Outfit
              </button>
            </div>
          </section>

          {/* Digital Wardrobe Grid */}
          <section className="reveal">
            <div className="flex items-end justify-between mb-10">
              <div>
                <h2 className="font-display text-4xl md:text-5xl italic luxury-text-gradient mb-2 select-none">
                  The Collection
                </h2>
                <p className="font-body-md text-on-surface-variant/40 tracking-[0.2em] uppercase text-[9px] font-semibold select-none">
                  Your curated digital archive
                </p>
              </div>
              
              <div className="flex gap-3 select-none">
                <button className="p-2.5 glass-panel rounded-lg text-on-surface-variant/40 hover:text-on-surface transition-all cursor-pointer">
                  <span className="material-symbols-outlined text-sm">grid_view</span>
                </button>
                <button className="p-2.5 glass-panel rounded-lg text-on-surface-variant/40 hover:text-on-surface transition-all cursor-pointer">
                  <span className="material-symbols-outlined text-sm">view_agenda</span>
                </button>
              </div>
            </div>

            {filteredCategories.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-8">
                {filteredCategories.map((cat) => (
                  <Link
                    key={cat.id}
                    to={cat.path}
                    className="category-card group relative aspect-[4/5] rounded-2xl overflow-hidden glass-panel flex flex-col justify-end p-8 hover:border-white/20 transition-all duration-700 shadow-2xl hover:scale-[1.01]"
                  >
                    <img
                      alt={cat.name}
                      className="category-image absolute inset-0 w-full h-full object-cover opacity-50 grayscale-[0.2] transition-all duration-1000 ease-out"
                      src={cat.image}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent"></div>
                    <div className="relative z-10 space-y-2">
                      <span className="font-label-sm text-[9px] text-tertiary/70 uppercase tracking-[0.3em] block font-bold">
                        {cat.subtitle}
                      </span>
                      <h3 className="font-display text-3xl luxury-text-gradient italic">
                        {cat.name}
                      </h3>
                      <div className="flex items-center gap-3 pt-4 border-t border-white/5 mt-4">
                        <span className="font-body-md text-xs text-on-surface-variant/50">
                          {cat.count} Items
                        </span>
                        <span className="w-1 h-1 rounded-full bg-white/10"></span>
                        <span className="font-label-sm text-[8px] text-on-surface-variant/40 uppercase tracking-widest font-semibold">
                          {cat.status}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}

                {/* Add New Category Card */}
                <button 
                  onClick={() => navigate("/app/camera")}
                  className="group relative aspect-[4/5] rounded-2xl overflow-hidden glass-panel flex flex-col items-center justify-center border-dashed border border-white/10 hover:border-white/20 hover:bg-white/[0.02] transition-all duration-500 cursor-pointer shadow-xl"
                >
                  <div className="w-14 h-14 rounded-full glass-panel bg-white/5 flex items-center justify-center mb-4 group-hover:bg-tertiary group-hover:text-on-tertiary transition-all duration-300 shadow-inner">
                    <span className="material-symbols-outlined text-2xl">add</span>
                  </div>
                  <span className="font-label-sm text-[10px] uppercase tracking-[0.2em] text-on-surface-variant/40 group-hover:text-on-surface font-bold">
                    New Category
                  </span>
                </button>
              </div>
            ) : (
              <div className="text-center py-16 glass-panel rounded-2xl shadow-xl">
                <span className="material-symbols-outlined text-5xl opacity-40 mb-3 text-tertiary">
                  checkroom
                </span>
                <p className="font-body-md text-sm text-on-surface-variant">
                  No matching wardrobe categories found.
                </p>
              </div>
            )}
          </section>
        </div>

        {/* Refined Sidebar */}
        <aside className="hidden lg:flex lg:col-span-4 xl:col-span-3 flex-col gap-gutter reveal">
          {/* Stats Card */}
          <div className="glass-panel rounded-2xl p-8 ai-glow shadow-xl">
            <h3 className="font-display text-xl italic luxury-text-gradient mb-8 select-none">
              Wardrobe Pulse
            </h3>
            
            <div className="space-y-8">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1.5 font-bold">
                    Items Sync
                  </p>
                  <p className="font-display text-2xl luxury-text-gradient font-semibold">
                    84%
                  </p>
                </div>
                <span className="material-symbols-outlined text-tertiary/20 text-2xl">
                  cloud_done
                </span>
              </div>
              
              <div className="h-[2px] bg-white/5 rounded-full overflow-hidden select-none">
                <div className="h-full bg-tertiary/60 w-[84%] rounded-full"></div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/5">
                <div>
                  <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1.5 font-bold">
                    Total Pieces
                  </p>
                  <p className="font-display text-xl luxury-text-gradient font-semibold">
                    1,248
                  </p>
                </div>
                <div>
                  <p className="font-label-sm text-[9px] text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1.5 font-bold">
                    Outfits
                  </p>
                  <p className="font-display text-xl luxury-text-gradient font-semibold">
                    342
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recently Viewed */}
          <div className="glass-panel rounded-2xl p-8 flex flex-col flex-grow shadow-xl">
            <h3 className="font-display text-xl italic luxury-text-gradient mb-8 select-none">
              Recent History
            </h3>
            
            <div className="space-y-6 flex-grow overflow-y-auto no-scrollbar max-h-[350px]">
              {/* Blouse */}
              <div 
                onClick={() => navigate("/app/item/tops/blouse")}
                className="flex items-center gap-4 group cursor-pointer"
              >
                <div className="w-16 h-20 rounded-lg overflow-hidden flex-shrink-0 glass-panel shadow-md">
                  <img
                    alt="Noir Silk"
                    className="w-full h-full object-cover grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
                    src="/assets/blouse_recent.png"
                  />
                </div>
                <div>
                  <h4 className="font-body text-xs text-on-surface-variant/80 group-hover:text-on-surface transition-colors font-medium">
                    Noir Silk Blouse
                  </h4>
                  <p className="font-label-sm text-[8px] text-on-surface-variant/30 uppercase mt-1.5 tracking-widest font-semibold">
                    2 hours ago
                  </p>
                </div>
              </div>

              {/* Sneakers */}
              <div 
                onClick={() => navigate("/app/item/footwear/sneakers")}
                className="flex items-center gap-4 group cursor-pointer"
              >
                <div className="w-16 h-20 rounded-lg overflow-hidden flex-shrink-0 glass-panel shadow-md">
                  <img
                    alt="Low Tops"
                    className="w-full h-full object-cover grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
                    src="/assets/sneakers_recent.png"
                  />
                </div>
                <div>
                  <h4 className="font-body text-xs text-on-surface-variant/80 group-hover:text-on-surface transition-colors font-medium">
                    Essential Sneakers
                  </h4>
                  <p className="font-label-sm text-[8px] text-on-surface-variant/30 uppercase mt-1.5 tracking-widest font-semibold">
                    Yesterday
                  </p>
                </div>
              </div>
            </div>
            
            <button 
              onClick={() => navigate("/app/discover")}
              className="mt-8 text-on-surface-variant/40 hover:text-on-surface transition-colors font-label-sm text-[9px] uppercase tracking-[0.2em] text-left font-bold cursor-pointer"
            >
              View All History
            </button>
          </div>

          {/* Premium CTA */}
          <div className="relative rounded-2xl overflow-hidden p-8 border border-white/5 bg-gradient-to-br from-white/[0.03] to-transparent shadow-xl">
            <h3 className="font-display text-lg mb-2 italic luxury-text-gradient select-none">
              Elevate Status
            </h3>
            <p className="font-body text-[11px] text-on-surface-variant/40 mb-8 leading-relaxed font-light select-none">
              Unlock generative fabric analysis and private collection vaults.
            </p>
            <button 
              onClick={() => navigate("/app/profile")}
              className="w-full py-4 glass-panel bg-white/5 hover:bg-white/10 text-on-surface rounded-lg font-label-sm text-[9px] uppercase tracking-[0.3em] transition-all cursor-pointer font-bold active:scale-95"
            >
              Go Premium
            </button>
          </div>
        </aside>
      </div>

      {/* Contextual FAB (Mobile Upload New Item) */}
      <button
        onClick={() => navigate("/app/camera")}
        aria-label="Upload New Item"
        className="md:hidden fixed bottom-24 right-6 z-[55] w-14 h-14 glass-panel bg-white/10 text-on-surface rounded-full flex items-center justify-center shadow-2xl hover:scale-105 active:scale-95 transition-transform cursor-pointer"
      >
        <span className="material-symbols-outlined text-2xl font-bold">add</span>
      </button>
    </Layout>
  );
};

export default Wardrobe;
