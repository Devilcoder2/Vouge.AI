# Fashion Platform Core Product Logic & Business Rules

This document defines the deterministic rules, taxonomies, and scoring calculations for the AI Fashion Assistant Platform. These rules govern wardrobe organization, outfit generation constraints, and candidate recommendation scoring.

---

## 1. Wardrobe & Taxonomy Logic

### 1.1 Category Hierarchy
Clothing items are classified into a two-tier hierarchical tree. Every item must map to exactly one `Category` and one `Subcategory`.

```
├── Tops
│   ├── T-Shirts & Tanks
│   ├── Casual Shirts (Button-downs, Flannels)
│   ├── Dress Shirts
│   ├── Polos
│   ├── Sweaters & Cardigans
│   └── Hoodies & Sweatshirts
├── Bottoms
│   ├── Jeans
│   ├── Chinos & Trousers
│   ├── Dress Pants
│   ├── Cargo Pants
│   ├── Shorts
│   └── Skirts
├── Outerwear
│   ├── Blazers & Suit Jackets
│   ├── Light Jackets (Denim, Bomber, Windbreaker)
│   ├── Leather Jackets
│   └── Heavy Coats (Overcoats, Parkas, Puffer Jackets)
├── Dresses (Full-Body)
│   ├── Casual Dresses
│   ├── Formal & Evening Dresses
│   └── Jumpsuits & Rompers
├── Shoes
│   ├── Sneakers (Casual & Athletic)
│   ├── Dress Shoes (Oxfords, Derbies)
│   ├── Boots (Chelsea, Combat, Ankle)
│   ├── Loafers & Slip-ons
│   └── Sandals & Slides
└── Accessories
    ├── Bags & Backpacks
    ├── Hats & Caps
    ├── Belts
    ├── Scarves & Gloves
    └── Eyewear
```

### 1.2 Wardrobe Constraints & Limits
*   **Shoe Constraint:** A valid outfit contains **exactly one** pair of shoes. Multi-shoe outfits are out of scope.
*   **Item Uniqueness:** An item cannot be duplicated in a single outfit (e.g., you cannot wear two identical belts or two pairs of shoes).
*   **Dresses vs. Separates:** An outfit can contain either **one Dress (Full-Body)** OR **one Top + one Bottom**, but not both.

### 1.3 Fixed Seasons
Seasons determine the primary seasonal suitability of items:
*   **Spring:** Temperature range $15^\circ\text{C}$ to $22^\circ\text{C}$. Mid-weight fabrics.
*   **Summer:** Temperature range $>22^\circ\text{C}$. Lightweight, breathable fabrics (linen, thin cotton).
*   **Autumn:** Temperature range $10^\circ\text{C}$ to $18^\circ\text{C}$. Earth tones, layering-friendly fabrics (flannel, corduroy).
*   **Winter:** Temperature range $<10^\circ\text{C}$. Heavyweight fabrics (wool, cashmere, down).
*   **Transitional Tags:** Items can be flagged for multiple seasons (e.g., a cotton cardigan as `[Spring, Autumn, Winter]`).

### 1.4 Gender-Neutral Logic
*   **Aesthetic-First Classifications:** Clothing items are categorized by fit profiles, drapes, and structural measurements rather than binary genders.
*   **Fit Profiles:**
    *   `Slim Fit`: Contoured to body curves.
    *   `Standard Fit`: Classic proportion spacing.
    *   `Oversized / Relaxed Fit`: Dropped shoulders, extended hem lengths.
*   **Stylist Mapping:** The Recommender service queries style similarity using CLIP embeddings which naturally capture silhouettes, bypassing binary gender assumptions unless the user explicitly requests strict gender-specific filtering.

### 1.5 Multi-Style Classification
An item can be tagged with up to three style categories to allow high-versatility pairings:
*   `Minimalist`: Clean lines, neutral/solid colors, no loud logos.
*   `Streetwear`: Graphic tees, hoodies, loose fits, sneakers, cargo pants.
*   `Classic / Preppy`: Oxford shirts, blazers, chinos, loafers, knitwear.
*   `Formal / Business`: Suits, dress trousers, dress shirts, oxfords.
*   `Athleisure`: Joggers, sweatpants, tech hoodies, performance sneakers.
*   `Bohemian`: Flowing cuts, floral/paisley patterns, earth tones, sandals.
*   `Grunge / Rocker`: Distressed denim, leather jackets, combat boots, band tees.

---

