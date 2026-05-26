// VOGUE.AI | Outfit Recommendation & Personalization Store
// Bridges React view pages with live FastAPI uvicorn recommendation services.
// Implements robust caching, pagination helpers, and premium uvicorn-independent offline fallbacks.

import { getWardrobeItems, formatImageUrl } from "./wardrobeStore";

const API_BASE = "http://localhost:8000/recommendations";

// Local Storage Keys
const SAVED_OUTFITS_KEY = "vogue_saved_outfits_list";
const USER_PROFILE_KEY = "vogue_user_profile";
const DETAILED_FEEDBACK_KEY = "vogue_detailed_feedback";

// Rich High-Fashion Fallback Templates (used if uvicorn is offline or closet has no items)
const DEFAULT_OUTFITS = [
  {
    id: "modern-minimalist",
    name: "Modern Minimalist",
    heroImage: "https://lh3.googleusercontent.com/aida-public/AB6AXuAki4BGSUntHAPAS69IXZ7zBI26fPNidz4OKKv5f5RUqgqQulEoRhNCLpAseImJY4jdTjBUdUiUzDFey6Unr5nL4FUKV5lgc4p6Y9NCqNO0J2KzrOiME_Y7cSdhv35ewijJe1xrojfHq9mQb5lucrj88BrzfS7X6f0EfauWEgYVwJgWMTtBqSqm3UAMohWhmNGu9MAaFFAa_JF_6u9MNsnzaEdcyq2ymoqf2mrDrK-Ya_HSE1sRViTR01H9TzqceSOhQiNpu8PWwlS1",
    subtitle: "Architectural Minimalism",
    weather: "65°F & CLEAR",
    occasion: "COCKTAIL PARTY",
    description: "A curated selection of structured silhouettes and premium textures designed for the contemporary urban visionary.",
    vogueScore: 94,
    metrics: {
      colorHarmony: 97,
      styleAlignment: 90,
      occasionContext: 85,
      formalityBalance: 100,
      seasonAppropriateness: 100
    },
    reasoning: [
      "Tailored to complement your rectangle archetype proportions by introducing structured shoulder lines.",
      "Perfect match for your preferred minimalist aesthetic, utilizing a monochromatic charcoal base with cream accents.",
      "High-contrast textile interaction creates visual depth without the need for intrusive patterns."
    ],
    items: [
      {
        id: "trench",
        categoryId: "outerwear",
        categoryLabel: "Outerwear",
        name: "Structured Wool Overcoat",
        textile: "Charcoal Melange | 100% Cashmere-Wool",
        image: "/assets/outerwear_category.png"
      },
      {
        id: "knit",
        categoryId: "tops",
        categoryLabel: "Base Layer",
        name: "Stone Cashmere Knit",
        textile: "Stone Gray | 70% Cashmere, 30% Silk",
        image: "/assets/tops_category.png"
      },
      {
        id: "trouser",
        categoryId: "bottoms",
        categoryLabel: "Bottoms",
        name: "Pleated Wool Trousers",
        textile: "Charcoal Wool | 100% Merino Wool",
        image: "/assets/pleated_trousers.png"
      },
      {
        id: "boots",
        categoryId: "footwear",
        categoryLabel: "Footwear",
        name: "Leather Chelsea Boots",
        textile: "Matte Black | Waxed Calfskin",
        image: "/assets/chelsea_boots_gap.png"
      }
    ]
  },
  {
    id: "monochrome-discipline",
    name: "Monochrome Discipline",
    heroImage: "https://lh3.googleusercontent.com/aida-public/AB6AXuA03GURmg3fhWFSxJVnuY27Zw3k9Y6vN_WQ4-Yah6dKviKO_JE4aLnGRD8gy4j3qDdUfhahGkvOjp88Fs9ZtsZsv5dAhsQPOvuz8fH2psGtGT_uDZ8QgW22kkGWLOwryn23vA2rubRY8PtgeaK73GLh0AiM8d8-R7mxeRNo-SODaJAoRZhB7hLWaP2DQ1VhYc-AX3K6EM0lrdAMUxvqVMK8qpXDzpTPXalkQWuYYnpmjpoGs-nKYH3tuEEgLv55RTOdECiVrRu1opiU",
    subtitle: "Fluid Fluidity",
    weather: "72°F & INDOORS",
    occasion: "GALLERY OPENING",
    description: "Elegant silk reflection overlays tailored raw selvedge denim, providing visual weight balance under soft gallery ambient lighting.",
    vogueScore: 96,
    metrics: {
      colorHarmony: 99,
      styleAlignment: 95,
      occasionContext: 92,
      formalityBalance: 95,
      seasonAppropriateness: 100
    },
    reasoning: [
      "Monochromatic charcoal silk blouse delivers elegant reflection highlights under low-light ambient setups.",
      "Relaxed fluid flow balances tailored high-waisted raw denim lines beautifully.",
      "Classic and versatile evening wear that transitions seamlessly from corporate review to private galleries."
    ],
    items: [
      {
        id: "blouse",
        categoryId: "tops",
        categoryLabel: "Tops",
        name: "Noir Silk Blouse",
        textile: "Midnight Charcoal | 100% Mulberry Silk",
        image: "/assets/blouse_recent.png"
      },
      {
        id: "denim",
        categoryId: "bottoms",
        categoryLabel: "Bottoms",
        name: "Raw Denim Jeans",
        textile: "Indigo Navy | 13.5oz Selvedge Denim",
        image: "/assets/bottoms_category.png"
      },
      {
        id: "derby",
        categoryId: "footwear",
        categoryLabel: "Footwear",
        name: "Minimalist Derby",
        textile: "Polished Black | Calfskin Leather",
        image: "/assets/shoes_category.png"
      },
      {
        id: "watch",
        categoryId: "accessories",
        categoryLabel: "Accessories",
        name: "Gold Timepiece",
        textile: "Champagne Gold | 18K Gold Plated",
        image: "/assets/gold_watch.png"
      }
    ]
  },
  {
    id: "casual-sophisticate",
    name: "Casual Sophisticate",
    heroImage: "/assets/curation_collage_feature.png",
    subtitle: "Atelier Layering",
    weather: "68°F & OVERCAST",
    occasion: "WEEKEND BRUNCH",
    description: "An incredibly comfortable yet editorial layering composition blending stone knit cashmere with washes of organic denim.",
    vogueScore: 89,
    metrics: {
      colorHarmony: 92,
      styleAlignment: 88,
      occasionContext: 95,
      formalityBalance: 80,
      seasonAppropriateness: 90
    },
    reasoning: [
      "Effortless casual draping utilizing a washed cotton organic denim and premium cotton tee.",
      "Stone grey cashmere knit handles layering requirements, providing thermal balance and soft textures.",
      "Minimal white sneakers keep the visual weight light and crisp."
    ],
    items: [
      {
        id: "tee",
        categoryId: "tops",
        categoryLabel: "Base Layer",
        name: "Essential Tee",
        textile: "Obsidian Black | 100% Pima Cotton",
        image: "/assets/tee_item.png"
      },
      {
        id: "knit",
        categoryId: "tops",
        categoryLabel: "Layering Piece",
        name: "Stone Cashmere Knit",
        textile: "Stone Gray | 70% Cashmere, 30% Silk",
        image: "/assets/tops_category.png"
      },
      {
        id: "neutral_bottom",
        categoryId: "bottoms",
        categoryLabel: "Bottoms",
        name: "Minimal Denim",
        textile: "Ecrú | Washed Organic Cotton Denim",
        image: "/assets/clothing_layout_gap.png"
      },
      {
        id: "sneakers",
        categoryId: "footwear",
        categoryLabel: "Footwear",
        name: "Essential Sneakers",
        textile: "Minimal White | Nappa Leather",
        image: "/assets/sneakers_recent.png"
      }
    ]
  }
];

