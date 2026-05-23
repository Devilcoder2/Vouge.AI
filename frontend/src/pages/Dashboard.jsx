import React from "react";
import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const Dashboard = () => {
  return (
    <Layout>
      {/* Curated Look Banner */}
      <section className="relative w-full h-[400px] md:h-[500px] rounded-xl overflow-hidden group mb-8 shadow-xl">
        <img
          alt="Today's Curated Look"
          className="absolute inset-0 w-full h-full object-cover opacity-80 transition-transform duration-700 group-hover:scale-105"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuDW_zA31AiVcgHZnRclvMFUoiC-eCgqsBHJfHHxFO4RPtWBEtJdEXiBtkgLMQJVHBERd1sQxL5cTYIvP6d1sQPAXq9HDake4LwiV_RxrZTCS7Sg9wGRM_uacSz1m-VugTAKGZh-iD76PeqbOe57GIOTMH_8BY9hqC_QQcX0kym5yI7qAOHJXhQz0AsEEc-IiOxsyU_m5oZa2AtmiFBZjorArU5uh06MPSfjduTZfaGEcWVEkr0hGqte2y9whHl5zYIQEGe4W065eivM"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent"></div>
        <div className="absolute inset-0 p-6 flex flex-col justify-end">
          <div className="glass-panel p-6 rounded-lg max-w-lg ai-glow">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-tertiary">cloud</span>
              <span className="text-xs text-tertiary uppercase tracking-widest font-medium">
                55°F • Chilly & Chic
              </span>
            </div>
            <h2 className="font-display text-3xl mb-4 tracking-wide leading-tight">
              Today's Curated Look
            </h2>
            <p className="text-on-surface-variant mb-6 text-sm leading-relaxed">
              A masterclass in transitional layering. We've selected your charcoal wool
              trench paired with the minimalist white knit.
            </p>
            <Link
              to="/app/recommendations"
              className="bg-on-surface text-surface px-6 py-3 rounded uppercase tracking-widest text-xs font-semibold hover:bg-tertiary hover:text-on-tertiary-fixed transition-colors duration-300 inline-block text-center"
            >
              View Details
            </Link>
          </div>
        </div>
      </section>

      {/* Wardrobe Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="glass-panel p-6 rounded-lg text-center shadow-lg transition-all hover:scale-[1.01]">
          <span className="material-symbols-outlined text-3xl opacity-50 mb-2">
            inventory_2
          </span>
          <h3 className="font-display text-4xl mb-1 font-semibold">84%</h3>
          <p className="text-[10px] text-on-surface-variant uppercase tracking-widest font-medium">
            Digitized
          </p>
        </div>
        <Link
          to="/app/analysis"
          className="glass-panel p-6 rounded-lg text-center hover:border-tertiary/50 transition-all duration-300 shadow-lg hover:scale-[1.01]"
        >
          <span className="material-symbols-outlined text-3xl opacity-50 mb-2 transition-colors duration-300 group-hover:text-tertiary">
            insights
          </span>
          <h3 className="font-display text-4xl mb-1 font-semibold">2</h3>
          <p className="text-[10px] text-on-surface-variant uppercase tracking-widest font-medium">
            Wardrobe Gaps
          </p>
        </Link>
      </div>
    </Layout>
  );
};

export default Dashboard;
