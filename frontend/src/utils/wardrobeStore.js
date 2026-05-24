// Quiet Luxury Wardrobe Store - Vogue.AI
// Handles persistence in localStorage to make the application scalable and interactive.

const DEFAULT_CATALOG = {
  tops: {
    title: "Tops",
    description: "Editorial Pieces",
    items: [
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
      },
    ],
  },
};

const STORAGE_KEY = "vogue_wardrobe_catalog";

export const getWardrobe = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_CATALOG));
      return DEFAULT_CATALOG;
    }
    const parsed = JSON.parse(data);
    // Migration: make sure secondaryColors and moreDetails exist for all items
    let migrated = false;
    Object.keys(parsed).forEach((catKey) => {
      parsed[catKey].items.forEach((item) => {
        if (item.secondaryColors === undefined) {
          item.secondaryColors = [];
          migrated = true;
        }
        if (item.moreDetails === undefined) {
          item.moreDetails = "";
          migrated = true;
        }
      });
    });
    if (migrated) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
    }
    return parsed;
  } catch (error) {
    console.error("Error accessing localStorage wardrobe catalog:", error);
    return DEFAULT_CATALOG;
  }
};

export const saveWardrobe = (catalog) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(catalog));
  } catch (error) {
    console.error("Error saving wardrobe to localStorage:", error);
  }
};

export const getCategory = (categoryId) => {
  const wardrobe = getWardrobe();
  const key = categoryId === "shoes" ? "footwear" : categoryId;
  return wardrobe[key] || { title: categoryId, description: "Digital Archive", items: [] };
};

export const getItem = (categoryId, itemId) => {
  const cat = getCategory(categoryId);
  return cat.items.find((item) => item.id === itemId) || null;
};

export const updateItem = (categoryId, itemId, updatedFields) => {
  const wardrobe = getWardrobe();
  const key = categoryId === "shoes" ? "footwear" : categoryId;
  
  if (!wardrobe[key]) return false;
  
  const itemIndex = wardrobe[key].items.findIndex((item) => item.id === itemId);
  if (itemIndex === -1) return false;

  const currentItem = wardrobe[key].items[itemIndex];
  const nextItem = { ...currentItem, ...updatedFields };

  const newCategoryKey = updatedFields.categoryId || key;
  const targetCategoryKey = newCategoryKey === "shoes" ? "footwear" : newCategoryKey;

  if (targetCategoryKey !== key && wardrobe[targetCategoryKey]) {
    wardrobe[key].items.splice(itemIndex, 1);
    delete nextItem.categoryId;
    wardrobe[targetCategoryKey].items.push(nextItem);
  } else {
    delete nextItem.categoryId;
    wardrobe[key].items[itemIndex] = nextItem;
  }

  saveWardrobe(wardrobe);
  return true;
};

export const deleteItem = (categoryId, itemId) => {
  const wardrobe = getWardrobe();
  const key = categoryId === "shoes" ? "footwear" : categoryId;
  
  if (!wardrobe[key]) return false;
  
  const itemIndex = wardrobe[key].items.findIndex((item) => item.id === itemId);
  if (itemIndex === -1) return false;

  wardrobe[key].items.splice(itemIndex, 1);
  saveWardrobe(wardrobe);
  return true;
};

export const resetWardrobe = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_CATALOG));
  return DEFAULT_CATALOG;
};