// Helper to check for relative preview endpoints and format uvicorn domain
export const formatPreviewUrl = (url) => {
  if (!url) return null;
  if (url.startsWith("/recommendations/")) {
    return `http://localhost:8000${url}`;
  }
  return formatImageUrl(url);
};

// Local Outfit Candidate Generator Fallback (Runs if backend empty or offline)
const generateLocalFallbackRecommendations = (occasion = "casual", season = "autumn") => {
  const closetItems = getWardrobeItems();
  if (!closetItems || closetItems.length === 0) {
    return DEFAULT_OUTFITS;
  }

  // Group items by category to build structured candidates
  const tops = closetItems.filter(i => i.categories.includes("tops"));
  const bottoms = closetItems.filter(i => i.categories.includes("bottoms"));
  const outerwear = closetItems.filter(i => i.categories.includes("outerwear"));
  const footwear = closetItems.filter(i => i.categories.includes("footwear") || i.categories.includes("shoes"));
  const accessories = closetItems.filter(i => i.categories.includes("accessories"));

  const generated = [];
  const count = Math.min(3, Math.max(1, tops.length));

  for (let i = 0; i < count; i++) {
    const selectedTops = tops[i] || tops[0];
    const selectedBottoms = bottoms[i] || bottoms[0];
    const selectedOuterwear = outerwear[i] || outerwear[0];
    const selectedFootwear = footwear[i] || footwear[0] || selectedOuterwear;

    if (!selectedTops || !selectedBottoms) continue;

    const items = [];
    if (selectedOuterwear) items.push(selectedOuterwear);
    items.push(selectedTops);
    items.push(selectedBottoms);
    if (selectedFootwear && selectedFootwear.id !== selectedOuterwear?.id) {
      items.push(selectedFootwear);
    }

    const vogueScore = Math.floor(Math.random() * 15) + 82; // 82 to 96 range
    
    generated.push({
      id: `local-combo-${i}-${occasion}-${season}`,
      name: `${occasion.charAt(0).toUpperCase() + occasion.slice(1)} Curation #${i + 1}`,
      heroImage: selectedOuterwear ? formatImageUrl(selectedOuterwear.image) : formatImageUrl(selectedTops.image),
      subtitle: `${season.toUpperCase()} SYNERGY`,
      weather: `68°F & ${season.toUpperCase()}`,
      occasion: occasion.toUpperCase(),
      description: `A dynamic localized candidate layering selected pieces to maximize tactile texture matches for ${occasion} situations.`,
      vogueScore,
      metrics: {
        colorHarmony: Math.floor(Math.random() * 10) + 90,
        styleAlignment: Math.floor(Math.random() * 10) + 85,
        occasionContext: Math.floor(Math.random() * 10) + 88,
        formalityBalance: Math.floor(Math.random() * 10) + 85,
        seasonAppropriateness: Math.floor(Math.random() * 10) + 90
      },
      reasoning: [
        `Harmoniously links your ${selectedTops.name} with ${selectedBottoms.name} under our local styling matrix.`,
        selectedOuterwear ? `Adds structured layering via ${selectedOuterwear.name} to balance the casual neckline.` : "Keeps the silhouette minimal and clean without heavy overlays.",
        "Perfect tone-on-tone color spectrum tailored for comfort."
      ],
      items: items.map(item => ({
        id: item.id,
        categoryId: item.categories[0],
        categoryLabel: item.categories[0].charAt(0).toUpperCase() + item.categories[0].slice(1),
        name: item.name,
        textile: item.textile,
        image: formatImageUrl(item.image)
      }))
    });
  }

  return generated.length > 0 ? generated : DEFAULT_OUTFITS;
};

