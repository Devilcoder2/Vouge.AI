// Quiet Luxury Wardrobe Store - Vogue.AI
// Handles persistence in localStorage to make the application scalable and interactive.

const DEFAULT_ITEMS = [
  {
    id: "shirt",
    name: "Essential White Shirt",
    textile: "100% Poplin Cotton",
    colorName: "Alabaster White",
    colorHex: "#F5F5F7",
    secondaryColors: [],
    moreDetails: "Crafted in crisp long-staple Italian poplin, featuring a tailored silhouette and premium structural collar.",
    occasion: "work",
    image: "/assets/shirt_item.png",
    verified: true,
    long: true,
    hasAIService: true,
    categories: ["tops"]
  },
  {
    id: "blouse",
    name: "Noir Silk Blouse",
    textile: "100% Mulberry Silk",
    colorName: "Midnight Charcoal",
    colorHex: "#2A2B2E",
    secondaryColors: [
      { name: "Obsidian Black", hex: "#121317" }
    ],
    moreDetails: "Designed with an elegant fluid drape, featuring subtle sheen and delicate mother-of-pearl button details.",
    occasion: "evening",
    image: "/assets/blouse_recent.png",
    verified: false,
    long: false,
    hasAIService: false,
    categories: ["tops"]
  },
  {
    id: "tee",
    name: "Essential Tee",
    textile: "100% Pima Cotton",
    colorName: "Obsidian Black",
    colorHex: "#121317",
    secondaryColors: [
      { name: "Slate Gray", hex: "#707A8A" }
    ],
    moreDetails: "Classic crewneck crafted from ultra-soft Peruvian Pima cotton with double-needle stitch finishing.",
    occasion: "casual",
    image: "/assets/tee_item.png",
    verified: true,
    long: false,
    hasAIService: false,
    categories: ["tops"]
  },
  {
    id: "knit",
    name: "Stone Knit",
    textile: "70% Cashmere, 30% Silk",
    colorName: "Stone Gray",
    colorHex: "#8E9192",
    secondaryColors: [
      { name: "Alabaster White", hex: "#F5F5F7" }
    ],
    moreDetails: "Premium waffle knit structure, incredibly insulating yet lightweight, tailored with ribbed hems.",
    occasion: "casual",
    image: "/assets/tops_category.png",
    verified: false,
    long: true,
    hasAIService: true,
    categories: ["tops", "outerwear"] // Cashmere knit belongs to both Tops and Outerwear!
  },
  {
    id: "denim",
    name: "Raw Denim Jeans",
    textile: "13.5oz Selvedge Denim",
    colorName: "Indigo Navy",
    colorHex: "#1C2E4A",
    secondaryColors: [],
    moreDetails: "Japanese selvedge rigid denim with an indigo dyed warp, copper rivets, and a classic straight leg line.",
    occasion: "casual",
    image: "/assets/bottoms_category.png",
    verified: true,
    long: true,
    hasAIService: true,
    categories: ["bottoms"]
  },
  {
    id: "trouser",
    name: "Pleated Trousers",
    textile: "100% Merino Wool",
    colorName: "Charcoal Gray",
    colorHex: "#343539",
    secondaryColors: [
      { name: "Obsidian Black", hex: "#121317" }
    ],
    moreDetails: "Features double front pleats, adjustable side tabs, and a refined drape that breaks perfectly over boots.",
    occasion: "work",
    image: "/assets/pleated_trousers.png",
    verified: false,
    long: false,
    hasAIService: false,
    categories: ["bottoms"]
  },
  {
    id: "neutral_bottom",
    name: "Minimal Denim",
    textile: "Washed Organic Cotton Denim",
    colorName: "Ecrú",
    colorHex: "#E5E2E1",
    secondaryColors: [
      { name: "Cashmere Creme", hex: "#F5EBE6" }
    ],
    moreDetails: "Soft washed organic cotton in a neutral bone hue, featuring a relaxed mid-rise silhouette.",
    occasion: "casual",
    image: "/assets/clothing_layout_gap.png",
    verified: true,
    long: true,
    hasAIService: false,
    categories: ["bottoms"]
  },
  {
    id: "trench",
    name: "Wool Trench Coat",
    textile: "100% Cashmere-Wool",
    colorName: "Espresso Taupe",
    colorHex: "#292A2E",
    secondaryColors: [
      { name: "Midnight Charcoal", hex: "#2A2B2E" }
    ],
    moreDetails: "Premium double-face cashmere-wool blend, double-breasted storm flap details, and removable waist tie.",
    occasion: "evening",
    image: "/assets/outerwear_category.png",
    verified: true,
    long: true,
    hasAIService: true,
    categories: ["outerwear"]
  },
  {
    id: "bomber",
    name: "Shearling Bomber",
    textile: "Genuine Suede & Merino Sheepskin",
    colorName: "Camel Brown",
    colorHex: "#8B5A2B",
    secondaryColors: [],
    moreDetails: "Rugged suede exterior lined with luxurious, thick merino sheepskin. Finished with heavy-duty brass zippers.",
    occasion: "casual",
    image: "/assets/shearling_jacket.png",
    verified: false,
    long: false,
    hasAIService: false,
    categories: ["outerwear"]
  },
  {
    id: "derby",
    name: "Minimalist Derby",
    textile: "Full-Grain Calfskin Leather",
    colorName: "Polished Black",
    colorHex: "#0D0E12",
    secondaryColors: [],
    moreDetails: "Blake-stitched construction, refined low profile dress silhouette with subtle blind eyelets.",
    occasion: "event",
    image: "/assets/shoes_category.png",
    verified: true,
    long: true,
    hasAIService: true,
    categories: ["footwear"]
  },
  {
    id: "sneakers",
    name: "Essential Sneakers",
    textile: "Nappa Leather",
    colorName: "Minimal White",
    colorHex: "#E2E2E2",
    secondaryColors: [
      { name: "Alabaster White", hex: "#F5F5F7" }
    ],
    moreDetails: "Buttery soft Italian nappa leather low-tops with hand-stitched Margom rubber soles.",
    occasion: "casual",
    image: "/assets/sneakers_recent.png",
    verified: false,
    long: false,
    hasAIService: false,
    categories: ["footwear"]
  },
  {
    id: "boots",
    name: "Chelsea Boots",
    textile: "Premium Waxed Calfskin",
    colorName: "Matte Black",
    colorHex: "#1A1B1F",
    secondaryColors: [],
    moreDetails: "Durable Goodyear welted soles, flexible side elastic gores, and waxed pull-tabs.",
    occasion: "casual",
    image: "/assets/chelsea_boots_gap.png",
    verified: true,
    long: false,
    hasAIService: true,
    categories: ["footwear"]
  },
  {
    id: "watch",
    name: "Gold Timepiece",
    textile: "18K Gold Plated",
    colorName: "Champagne Gold",
    colorHex: "#D4AF37",
    secondaryColors: [
      { name: "Obsidian Black", hex: "#121317" }
    ],
    moreDetails: "Brushed 18k yellow gold analog case with a black hand-stitched alligator leather strap.",
    occasion: "event",
    image: "/assets/gold_watch.png",
    verified: true,
    long: true,
    hasAIService: true,
    categories: ["accessories"]
  },
  {
    id: "flatlay_acc",
    name: "Atelier Flatlay",
    textile: "Curated Set",
    colorName: "Vogue Palette",
    colorHex: "#adc6ff",
    secondaryColors: [
      { name: "Alabaster White", hex: "#F5F5F7" }
    ],
    moreDetails: "Curated styling elements combining sunglasses, cologne, and silver ring detailing.",
    occasion: "evening",
    image: "/assets/curation_collage_feature.png",
    verified: false,
    long: false,
    hasAIService: false,
    categories: ["accessories"]
  },
];

