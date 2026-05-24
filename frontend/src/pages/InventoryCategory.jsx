import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const InventoryCategory = () => {
  const { categoryId } = useParams();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");

  // Scroll reveal Intersection Observer on mount and when categoryId changes
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
    revealElements.forEach((el) => {
      el.classList.remove("active"); // Reset active state so it fades up fresh on swap
      observer.observe(el);
    });

    return () => {
      revealElements.forEach((el) => observer.unobserve(el));
    };
  }, [categoryId]);

  // Dynamic catalog containing populated quiet luxury items for ALL wardrobe categories
  const catalog = {
    tops: {
      title: "Tops",
      description: "Editorial Pieces",
      items: [
        {
          id: "shirt",
          name: "Essential White Shirt",
          textile: "Poplin",
          image: "/assets/shirt_item.png",
          verified: true,
          long: true,
          hasAIService: true,
        },
        {
          id: "blouse",
          name: "Noir Silk Blouse",
          textile: "100% Silk",
          image: "/assets/blouse_recent.png",
          verified: false,
          long: false,
          hasAIService: false,
        },
        {
          id: "tee",
          name: "Essential Tee",
          textile: "Pima Cotton",
          image: "/assets/tee_item.png",
          verified: true,
          long: false,
          hasAIService: false,
        },
        {
          id: "knit",
          name: "Stone Knit",
          textile: "Cashmere",
          image: "/assets/tops_category.png",
          verified: false,
          long: true,
          hasAIService: true,
        },
      ],
    },
    bottoms: {
      title: "Bottoms",
      description: "Structured Silhouettes",
      items: [
        {
          id: "denim",
          name: "Raw Denim Jeans",
          textile: "13.5oz Selvedge",
          image: "/assets/bottoms_category.png",
          verified: true,
          long: true,
          hasAIService: true,
        },
        {
          id: "trouser",
          name: "Pleated Trousers",
          textile: "Charcoal Wool",
          image: "/assets/pleated_trousers.png",
          verified: false,
          long: false,
          hasAIService: false,
        },
        {
          id: "neutral_bottom",
          name: "Minimal Denim",
          textile: "Washed Denim",
          image: "/assets/clothing_layout_gap.png",
          verified: true,
          long: true,
          hasAIService: false,
        },
      ],
    },
    outerwear: {
      title: "Outerwear",
      description: "Layering Archives",
      items: [
        {
          id: "trench",
          name: "Wool Trench Coat",
          textile: "Charcoal Wool",
          image: "/assets/outerwear_category.png",
          verified: true,
          long: true,
          hasAIService: true,
        },
        {
          id: "bomber",
          name: "Shearling Bomber",
          textile: "Suede & Sheepskin",
          image: "/assets/shearling_jacket.png",
          verified: false,
          long: false,
          hasAIService: false,
        },
      ],
    },
    footwear: {
      title: "Shoes",
      description: "Footwear Collection",
      items: [
        {
          id: "derby",
          name: "Minimalist Derby",
          textile: "Calfskin Leather",
          image: "/assets/shoes_category.png",
          verified: true,
          long: true,
          hasAIService: true,
        },
        {
          id: "sneakers",
          name: "Essential Sneakers",
          textile: "White Leather",
          image: "/assets/sneakers_recent.png",
          verified: false,
          long: false,
          hasAIService: false,
        },
        {
          id: "boots",
          name: "Chelsea Boots",
          textile: "Black Leather",
          image: "/assets/chelsea_boots_gap.png",
          verified: true,
          long: false,
          hasAIService: true,
        },
      ],
    },
    accessories: {
      title: "Accessories",
      description: "Editorial Details",
      items: [
        {
          id: "watch",
          name: "Gold Timepiece",
          textile: "18K Gold & Leather",
          image: "/assets/gold_watch.png",
          verified: true,
          long: true,
          hasAIService: true,
        },
        {
          id: "flatlay_acc",
          name: "Atelier Flatlay",
          textile: "Curated Set",
          image: "/assets/curation_collage_feature.png",
          verified: false,
          long: false,
          hasAIService: false,
        },
      ],
    },
  };

  // Find metadata associated with categoryId or use safe stubs
  const currentCategory = catalog[categoryId] || {
    title: "Collection",
    description: "Digital Archive",
    items: [],
  };

  const filteredItems = currentCategory.items.filter(
    (item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.textile.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-8 max-w-container-max mx-auto w-full">
        {/* Search & Filter */}
        <section className="relative hero-reveal" style={{ animationDelay: "0.1s" }}>
          <div className="flex gap-4 items-center">
            <div className="relative flex-grow w-full glass-panel rounded-xl overflow-hidden flex items-center px-6 py-4 focus-within:ring-1 focus-within:ring-white/20 transition-all shadow-lg">
              <span className="material-symbols-outlined text-outline mr-4 select-none">search</span>
              <input
                className="bg-transparent border-none w-full text-on-surface font-body-md text-body-md focus:ring-0 focus:outline-none placeholder:text-outline-variant/50"
                placeholder="Search Inventory"
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

              <div className="h-6 w-[1px] bg-white/10 mx-3 select-none"></div>
              <button 
                onClick={() => navigate("/app/analysis")}
                className="text-primary hover:opacity-80 transition-opacity flex items-center justify-center p-1 cursor-pointer" 
                title="Style Filter"
              >
                <span className="material-symbols-outlined text-xl">tune</span>
              </button>
            </div>
          </div>
        </section>

        {/* Collection Header Info */}
        <section className="reveal flex justify-between items-end">
          <div>
            <h2 className="font-display text-4xl md:text-5xl text-on-surface italic luxury-text-gradient mb-1 select-none">
              {currentCategory.title}
            </h2>
            <p className="font-label-sm text-xs text-on-surface-variant uppercase tracking-[0.2em] font-semibold select-none">
              {filteredItems.length} Editorial Piece{filteredItems.length !== 1 ? "s" : ""}
            </p>
          </div>
        </section>

        {/* Masonry Inventory Grid */}
        <section className="reveal">
          {filteredItems.length > 0 ? (
            <div className="columns-2 lg:columns-4 gap-6 space-y-6">
              {filteredItems.map((item) => (
                <div
                  key={item.id}
                  className="break-inside-avoid glass-card rounded-xl overflow-hidden flex flex-col group transition-all duration-500 hover:border-primary/30 shadow-xl"
                >
                  {/* Image Block with Variable Heights */}
                  <div
                    className={`relative overflow-hidden bg-[#1A1A1A] w-full ${
                      item.long ? "aspect-[3/4.2]" : "aspect-[3/3.6]"
                    }`}
                  >
                    <img
                      className="w-full h-full object-cover transition-transform duration-1000 ease-out group-hover:scale-105"
                      src={item.image}
                      alt={item.name}
                    />
                    
                    {item.verified && (
                      <div className="absolute top-3 left-3 bg-background/60 backdrop-blur-md px-2 py-1 rounded flex items-center gap-1 border border-white/5 select-none">
                        <span
                          className="material-symbols-outlined text-[10px] text-tertiary font-bold"
                          style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                          auto_awesome
                        </span>
                        <span className="text-[8px] font-label-sm text-on-surface tracking-widest uppercase font-semibold">
                          AI Verified
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Card Content & Action Button */}
                  <div className="p-4 bg-surface-container-low flex-grow flex flex-col justify-between">
                    <div className="mb-4">
                      <p className="font-label-sm text-on-surface-variant uppercase text-[10px] tracking-wider mb-1 font-semibold select-none">
                        {item.textile}
                      </p>
                      <h3 className="font-display text-[16px] text-on-surface mb-2 leading-tight italic">
                        {item.name}
                      </h3>
                    </div>

                    <button
                      onClick={() => navigate("/app/chat")}
                      className={`w-full py-2.5 font-label-sm text-[10px] uppercase tracking-widest rounded-sm active:scale-95 transition-transform cursor-pointer font-bold duration-300 ${
                        item.hasAIService
                          ? "bg-on-surface text-background hover:bg-tertiary hover:text-on-tertiary shadow-lg"
                          : "border border-white/10 text-on-surface hover:bg-white/5"
                      }`}
                    >
                      {item.hasAIService ? "Style with AI" : "Style"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 glass-panel rounded-2xl shadow-xl animate-fade-in">
              <span className="material-symbols-outlined text-5xl opacity-40 mb-3 text-tertiary">
                checkroom
              </span>
              <p className="font-body-md text-sm text-on-surface-variant">
                No inventory pieces matched your search criteria.
              </p>
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
};

export default InventoryCategory;