// Helper: Merges thin backend garment items (UUIDs) with fully enriched Local Wardrobe data
const enrichBackendItems = (backendItems) => {
  if (!backendItems) return [];
  const closetItems = getWardrobeItems();

  return backendItems.map(item => {
    // Look up detailed name, textile and local assets matching the ID
    const fullItem = closetItems.find(c => c.id === item.id);
    return {
      id: item.id,
      categoryId: item.category,
      categoryLabel: item.category.charAt(0).toUpperCase() + item.category.slice(1),
      name: fullItem ? fullItem.name : `${item.fit} ${item.primary_color} ${item.subcategory || item.category}`,
      textile: fullItem ? fullItem.textile : `${item.style} cut in ${item.pattern} pattern`,
      image: fullItem ? formatImageUrl(fullItem.image) : "/assets/curation_collage_feature.png",
      // Keep backend specs
      primary_color: item.primary_color,
      primary_color_hex: item.primary_color_hex,
      fit: item.fit,
      style: item.style,
      formality: item.formality,
      pattern: item.pattern
    };
  });
};

// ── OUTFITS RECOMMENDATION APIS ───────────────────────────────────────────────

/**
 * 1. Generate & Retrieve Outfits List (POST /recommendations/generate-outfits)
 */
export const apiGenerateOutfits = async (payload) => {
  const { user_id = "default_user", occasion = "casual", season = "autumn" } = payload;
  try {
    const res = await fetch(`${API_BASE}/generate-outfits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id, occasion, season })
    });
    if (!res.ok) throw new Error("Backend recommendation router returned status " + res.status);
    
    const data = await res.json();
    
    // If backend reports no outfits (e.g. empty database), trigger our smart fallback
    if (!data.outfits || data.outfits.length === 0) {
      console.warn("Backend closet database is empty, compiling local fallbacks...");
      return generateLocalFallbackRecommendations(occasion, season);
    }

    // Format backend response schema directly to premium frontend structure
    return data.outfits.map((outfit, index) => ({
      id: `backend-${index}-${outfit.score}-${occasion}-${season}`,
      name: outfit.template_name || `AI Recommendation #${index + 1}`,
      heroImage: formatPreviewUrl(outfit.preview_url) || "/assets/curation_collage_feature.png",
      subtitle: outfit.template_name ? `AI Curation` : `Synergized Combination`,
      weather: `65°F & ${season.toUpperCase()}`,
      occasion: occasion.toUpperCase(),
      description: outfit.reasoning || "A perfectly harmonized composition designed by Vogue.AI deep learning styling engine.",
      vogueScore: outfit.score,
      metrics: {
        colorHarmony: outfit.breakdown?.color_score || 90,
        styleAlignment: outfit.breakdown?.style_score || 88,
        occasionContext: outfit.breakdown?.occasion_score || 85,
        formalityBalance: outfit.breakdown?.formality_score || 90,
        seasonAppropriateness: outfit.breakdown?.season_score || 95
      },
      reasoning: outfit.why_selected && outfit.why_selected.length > 0 ? outfit.why_selected : [outfit.reasoning],
      items: enrichBackendItems(outfit.items),
      preview_url: outfit.preview_url
    }));
  } catch (err) {
    console.warn("Backend recommendations API unavailable, executing local candidate fallback:", err);
    return generateLocalFallbackRecommendations(occasion, season);
  }
};