## 2. Outfit Structure & Layering Logic

An outfit is a structured collection of items that must satisfy structural, thematic, and physical constraints.

### 2.1 Required & Optional Pieces
The system supports two core structural formats:

#### Format A: Separates
*   **Required:** 
    *   $1 \times$ Top
    *   $1 \times$ Bottom
    *   $1 \times$ Shoes
*   **Optional:** 
    *   Up to $2 \times$ Outerwear (for layering)
    *   Up to $4 \times$ Accessories (Bags, Belts, Scarves, Hats, Eyewear - maximum one of each subcategory)

#### Format B: Full-Body
*   **Required:** 
    *   $1 \times$ Dress (Full-Body)
    *   $1 \times$ Shoes
*   **Optional:** 
    *   Up to $2 \times$ Outerwear
    *   Up to $4 \times$ Accessories

---

### 2.2 Layering Rules
Layering is governed by a deterministic hierarchy based on `Layer Index` values. Items must be layered sequentially.

| Layer Index | Layer Type | Permitted Subcategories | Max Count |
|---|---|---|---|
| **Layer 0** | Base Layer | T-Shirts & Tanks, Jumpsuits | 1 |
| **Layer 1** | Top Layer | Casual Shirts, Dress Shirts, Polos, Sweaters, Hoodies | 1 |
| **Layer 2** | Mid-Outerwear | Blazers, Light Jackets, Leather Jackets, Cardigans | 1 |
| **Layer 3** | Shell Outerwear | Heavy Coats, Parkas, Trench Coats | 1 |

*   **Rule 1: Ascending Sequence.** Items must be layered from lower index to higher index (e.g., Layer 0 under Layer 2, Layer 1 under Layer 3). You cannot wear a Blazer (Layer 2) under a Sweater (Layer 1).
*   **Rule 2: Visual Compatibility.** The collar of a lower layer must physically accommodate the upper layer (e.g., a hooded sweatshirt Layer 1 must sit over a flat collar Layer 0, and the hood must drape outside a Layer 2/3 coat).

---

### 2.3 Formality & Occasion Mapping
Every item has a base `formality_score` on a scale of **1 to 10**. The overall outfit formality is the **weighted average** of the core pieces (Tops, Bottoms/Dresses, Shoes), with Outerwear adjusting the score up or down.

#### Formality Scale:
*   **1–2 (Very Casual / Lounge):** Sweatpants, slides, tank tops.
*   **3–4 (Casual):** T-shirts, jeans, shorts, sneakers.
*   **5–6 (Smart Casual):** Polos, chinos, casual shirts, cardigans, loafers.
*   **7–8 (Business Casual / Semi-Formal):** Blazers, dress trousers, button-downs, oxfords, Chelsea boots.
*   **9–10 (Formal / Black Tie):** Suits, tuxedos, evening gowns, patent dress shoes.

#### Occasion Formality Bands:
The Recommender service filters candidates using occasion-specific formality ranges:

| Occasion | Allowed Formality Range | Structural Requirements |
|---|---|---|
| **Everyday Casual** | 3.0 – 5.0 | No suit pieces. Loafers/sneakers allowed. |
| **Date Night** | 5.0 – 8.0 | Min 1 "smart" element (e.g., collar, leather shoes, or blazer). |
| **Business / Work** | 6.0 – 8.5 | No shorts, slides, or graphic tees. Collars/dress pants preferred. |
| **Gym / Active** | 1.0 – 3.0 | Must use Athleisure/Tops (T-Shirts/Tanks) + Shorts/Joggers + Sneakers. |
| **Cocktail / Formal**| 8.5 – 10.0 | Full suit, formal dress, or high-end evening wear. Dress shoes only. |

---

### 2.4 Weather Compatibility
Weather profiles dictate the thermal index of outfits. Every subcategory has an insulation factor:

$$\text{Outfit Warmth Score} = \sum (\text{item\_insulation\_factor})$$

*   **Extreme Cold ($<5^\circ\text{C}$):**
    *   Required: At least one Layer 3 item (insulation $\ge 8$) + Bottoms (no shorts/skirts without tights) + closed-toe shoes (Boots/Sneakers).
*   **Cold ($5\text{--}12^\circ\text{C}$):**
    *   Required: At least one Layer 2 or Layer 3 item.
*   **Mild ($12\text{--}20^\circ\text{C}$):**
    *   Required: Standard separates. Outerwear is optional.
