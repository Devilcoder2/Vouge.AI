import React from "react";
import Layout from "../components/layout/Layout";

export const GenericScreen = ({ title }) => {
  return (
    <Layout title={title} showBack>
      <div className="flex items-center justify-center h-full min-h-[400px] border border-dashed border-white/20 rounded-xl">
        <div className="text-center p-6">
          <span className="material-symbols-outlined text-4xl opacity-50 mb-4 animate-pulse">
            construction
          </span>
          <h2 className="font-display text-2xl tracking-wide">{title}</h2>
          <p className="text-on-surface-variant text-sm mt-2">
            Prototype stub - currently in development
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default GenericScreen;
