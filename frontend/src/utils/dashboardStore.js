// VOGUE.AI | Dashboard & AI Chat Assistant Client Store
// Handles async API integrations with uvicorn and provides elegant localized offline fallbacks.

import { getWardrobeItems, formatImageUrl } from "./wardrobeStore";
import { formatPreviewUrl } from "./outfitStore";

const API_BASE = "http://localhost:8000";

// Local Storage Fallback keys
const STYLE_PROFILE_KEY = "vogue_style_profile_cache";
const WEATHER_CACHE_KEY = "vogue_weather_cache";

// ── GLOBAL DEDUPLICATION REGISTRY & HELPER ────────────────────────────────────
const activePromises = new Map();

/**
 * Custom fetch wrapper that de-duplicates concurrent requests to the exact same 
 * URL, method, and request payload, resolving them to the same active promise.
 */
const dedupeFetch = async (url, options = {}) => {
  const method = options.method || "GET";
  const bodyHash = options.body ? options.body : "";
  const key = `${method}:${url}:${bodyHash}`;

  if (activePromises.has(key)) {
    console.log(`[DEDUPE] Joining existing inflight dashboard request: ${key}`);
    return activePromises.get(key);
  }

  const promise = (async () => {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`HTTP Error ${res.status}: ${errText || "Request failed"}`);
    }
    return await res.json();
  })();

  activePromises.set(key, promise);

  try {
    return await promise;
  } finally {
    activePromises.delete(key);
  }
};

// ── BACKEND API INTEGRATIONS (WITH RESILIENT LOCAL FALLBACKS) ─────────────────

/**
 * 1. Retrieves user's local climate weather data (GET /api/dashboard/weather)
 */
export const apiGetWeather = async (latitude = null, longitude = null) => {
  try {
    let url = `${API_BASE}/api/dashboard/weather`;
    if (latitude && longitude) {
      url += `?latitude=${latitude}&longitude=${longitude}`;
    }
    const data = await dedupeFetch(url);
    localStorage.setItem(WEATHER_CACHE_KEY, JSON.stringify(data));
    return data;
  } catch (err) {
    console.warn("Backend weather API unavailable, returning offline fallback:", err);
    try {
      const cached = localStorage.getItem(WEATHER_CACHE_KEY);
      if (cached) return JSON.parse(cached);
    } catch (e) {}

    // Default London overkill standard stub
    return {
      location: "London",
      temperature_celsius: 12.0,
      condition: "Overcast",
      humidity_percent: 78,
      wind_kph: 14.0,
      icon: "weather-cloudy"
    };
  }
};

/**
 * Helper: Merges thin backend garment items (UUIDs) with fully enriched Local Wardrobe data
 */
const enrichBackendItems = (backendItemIds) => {
  if (!backendItemIds) return [];
  const closetItems = getWardrobeItems();

  return backendItemIds.map(id => {
    const fullItem = closetItems.find(c => c.id === id);
    if (fullItem) {
      return {
        id: fullItem.id,
        categoryId: fullItem.categories[0],
        categoryLabel: fullItem.categories[0].charAt(0).toUpperCase() + fullItem.categories[0].slice(1),
        name: fullItem.name,
        textile: fullItem.textile,
        image: formatImageUrl(fullItem.image)
      };
    }
    return {
      id,
      categoryId: "tops",
      categoryLabel: "Tops",
      name: "Tailored Curation Garment",
      textile: "High-fashion Textile",
      image: "/assets/curation_collage_feature.png"
    };
  });
};

/**
 * 2. Fetches "Today's Curated Look" (GET /recommendations/editorial-look)
 */
export const apiGetEditorialLook = async (userId = "default_user") => {
  try {
    const data = await dedupeFetch(`${API_BASE}/recommendations/editorial-look?user_id=${userId}`);
    return {
      id: data.outfit_id,
      name: data.editorial_title || "Modern Noir",
      heroImage: formatPreviewUrl(data.hero_image_url) || "/assets/modern_noir_hero.png",
      subtitle: data.subtitle || "Architectural Minimalism",
      description: data.description || "A cinematic approach to your Monday.",
      vogueScore: data.vogue_score || 94,
      occasion: data.occasion || "COCKTAIL PARTY",
      weather: `${data.weather_context?.temperature_celsius}°C • ${data.weather_context?.condition}`,
      items: enrichBackendItems(data.clothing_item_ids),
      raw_item_ids: data.clothing_item_ids
    };
  } catch (err) {
    console.warn("Backend editorial look API failed, returning offline fallback:", err);
    return {
      id: "bc3b18d2-4411-4a46-880c-e2f47385a999",
      name: "The Editorial Edit: Modern Noir",
      heroImage: "/assets/modern_noir_hero.png",
      subtitle: "Architectural Minimalism",
      description: "A cinematic approach to your Monday. Your charcoal wool trench meets a crisp ivory knit for an aesthetic that commands the room.",
      vogueScore: 94,
      occasion: "COCKTAIL PARTY",
      weather: "London • 12°C • Overcast",
      items: enrichBackendItems(["trench", "knit", "trouser", "boots"])
    };
  }
};