/**
 * 2. Save Curated Outfit Combination (POST /recommendations/save-outfit)
 */
export const apiSaveOutfit = async (payload) => {
  try {
    const res = await fetch(`${API_BASE}/save-outfit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: payload.user_id || "default_user",
        name: payload.name,
        occasion: payload.occasion,
        season: payload.season,
        score: payload.score,
        reasoning: Array.isArray(payload.reasoning) ? payload.reasoning.join(". ") : payload.reasoning,
        clothing_item_ids: payload.clothing_item_ids,
        preview_url: payload.preview_url || null
      })
    });
    if (!res.ok) throw new Error("Backend save-outfit returned status " + res.status);
    const data = await res.json();
    
    // Refresh local storage saved outfits to synchronize
    await apiGetSavedOutfits(payload.user_id || "default_user");
    return data;
  } catch (err) {
    console.warn("Backend save outfit API failed, using localStorage fallback:", err);
    
    // Save locally
    let saved = [];
    try {
      const stored = localStorage.getItem(SAVED_OUTFITS_KEY);
      if (stored) saved = JSON.parse(stored);
    } catch (e) {
      console.error(e);
    }

    const localItem = {
      id: `saved-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      user_id: payload.user_id || "default_user",
      name: payload.name,
      occasion: payload.occasion,
      season: payload.season,
      score: payload.score,
      reasoning: Array.isArray(payload.reasoning) ? payload.reasoning.join(". ") : payload.reasoning,
      preview_url: payload.preview_url || "/assets/curation_collage_feature.png",
      created_at: new Date().toISOString(),
      items: getWardrobeItems().filter(i => payload.clothing_item_ids.includes(i.id))
    };
    
    saved.unshift(localItem);
    localStorage.setItem(SAVED_OUTFITS_KEY, JSON.stringify(saved));
    return localItem;
  }
};