const DEFAULT_CATEGORIES = [
  {
    id: "tops",
    name: "Tops",
    subtitle: "Essentials",
    status: "Sync Complete",
    image: "/assets/tops_category.png",
    path: "/app/inventory/tops",
  },
  {
    id: "bottoms",
    name: "Bottoms",
    subtitle: "Structured",
    status: "12 Available",
    image: "/assets/bottoms_category.png",
    path: "/app/inventory/bottoms",
  },
  {
    id: "outerwear",
    name: "Outerwear",
    subtitle: "Layering",
    status: "Season Ready",
    image: "/assets/outerwear_category.png",
    path: "/app/inventory/outerwear",
  },
  {
    id: "footwear",
    name: "Shoes",
    subtitle: "Footwear",
    status: "Verified",
    image: "/assets/shoes_category.png",
    path: "/app/inventory/footwear",
  },
  {
    id: "accessories",
    name: "Accessories",
    subtitle: "Details",
    status: "Scanning...",
    image: "/assets/curation_collage_feature.png",
    path: "/app/inventory/accessories",
  },
];

const ITEMS_KEY = "vogue_wardrobe_items_flat";
const CATEGORIES_KEY = "vogue_wardrobe_categories";

export const getWardrobeItems = () => {
  try {
    const data = localStorage.getItem(ITEMS_KEY);
    if (!data) {
      localStorage.setItem(ITEMS_KEY, JSON.stringify(DEFAULT_ITEMS));
      return DEFAULT_ITEMS;
    }
    const parsed = JSON.parse(data);
    return parsed;
  } catch (error) {
    console.error("Error accessing flat localStorage items list:", error);
    return DEFAULT_ITEMS;
  }
};

