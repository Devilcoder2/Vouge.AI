// Quiet Luxury Outfit Curation Store - Vogue.AI
// Manages AI recommended outfits, VOGUE scores, reasoning, and linked wardrobe items.

const OUTFITS = [
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
  },
  {
    id: "urban-transitional",
    name: "Urban Transitional",
    heroImage: "/assets/shearling_jacket.png",
    subtitle: "Suede Heritage Lining",
    weather: "52°F & WINDY",
    occasion: "BUSINESS CASUAL",
    description: "Structured camel suede shearling aviator jacket grounds the outfit warp with a classic heritage weight and crisp white poplin.",
    vogueScore: 92,
    metrics: {
      colorHarmony: 90,
      styleAlignment: 94,
      occasionContext: 90,
      formalityBalance: 85,
      seasonAppropriateness: 100
    },
    reasoning: [
      "Structured camel suede shearling aviator jacket grounds the outfit with classic heritage layering weight.",
      "Clean white cotton poplin shirt provides a sharp corporate contrast at the neckline.",
      "Refined matte black Chelsea boots complete the masculine, high-end transitional silhouette."
    ],
    items: [
      {
        id: "bomber",
        categoryId: "outerwear",
        categoryLabel: "Outerwear",
        name: "Shearling Bomber",
        textile: "Camel Brown | Suede & Merino Sheepskin",
        image: "/assets/shearling_jacket.png"
      },
      {
        id: "shirt",
        categoryId: "tops",
        categoryLabel: "Tops",
        name: "Essential White Shirt",
        textile: "Alabaster White | 100% Poplin Cotton",
        image: "/assets/shirt_item.png"
      },
      {
        id: "trouser",
        categoryId: "bottoms",
        categoryLabel: "Bottoms",
        name: "Pleated Trousers",
        textile: "Charcoal Gray | 100% Merino Wool",
        image: "/assets/pleated_trousers.png"
      },
      {
        id: "boots",
        categoryId: "footwear",
        categoryLabel: "Footwear",
        name: "Chelsea Boots",
        textile: "Matte Black | Premium Waxed Calfskin",
        image: "/assets/chelsea_boots_gap.png"
      }
    ]
  }
];

export const getOutfits = () => OUTFITS;

export const getOutfit = (outfitId) => {
  return OUTFITS.find((outfit) => outfit.id === outfitId) || null;
};