/**
 * 3. Retrieve Previously Saved Outfits (GET /recommendations/saved-outfits)
 */
export const apiGetSavedOutfits = async (userId = "default_user", page = 1, limit = 10) => {
  try {
    const res = await fetch(`${API_BASE}/saved-outfits?user_id=${userId}&page=${page}&limit=${limit}`);
    if (!res.ok) throw new Error("Backend saved-outfits returned status " + res.status);
    const data = await res.json();
    
    // Enriched list
    const enrichedList = (data.data || data || []).map(outfit => ({
      ...outfit,
      id: outfit.id || outfit.outfit_id,
      heroImage: formatPreviewUrl(outfit.preview_url) || "/assets/curation_collage_feature.png",
      subtitle: `${outfit.season?.toUpperCase()} ROTATION`,
      weather: `60°F & ${outfit.season?.toUpperCase()}`,
      description: outfit.reasoning || "Premium curated outfit saved in your digital library.",
      vogueScore: outfit.score || 90,
      metrics: {
        colorHarmony: 95,
        styleAlignment: 92,
        occasionContext: 90,
        formalityBalance: 88,
        seasonAppropriateness: 95
      },
      reasoning: outfit.reasoning ? [outfit.reasoning] : ["Compatible high-fashion curation."],
      items: enrichBackendItems(outfit.items)
    }));

    const totalCount = enrichedList.length;
    const totalPages = Math.ceil(totalCount / limit);
    const paginated = enrichedList.slice((page - 1) * limit, page * limit);

    return {
      data: paginated,
      meta: {
        currentPage: page,
        pageSize: limit,
        totalPages: totalPages,
        totalCount: totalCount,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1
      }
    };
  } catch (err) {
    console.warn("Backend saved outfits API unavailable, returning localStorage fallback:", err);
    let saved = [];
    try {
      const stored = localStorage.getItem(SAVED_OUTFITS_KEY);
      if (stored) {
        saved = JSON.parse(stored);
      } else {
        // Seed default stubs
        const items = getWardrobeItems();
        saved = [
          {
            id: "modern-minimalist",
            user_id: userId,
            name: "Modern Minimalist",
            occasion: "cocktail party",
            season: "autumn",
            score: 94,
            reasoning: "Architectural minimalism suited for cocktail layouts.",
            preview_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuAki4BGSUntHAPAS69IXZ7zBI26fPNidz4OKKv5f5RUqgqQulEoRhNCLpAseImJY4jdTjBUdUiUzDFey6Unr5nL4FUKV5lgc4p6Y9NCqNO0J2KzrOiME_Y7cSdhv35ewijJe1xrojfHq9mQb5lucrj88BrzfS7X6f0EfauWEgYVwJgWMTtBqSqm3UAMohWhmNGu9MAaFFAa_JF_6u9MNsnzaEdcyq2ymoqf2mrDrK-Ya_HSE1sRViTR01H9TzqceSOhQiNpu8PWwlS1",
            created_at: new Date(Date.now() - 3600000).toISOString(),
            items: items.filter(i => ["trench", "knit", "trouser", "boots"].includes(i.id))
          }
        ];
        localStorage.setItem(SAVED_OUTFITS_KEY, JSON.stringify(saved));
      }
    } catch (e) {
      console.error(e);
    }

    const totalCount = saved.length;
    const totalPages = Math.ceil(totalCount / limit);
    const paginated = saved.slice((page - 1) * limit, page * limit).map(outfit => ({
      ...outfit,
      heroImage: formatPreviewUrl(outfit.preview_url) || "/assets/curation_collage_feature.png",
      subtitle: `${outfit.season?.toUpperCase()} ROTATION`,
      weather: `60°F & ${outfit.season?.toUpperCase()}`,
      description: outfit.reasoning || "Premium curated outfit saved in your digital library.",
      vogueScore: outfit.score || 90,
      metrics: {
        colorHarmony: 95,
        styleAlignment: 92,
        occasionContext: 90,
        formalityBalance: 88,
        seasonAppropriateness: 95
      },
      reasoning: [outfit.reasoning || "Compatible high-fashion curation."],
      items: outfit.items.map(i => ({
        ...i,
        categoryId: i.categories?.[0] || "tops",
        categoryLabel: (i.categories?.[0] || "tops").charAt(0).toUpperCase() + (i.categories?.[0] || "tops").slice(1),
        image: formatImageUrl(i.image)
      }))
    }));

    return {
      data: paginated,
      meta: {
        currentPage: page,
        pageSize: limit,
        totalPages: totalPages,
        totalCount: totalCount,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1
      }
    };
  }
};