export const saveWardrobeItems = (items) => {
  try {
    localStorage.setItem(ITEMS_KEY, JSON.stringify(items));
  } catch (error) {
    console.error("Error saving flat items list:", error);
  }
};

export const getCategories = () => {
  try {
    const data = localStorage.getItem(CATEGORIES_KEY);
    let categoriesList = DEFAULT_CATEGORIES;
    if (data) {
      categoriesList = JSON.parse(data);
    } else {
      localStorage.setItem(CATEGORIES_KEY, JSON.stringify(DEFAULT_CATEGORIES));
    }

    // Dynamic count calculation from the flat items list
    const items = getWardrobeItems();
    return categoriesList.map((cat) => {
      const catalogKey = cat.id === "shoes" ? "footwear" : cat.id;
      const count = items.filter((item) => (item.categories || []).includes(catalogKey)).length;
      return {
        ...cat,
        count
      };
    });
  } catch (error) {
    console.error("Error loading categories:", error);
    return DEFAULT_CATEGORIES;
  }
};

export const addCategory = (newCat) => {
  try {
    const categoriesList = JSON.parse(localStorage.getItem(CATEGORIES_KEY) || JSON.stringify(DEFAULT_CATEGORIES));
    if (categoriesList.some((c) => c.id === newCat.id)) {
      return false;
    }
    categoriesList.push(newCat);
    localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categoriesList));
    return true;
  } catch (error) {
    console.error("Error adding category:", error);
    return false;
  }
};

export const getCategory = (categoryId) => {
  const items = getWardrobeItems();
  const key = categoryId === "shoes" ? "footwear" : categoryId;
  const filtered = items.filter((item) => (item.categories || []).includes(key));
  
  const categoryMeta = getCategories().find((c) => c.id === categoryId) || {
    name: categoryId.charAt(0).toUpperCase() + categoryId.slice(1),
    subtitle: "Digital Archive"
  };

  return {
    title: categoryMeta.name,
    description: `${categoryMeta.subtitle} Collection`,
    items: filtered
  };
};