/**
 * 3. Fetches runway fashion trends dynamically filtered by persona (GET /recommendations/trends)
 */
export const apiGetTrends = async (stylePersona = "minimalist", limit = 3) => {
  try {
    const data = await dedupeFetch(`${API_BASE}/recommendations/trends?style_persona=${stylePersona}&limit=${limit}`);
    return data.map(trend => ({
      ...trend,
      image_url: formatImageUrl(trend.image_url)
    }));
  } catch (err) {
    console.warn("Backend trends API failed, returning offline fallback:", err);
    return [
      {
        trend_id: "monochromatic-discipline",
        title: "The Monochromatic Discipline",
        source: "Paris Fashion Week",
        category: "Trending",
        image_url: "/assets/monochrome_trend.png",
        description: "Elevating basics through strict color discipline. A global shift towards high-contrast minimalism is emerging."
      }
    ];
  }
};

/**
 * 4. Queries calculated user style profiles & color dependency insights (GET /v1/users/style-profile)
 */
export const apiGetStyleProfile = async () => {
  try {
    const data = await dedupeFetch(`${API_BASE}/v1/users/style-profile`);
    localStorage.setItem(STYLE_PROFILE_KEY, JSON.stringify(data));
    return data;
  } catch (err) {
    console.warn("Backend style profile API failed, returning offline cached calculations:", err);
    try {
      const cached = localStorage.getItem(STYLE_PROFILE_KEY);
      if (cached) return JSON.parse(cached);
    } catch (e) {}

    // Default personal HSL color-block dependency stub
    return {
      user_id: "e43b18d2-4411-4a46-880c-e2f47385a498",
      preferred_colors: ["black", "stone", "navy"],
      disliked_colors: ["yellow"],
      preferred_styles: ["minimalist"],
      preferred_formality_range: [3, 8],
      favorite_categories: ["tops", "outerwear"],
      color_overreliance_index: {
        color_name: "Navy",
        percentage_dependency: 42.5,
        advice: "Our engine detected a 42.5% dependency on Navy tones this month. Your style evolution would benefit from introducing warm earth tones to soften your professional silhouette."
      },
      updated_at: new Date().toISOString()
    };
  }
};

/**
 * 5. Interactive Chat Styling Responses (POST /v1/chat/message)
 */
export const apiSendChatMessage = async (message, history = [], userId = "default_user") => {
  try {
    const response = await dedupeFetch(`${API_BASE}/v1/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        message,
        chat_history: history.map(msg => ({
          role: msg.sender === "user" ? "user" : "assistant",
          content: msg.text
        }))
      })
    });
    return response;
  } catch (err) {
    console.warn("Backend chatbot API down, compiling localized styling fallback:", err);
    
    // Custom local response generator
    let reply = "I recommend layering your outfits to align with the current climate region, highlighting details from your digitized closet.";
    const lower = message.toLowerCase();

    if (lower.includes("formal") || lower.includes("party") || lower.includes("cocktail")) {
      reply = "For tonight's formal setup, I highly suggest matching your Noir Silk Blouse with Pleated Wool Trousers and Derby shoes. Classy, yet effortless!";
    } else if (lower.includes("casual") || lower.includes("weekend") || lower.includes("sporty")) {
      reply = "Let's lean into upscale leisure. I'd go with your Stone Cashmere Knit, minimal white sneakers, and standard raw denim bottoms.";
    } else if (lower.includes("hello") || lower.includes("hi") || lower.includes("hey")) {
      reply = "Hello! I am your VOGUE.AI stylist assistant. Tell me what event or look we are planning today, and I'll scour your wardrobe for the perfect aesthetic!";
    } else if (lower.includes("wear today")) {
      reply = "Based on local overcast patterns, I highly suggest layering your Stone Cashmere Knit base layer with a structured coat. The texture blocks complement each other elegantly while keeping you protected.";
    }

    await new Promise(resolve => setTimeout(resolve, 800));

    return {
      reply,
      timestamp: new Date().toISOString(),
      suggested_outfit_id: lower.includes("wear today") ? "modern-minimalist" : null
    };
  }
};