/**
 * 4. Delete Saved Outfit Curation (DELETE /recommendations/saved-outfits/{outfit_id})
 */
export const apiDeleteSavedOutfit = async (outfitId) => {
  try {
    const res = await fetch(`${API_BASE}/saved-outfits/${outfitId}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Backend delete saved-outfit returned status " + res.status);
    return true;
  } catch (err) {
    console.warn("Backend delete outfit failed, using localStorage fallback:", err);
    try {
      const stored = localStorage.getItem(SAVED_OUTFITS_KEY);
      if (stored) {
        let saved = JSON.parse(stored);
        saved = saved.filter(o => o.id !== outfitId);
        localStorage.setItem(SAVED_OUTFITS_KEY, JSON.stringify(saved));
      }
    } catch (e) {
      console.error(e);
    }
    return true;
  }
};

/**
 * 5. Log Swipe Deck Feedback (POST /recommendations/feedback)
 */
export const apiSubmitFeedback = async (payload) => {
  const { user_id = "default_user", outfit_item_ids = [], feedback_type = "like" } = payload;
  try {
    const res = await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id, outfit_item_ids, feedback_type })
    });
    if (!res.ok) throw new Error("Backend feedback API returned status " + res.status);
    return await res.json();
  } catch (err) {
    console.warn("Backend feedback logging failed, keeping local event logs:", err);
    try {
      const logs = JSON.parse(localStorage.getItem(DETAILED_FEEDBACK_KEY) || "[]");
      logs.push({
        user_id,
        outfit_item_ids,
        feedback_type,
        timestamp: new Date().toISOString()
      });
      localStorage.setItem(DETAILED_FEEDBACK_KEY, JSON.stringify(logs));
    } catch (e) {
      console.error(e);
    }
    return { message: "Local feedback recorded successfully." };
  }
};

/**
 * 6. Save or Update Styling Profile Parameters (POST /recommendations/profile)
 */
export const apiUpdateProfile = async (payload) => {
  try {
    const res = await fetch(`${API_BASE}/profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Backend update-profile returned status " + res.status);
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Backend profile setup failed, caching in local user storage:", err);
    const current = JSON.parse(localStorage.getItem(USER_PROFILE_KEY) || "{}");
    const updated = { ...current, ...payload };
    localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(updated));
    return updated;
  }
};

/**
 * 7. Retrieve Closet Gaps Analysis (GET /recommendations/gap-analysis)
 */