export const getItem = (categoryId, itemId) => {
  const items = getWardrobeItems();
  // We can search directly across the flat list by ID!
  return items.find((item) => item.id === itemId) || null;
};

export const updateItem = (categoryId, itemId, updatedFields) => {
  const items = getWardrobeItems();
  const itemIndex = items.findIndex((item) => item.id === itemId);
  if (itemIndex === -1) return false;

  items[itemIndex] = {
    ...items[itemIndex],
    ...updatedFields
  };

  saveWardrobeItems(items);
  return true;
};

export const deleteItem = (categoryId, itemId) => {
  const items = getWardrobeItems();
  const filtered = items.filter((item) => item.id !== itemId);
  if (filtered.length === items.length) return false;

  saveWardrobeItems(filtered);
  return true;
};

export const resetWardrobe = () => {
  localStorage.setItem(ITEMS_KEY, JSON.stringify(DEFAULT_ITEMS));
  localStorage.setItem(CATEGORIES_KEY, JSON.stringify(DEFAULT_CATEGORIES));
  return DEFAULT_ITEMS;
};

// ── BACKEND API INTEGRATIONS (WITH RESILIENT LOCALSTORAGE FALLBACKS) ───────────

const API_BASE = "http://localhost:8000/api/wardrobe";

export const formatImageUrl = (url) => {
  if (!url) return "/assets/curation_collage_feature.png";
  if (url.startsWith("/v1/media/") || url.startsWith("/api/")) {
    return `http://localhost:8000${url}`;
  }
  return url;
};

export const apiListCategories = async (searchQuery = "") => {
  try {
    const url = `${API_BASE}/categories${searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Backend responded with error code " + res.status);
    const data = await res.json();
    
    // Auto-map backward compatibility path slugs
    return data.map(cat => ({
      ...cat,
      image: formatImageUrl(cat.image),
      path: cat.path || `/app/inventory/${cat.id}`
    }));
  } catch (err) {
    console.warn("Backend categories API unavailable, using localStorage fallback:", err);
    const localCats = getCategories();
    if (!searchQuery) return localCats;
    return localCats.filter(cat => 
      cat.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      cat.subtitle.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }
};

export const apiCreateCategory = async (payload) => {
  try {
    const res = await fetch(`${API_BASE}/categories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error creating category");
    }
    const data = await res.json();
    return {
      ...data,
      image: formatImageUrl(data.image),
      path: data.path || `/app/inventory/${data.id}`
    };
  } catch (err) {
    console.warn("Backend categories POST unavailable, saving to localStorage fallback:", err);
    const newCatId = payload.name.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-");
    const newCat = {
      id: newCatId,
      name: payload.name,
      subtitle: payload.subtitle || "",
      image: payload.image || "/assets/curation_collage_feature.png",
      status: "active",
      path: `/app/inventory/${newCatId}`
    };
    const success = addCategory(newCat);
    if (!success) throw new Error("Category already exists");
    return { ...newCat, count: 0 };
  }
};

export const apiGetCategory = async (categoryId) => {
  try {
    const res = await fetch(`${API_BASE}/categories/${categoryId}`);
    if (!res.ok) throw new Error("Category metadata not found on backend");
    const catMeta = await res.json();

    // Query matching items in this category from backend items list
    const itemsRes = await fetch(`${API_BASE}/items?categoryId=${categoryId}&limit=100`);
    let items = [];
    if (itemsRes.ok) {
      const itemsData = await itemsRes.json();
      items = (itemsData.data || []).map(item => ({
        ...item,
        image: formatImageUrl(item.image)
      }));
    }
    
    return {
      title: catMeta.name,
      description: `${catMeta.subtitle || "Digital Archive"} Collection`,
      items: items,
      rawMeta: {
        ...catMeta,
        image: formatImageUrl(catMeta.image)
      }
    };
  } catch (err) {
    console.warn(`Backend category fetch failed for ${categoryId}, using localStorage:`, err);
    return getCategory(categoryId);
  }
};

