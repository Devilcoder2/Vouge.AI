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

export const apiListCategories = async (searchQuery = "") => {
  try {
    const url = `${API_BASE}/categories${searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Backend responded with error code " + res.status);
    const data = await res.json();
    
    // Auto-map backward compatibility path slugs
    return data.map(cat => ({
      ...cat,
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
      items = itemsData.data;
    }
    
    return {
      title: catMeta.name,
      description: `${catMeta.subtitle || "Digital Archive"} Collection`,
      items: items,
      rawMeta: catMeta
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