*   **Hot ($>20^\circ\text{C}$):**
    *   Required: Outerwear is strictly prohibited (except ultra-light base items). Shorts/Skirts preferred.
*   **Precipitation Rule (Rain/Snow):**
    *   Exclude suede, canvas, and mesh items from footwear.
    *   Prioritize synthetic, waxed, or waterproof-treated outerwear.

---

## 3. Recommendation Scoring Engine

Outfits generated by the Recommender service are scored from **0.00 to 1.00**.

$$\text{Final Score} = w_1 S_{\text{color}} + w_2 S_{\text{style}} + w_3 S_{\text{body}} + w_4 S_{\text{versatility}} + w_5 S_{\text{trend}}$$

*   Recommended weights: $w_1 = 0.30$, $w_2 = 0.25$, $w_3 = 0.15$, $w_4 = 0.20$, $w_5 = 0.10$.

### 3.1 Color Compatibility ($S_{\text{color}}$)
Calculated using pixel-extracted primary/secondary HSL (Hue, Saturation, Lightness) color values:

1.  **Neutral Balancing (Base Rule):** Pairing any vibrant color (saturation $>40\%$) with at least one neutral color (Black, White, Grey, Beige, Navy - saturation $<15\%$). Score: **1.00**.
2.  **Monochromatic:** All outfit items have hues within $15^\circ$ of each other, with saturation and lightness varying by at least $20\%$ to avoid a flat look. Score: **0.95**.
3.  **Complementary:** Two primary items have hues separated by $180^\circ \pm 15^\circ$ (e.g., blue and orange). Score: **0.90**.
4.  **Analogous:** Items utilize hues within a contiguous $60^\circ$ arc on the color wheel (e.g., red, red-orange, orange). Score: **0.85**.
5.  **Color Clash Penalty:** More than 3 distinct vibrant hues (saturation $>40\%$) in one outfit. Score: **0.20**.

---

### 3.2 Style Compatibility ($S_{\text{style}}$)
1.  **Tag Cosine Similarity:** Recommender service generates user style profiles and item style tags. A similarity matrix is computed.
2.  **Clash Rules:** Strict penalties are applied for incompatible cross-genre pairings.
    *   *Example:* `Formal/Business` bottom (Dress Pants) + `Athleisure` top (Gym Tank) $\rightarrow$ Penalty multiplier **0.10**.
    *   *Exceptions:* Intentional crossover styles (e.g., `Streetwear` hoodie + `Formal` Blazer) are supported if a user has explicitly added both styles to their profile preference tags.

---

### 3.3 Body-Shape Suitability ($S_{\text{body}}$)
Heuristics matching garments to body silhouettes to maximize flattering fits:

| Body Type | Styling Objective | Ideal Silhouettes / Fits |
|---|---|---|
| **Hourglass** | Emphasize natural waist definition | Fitted tops, high-waisted bottoms, wrap dresses, belted coats. |
| **Pear (Triangle)** | Draw attention upwards, balance hips | Structured/detailed shoulders, A-line skirts, wide-leg trousers. |
| **Inverted Triangle**| Balance broad shoulders, add volume down | V-neck tops, boyfriend/wide jeans, pleated skirts, flared trousers. |
| **Rectangle** | Create curves or structure | Belts, tiered dresses, oversized jackets paired with slim bottoms. |
| **Apple (Round)** | Elongate torso, draw attention to limbs | Flowing fabrics, empire waists, straight-leg trousers, long outerwear. |

---

### 3.4 Versatility Score ($S_{\text{versatility}}$)
Applicable primarily for Gap Analysis recommendations. When evaluating an external product (item $E$) to recommend to a user:

$$S_{\text{versatility}} = \frac{\text{Count of valid new outfits enabled by adding } E}{\text{Target standard (e.g., 10 new outfits)}} \times \text{Average outfit compatibility score}$$

*   Items that unlock high-quality combinations across multiple categories score higher (e.g., a high-versatility white sneaker vs. a low-versatility lime green suede boot).

---

### 3.5 Trend Decay Score ($S_{\text{trend}}$)
Used to rank feed cards and recommend items that align with current platform signals:

$$S_{\text{trend}} = S_{\text{base}} \times e^{-\lambda t}$$

*   Where $t$ is the age of the trend/card in days.
*   $\lambda$ is the decay constant (half-life of 14 days for style trends).
*   $S_{\text{base}}$ is calculated dynamically from aggregate user interactions (CTR, likes, saves, click-through commerce links) across the platform in the last 72 hours.