export const apiUpdateCategory = async (categoryId, payload) => {
  try {
    const res = await fetch(`${API_BASE}/categories/${categoryId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error updating category");
    }
    const data = await res.json();
    return {
      ...data,
      image: formatImageUrl(data.image),
      path: data.path || `/app/inventory/${data.id}`
    };
  } catch (err) {
    console.warn(`Backend category PUT failed for ${categoryId}, updating localStorage:`, err);
    const localCategories = JSON.parse(localStorage.getItem(CATEGORIES_KEY) || "[]");
    const index = localCategories.findIndex(c => c.id === categoryId);
    if (index !== -1) {
      localCategories[index] = { ...localCategories[index], ...payload };
      localStorage.setItem(CATEGORIES_KEY, JSON.stringify(localCategories));
      return { 
        ...localCategories[index], 
        count: 0,
        path: `/app/inventory/${categoryId}`
      };
    }
    throw new Error("Category not found in localStorage");
  }
};

export const apiDeleteCategory = async (categoryId, cleanupMode = "keep_orphans") => {
  try {
    const res = await fetch(`${API_BASE}/categories/${categoryId}?cleanup=${cleanupMode}`, {
      method: "DELETE"
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error deleting category");
    }
    return true;
  } catch (err) {
    console.warn(`Backend category DELETE failed for ${categoryId}, deleting from localStorage:`, err);
    const localCategories = JSON.parse(localStorage.getItem(CATEGORIES_KEY) || "[]");
    const filtered = localCategories.filter(c => c.id !== categoryId);
    localStorage.setItem(CATEGORIES_KEY, JSON.stringify(filtered));
    return true;
  }
};

// ── WARDROBE ITEMS API INTEGRATIONS (WITH RESILIENT LOCALSTORAGE FALLBACKS) ───

export const apiListItems = async (params = {}) => {
  try {
    const query = new URLSearchParams();
    if (params.categoryId) query.append("categoryId", params.categoryId);
    if (params.search) query.append("search", params.search);
    if (params.occasion && params.occasion !== "all") query.append("occasion", params.occasion);
    if (params.verified !== undefined && params.verified !== null) query.append("verified", params.verified);
    if (params.hasAIService !== undefined && params.hasAIService !== null) query.append("hasAIService", params.hasAIService);
    if (params.sortBy) query.append("sortBy", params.sortBy);
    if (params.sortOrder) query.append("sortOrder", params.sortOrder);
    if (params.page) query.append("page", params.page);
    if (params.limit) query.append("limit", params.limit);

    const res = await fetch(`${API_BASE}/items?${query.toString()}`);
    if (!res.ok) throw new Error("Backend responded with error code " + res.status);
    const data = await res.json();
    return {
      ...data,
      data: (data.data || []).map(item => ({
        ...item,
        image: formatImageUrl(item.image)
      }))
    };
  } catch (err) {
    console.warn("Backend list items API unavailable, using localStorage fallback:", err);
    const allItems = getWardrobeItems();
    let filtered = allItems;
    if (params.categoryId) {
      filtered = filtered.filter(item => (item.categories || []).includes(params.categoryId));
    }
    if (params.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(item => 
        (item.name || "").toLowerCase().includes(q) || 
        (item.textile || "").toLowerCase().includes(q)
      );
    }
    if (params.occasion && params.occasion !== "all") {
      filtered = filtered.filter(item => (item.occasion || "").toLowerCase() === params.occasion.toLowerCase());
    }
    if (params.verified !== undefined && params.verified !== null) {
      filtered = filtered.filter(item => !!item.verified === !!params.verified);
    }
    if (params.hasAIService !== undefined && params.hasAIService !== null) {
      filtered = filtered.filter(item => !!item.hasAIService === !!params.hasAIService);
    }
    
    // Sort
    const sortBy = params.sortBy || "created_at";
    const sortOrder = params.sortOrder || "desc";
    filtered.sort((a, b) => {
      let comparison = 0;
      if (sortBy === "name") {
        comparison = (a.name || "").localeCompare(b.name || "");
      } else {
        comparison = (a.id || "").localeCompare(b.id || "");
      }
      return sortOrder === "asc" ? comparison : -comparison;
    });

    // Paginate
    const page = params.page || 1;
    const limit = params.limit || 10;
    const totalCount = filtered.length;
    const totalPages = Math.ceil(totalCount / limit);
    const paginated = filtered.slice((page - 1) * limit, page * limit);

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

export const apiGetItem = async (itemId) => {
  try {
    const res = await fetch(`${API_BASE}/items/${itemId}`);
    if (!res.ok) throw new Error("Item details not found on backend");
    const data = await res.json();
    return {
      ...data,
      image: formatImageUrl(data.image)
    };
  } catch (err) {
    console.warn(`Backend fetch failed for item ${itemId}, using localStorage:`, err);
    const items = getWardrobeItems();
    const found = items.find(item => item.id === itemId);
    if (!found) throw new Error("Item not found");

    // OFFLINE HISTORY LOGGER: Append item view to history log
    try {
      const HISTORY_KEY = "vogue_wardrobe_history_logs";
      let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
      // Remove any existing log for this same item to move it to top
      history = history.filter(h => h.item.id !== itemId);
      history.unshift({
        id: "hist-local-" + Math.random().toString(36).substr(2, 9),
        item: found,
        viewedAt: new Date().toISOString(),
        relativeTimeLabel: "Just now"
      });
      // Limit local history size to 30 elements
      if (history.length > 30) history = history.slice(0, 30);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) {
      console.error("Failed to append offline history log:", e);
    }

    return found;
  }
};

export const apiCreateItem = async (payload) => {
  try {
    const res = await fetch(`${API_BASE}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error creating wardrobe item");
    }
    const data = await res.json();
    return {
      ...data,
      image: formatImageUrl(data.image)
    };
  } catch (err) {
    console.warn("Backend items POST unavailable, saving to localStorage fallback:", err);
    const newId = Math.random().toString(36).substr(2, 9);
    const newItem = {
      id: newId,
      ...payload,
      verified: !!payload.verified,
      long: !!payload.long,
      hasAIService: !!payload.hasAIService
    };
    const allItems = getWardrobeItems();
    allItems.push(newItem);
    saveWardrobeItems(allItems);
    return newItem;
  }
};

