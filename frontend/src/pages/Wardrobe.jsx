import React, { useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const Wardrobe = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const categories = [
    {
      id: "tops",
      name: "Tops",
      count: 42,
      path: "/app/inventory/tops",
      image:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuD8KmBhoPAZAsRrGYP1cfIYEK2v8unVM9JiH5gu0MOoK5qDUamfNpTIkzCTWLg69tj6_IQJWif-xMWB4qw7UZVhKrLnUQY7Dmvz1DbWq4Z_BvXPcVCm9q2haLOEupGM_m777W_VFL4MYB-a22Zh6NRVhLXjA-plW_7-WONZuDL_E4dRLKrGkoLg7RIrUvdY2GTqGNvTniSAAZUKGtx8oqmyEgexID63Ixf6bkIHrQlJvsAWHdRE447D0ftsEfNYSPdsLKE9XCZhaFKQ",
    },
    {
      id: "bottoms",
      name: "Bottoms",
      count: 28,
      path: "/app/inventory/bottoms",
      image:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuAganbnixevDuQY1Z_ETb3RopEv8SiVd3CpOnjeGK8dYMp25Bg-pY559V09IJH7Mn_d6EFMYJwDd8iCgVvRAp-A0Al68jCf3eMMqnUFxem-v4h7BxQ-yrQtdwlmFk_GVteeQv0F8ZdQSYUBXiDVoniQQF30IT9Y42WWOU6Ox1PqITUZoCd57MviLyBKyTQAnTW0NQuhih-3r1Cv5BZrkAevBnSdOMpxMv8Qh6-e_T4leVDqYva3PvX8WOtLO-o1toqfKjcs6VkS3FTW",
    },
    {
      id: "outerwear",
      name: "Outerwear",
      count: 15,
      path: "/app/inventory/outerwear",
      image:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuDW_zA31AiVcgHZnRclvMFUoiC-eCgqsBHJfHHxFO4RPtWBEtJdEXiBtkgLMQJVHBERd1sQxL5cTYIvP6d1sQPAXq9HDake4LwiV_RxrZTCS7Sg9wGRM_uacSz1m-VugTAKGZh-iD76PeqbOe57GIOTMH_8BY9hqC_QQcX0kym5yI7qAOHJXhQz0AsEEc-IiOxsyU_m5oZa2AtmiFBZjorArU5uh06MPSfjduTZfaGEcWVEkr0hGqte2y9whHl5zYIQEGe4W065eivM",
    },
    {
      id: "footwear",
      name: "Footwear",
      count: 12,
      path: "/app/inventory/footwear",
      image:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof",
    },
  ];

  const filteredCategories = categories.filter((cat) =>
    cat.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout title="Wardrobe">
      {/* Search Input Bar */}
      <div className="relative w-full glass-panel rounded-full flex items-center px-5 py-3.5 mb-8 focus-within:border-tertiary/40 transition-colors shadow-lg">
        <span className="material-symbols-outlined text-on-surface-variant mr-3 select-none">
          search
        </span>
        <input
          className="bg-transparent border-none w-full focus:outline-none focus:ring-0 text-sm text-on-surface placeholder-on-surface-variant/50"
          placeholder="Search your wardrobe..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery("")}
            className="text-on-surface-variant hover:text-on-surface transition-colors mr-1 cursor-pointer"
            aria-label="Clear search"
          >
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        )}
      </div>

      {/* Grid List */}
      {filteredCategories.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {filteredCategories.map((cat) => (
            <Link
              key={cat.id}
              to={cat.path}
              className="group relative aspect-[4/5] rounded-xl overflow-hidden glass-panel flex flex-col justify-end p-5 hover:border-tertiary/40 transition-all duration-300 shadow-lg hover:scale-[1.01]"
            >
              <img
                alt={cat.name}
                className="absolute inset-0 w-full h-full object-cover opacity-60 transition-transform duration-500 group-hover:scale-105"
                src={cat.image}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/95 via-background/20 to-transparent"></div>
              <div className="relative z-10 transition-transform duration-300 group-hover:translate-x-1">
                <span className="text-xs uppercase tracking-widest font-semibold block mb-1">
                  {cat.name}
                </span>
                <span className="text-[11px] text-on-surface-variant font-medium">
                  {cat.count} Items
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 glass-panel rounded-xl">
          <span className="material-symbols-outlined text-4xl opacity-40 mb-3 select-none">
            checkroom
          </span>
          <p className="text-sm text-on-surface-variant">
            No matching categories found in your wardrobe.
          </p>
        </div>
      )}
    </Layout>
  );
};

export default Wardrobe;