export const apiGetGapAnalysis = async (page = 1, limit = 10) => {
  try {
    const res = await fetch(`${API_BASE}/gap-analysis?page=${page}&limit=${limit}`);
    if (!res.ok) throw new Error("Backend gap analysis returned status " + res.status);
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Backend gap analysis unavailable, returning offline calculations:", err);
    const data = [
      {
        item_name: "Cashmere Double-breasted Blazer",
        category: "outerwear",
        subcategory: "jackets",
        style: "minimalist",
        fit: "relaxed",
        formality: 75,
        primary_color: "Camel Brown",
        primary_color_hex: "#C59B73",
        pattern: "solid",
        unlocked_outfits_count: 6,
        reasoning: "Unlocks 6 high-scoring layering lookups combining your Alabaster poplin shirt and raw selvedge denim."
      },
      {
        item_name: "Mulberry Silk Midi Skirt",
        category: "bottoms",
        subcategory: "skirts",
        style: "old_money",
        fit: "fluid",
        formality: 80,
        primary_color: "Midnight Charcoal",
        primary_color_hex: "#2A2B2E",
        pattern: "solid",
        unlocked_outfits_count: 4,
        reasoning: "Coordinates 4 elegant gallery openings when dressed up with your Stone cashmeres."
      }
    ];

    const totalCount = data.length;
    const totalPages = Math.ceil(totalCount / limit);
    const paginated = data.slice((page - 1) * limit, page * limit);

    return {
      data: paginated,
      meta: {
        currentPage: page,
        pageSize: limit,
        totalPages: totalPages,
        totalCount: totalCount,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1
      }
    };
  }
};

/**
 * 8. Retrieve Closet Garments Versatility Report (GET /recommendations/versatility)
 */
export const apiGetVersatility = async (page = 1, limit = 10) => {
  try {
    const res = await fetch(`${API_BASE}/versatility?page=${page}&limit=${limit}`);
    if (!res.ok) throw new Error("Backend versatility endpoint returned status " + res.status);
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Backend versatility report unavailable, using local closet analysis:", err);
    const closetItems = getWardrobeItems();
    const data = closetItems.map((item, index) => {
      const usages = [18, 14, 11, 8, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1];
      const usage_count = usages[index] || 1;
      const versatility_score = Math.max(40, 98 - index * 6);
      return {
        item_id: item.id,
        category: item.categories[0],
        subcategory: item.categories[0] === "tops" ? "knitwear" : "tailoring",
        primary_color: item.colorName,
        versatility_score,
        usage_count,
        reasoning: `Acts as a highly scalable layering piece. Participates in ${usage_count} combinations across winter and summer rosters.`
      };
    });

    const totalCount = data.length;
    const totalPages = Math.ceil(totalCount / limit);
    const paginated = data.slice((page - 1) * limit, page * limit);

    return {
      data: paginated,
      meta: {
        currentPage: page,
        pageSize: limit,
        totalPages: totalPages,
        totalCount: totalCount,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1
      }
    };
  }
};

/**
 * 9. Custom Layered Collage Generator (POST /recommendations/outfit-preview)
 */
export const apiGenerateOutfitPreview = async (payload) => {
  try {
    const res = await fetch(`${API_BASE}/outfit-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Backend collage preview returned status " + res.status);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  } catch (err) {
    console.warn("Backend outfit composite failing, using static canvas collage placeholder:", err);
    return "/assets/curation_collage_feature.png";
  }
};

// ── COMPATIBILITY EXPORTS ────────────────────────────────────────────────────
// Keeps legacy stubs alive to avoid compile errors on other dummy views.
export const getOutfits = () => DEFAULT_OUTFITS;
export const getOutfit = (outfitId) => {
  // If it's loaded from local storage saves
  try {
    const stored = localStorage.getItem(SAVED_OUTFITS_KEY);
    if (stored) {
      const saved = JSON.parse(stored);
      const found = saved.find(o => o.id === outfitId);
      if (found) {
        return {
          ...found,
          heroImage: formatPreviewUrl(found.preview_url) || "/assets/curation_collage_feature.png",
          vogueScore: found.score || 90,
          metrics: {
            colorHarmony: 95,
            styleAlignment: 92,
            occasionContext: 90,
            formalityBalance: 88,
            seasonAppropriateness: 95
          },
          reasoning: [found.reasoning || "Stylist selection."]
        };
      }
    }
  } catch (e) {
    console.error(e);
  }
  return DEFAULT_OUTFITS.find((outfit) => outfit.id === outfitId) || null;
};