export const apiUpdateItem = async (itemId, payload) => {
  try {
    const res = await fetch(`${API_BASE}/items/${itemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error updating item details");
    }
    const data = await res.json();
    return {
      ...data,
      image: formatImageUrl(data.image)
    };
  } catch (err) {
    console.warn(`Backend item PUT failed for ${itemId}, updating localStorage:`, err);
    const allItems = getWardrobeItems();
    const idx = allItems.findIndex(item => item.id === itemId);
    if (idx !== -1) {
      allItems[idx] = { ...allItems[idx], ...payload };
      saveWardrobeItems(allItems);
      return allItems[idx];
    }
    throw new Error("Item not found in localStorage");
  }
};

export const apiDeleteItem = async (itemId) => {
  try {
    const res = await fetch(`${API_BASE}/items/${itemId}`, {
      method: "DELETE"
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error deleting wardrobe item");
    }
    return true;
  } catch (err) {
    console.warn(`Backend item DELETE failed for ${itemId}, deleting from localStorage:`, err);
    const allItems = getWardrobeItems();
    const filtered = allItems.filter(item => item.id !== itemId);
    saveWardrobeItems(filtered);
    return true;
  }
};

export const apiGetWardrobeStats = async () => {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error("Backend stats endpoint returned error code " + res.status);
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Backend stats API unavailable, calculating from localStorage fallback:", err);
    const items = getWardrobeItems();
    const totalPieces = items.length;
    const verifiedPieces = items.filter(item => item.verified).length;
    const syncPercentage = totalPieces > 0 ? Math.round((verifiedPieces / totalPieces) * 1000) / 10 : 0.0;
    
    // Simulate outfits count from local storage
    const outfitsData = localStorage.getItem("vogue_outfits_list");
    const outfitsCount = outfitsData ? JSON.parse(outfitsData).length : 5; // Default stubs
    
    return {
      syncPercentage,
      totalPieces,
      outfitsCount
    };
  }
};

export const apiListHistory = async (page = 1, limit = 10) => {
  try {
    const res = await fetch(`${API_BASE}/history?page=${page}&limit=${limit}`);
    if (!res.ok) throw new Error("Backend history endpoint returned error code " + res.status);
    const data = await res.json();
    return {
      ...data,
      data: (data.data || []).map(log => ({
        ...log,
        item: log.item ? { ...log.item, image: formatImageUrl(log.item.image) } : null
      }))
    };
  } catch (err) {
    console.warn("Backend history API unavailable, using localStorage fallback:", err);
    const HISTORY_KEY = "vogue_wardrobe_history_logs";
    let history = [];
    try {
      const stored = localStorage.getItem(HISTORY_KEY);
      if (stored) {
        history = JSON.parse(stored);
      } else {
        const items = getWardrobeItems();
        history = [
          {
            id: "hist-1",
            item: items.find(i => i.id === "blouse") || items[1] || {},
            viewedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            relativeTimeLabel: "2 hours ago"
          },
          {
            id: "hist-2",
            item: items.find(i => i.id === "sneakers") || items[2] || {},
            viewedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            relativeTimeLabel: "Yesterday"
          }
        ];
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
      }
    } catch (e) {
      console.error("Error reading fallback history logs:", e);
    }
    
    const totalCount = history.length;
    const totalPages = Math.ceil(totalCount / limit);
    const paginated = history.slice((page - 1) * limit, page * limit);
    
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

export const apiScanImage = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append("image", imageFile);
    
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Error scanning garment image");
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Backend scan image endpoint failed, using local classifier fallback:", err);
    
    const filename = imageFile.name ? imageFile.name.toLowerCase() : "";
    let colorName = "Midnight Charcoal";
    let colorHex = "#2A2B2E";
    let textile = "100% Cotton knit";
    let category = "tops";
    let subcategory = "knitwear";
    let confidence = 0.92;
    
    if (filename.includes("pant") || filename.includes("jean") || filename.includes("trouser")) {
      colorName = "Stone Gray";
      colorHex = "#8E9192";
      textile = "Japanese Selvedge rigid denim";
      category = "bottoms";
      subcategory = "denim";
      confidence = 0.89;
    } else if (filename.includes("shoe") || filename.includes("sneaker") || filename.includes("boot")) {
      colorName = "Polished Black";
      colorHex = "#0D0E12";
      textile = "Calfskin leather";
      category = "footwear";
      subcategory = "derby";
      confidence = 0.95;
    } else if (filename.includes("coat") || filename.includes("jacket") || filename.includes("trench")) {
      colorName = "Espresso Taupe";
      colorHex = "#292A2E";
      textile = "Cashmere wool blend";
      category = "outerwear";
      subcategory = "coat";
      confidence = 0.91;
    } else if (filename.includes("watch") || filename.includes("belt") || filename.includes("bag")) {
      colorName = "Champagne Gold";
      colorHex = "#D4AF37";
      textile = "18k gold plated";
      category = "accessories";
      subcategory = "timepiece";
      confidence = 0.88;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2500));
    
    return {
      colorName,
      colorHex,
      textile,
      category,
      subcategory,
      confidence,
      tempFileKey: "/assets/curation_collage_feature.png"
    };
  }
};


