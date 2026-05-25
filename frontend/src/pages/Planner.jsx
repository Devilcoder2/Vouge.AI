import React, { useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const Planner = () => {
  const [selectedDate, setSelectedDate] = useState("15");

  const dates = [
    { label: "TUE", day: "15" },
    { label: "WED", day: "16" },
    { label: "THU", day: "17" },
    { label: "FRI", day: "18" },
    { label: "SAT", day: "19" },
  ];

  const agendas = {
    15: {
      time: "10:00 AM • Meeting",
      title: "The Executive",
      description: "Charcoal wool trench, tailored slate slacks, and leather oxford shoes.",
      category: "Workplace Chic",
      imgColor: "bg-surface-container-highest",
      outfitId: "modern-minimalist",
    },
    16: {
      time: "7:30 PM • Dinner Gala",
      title: "Gala Noir",
      description: "Silk evening suit coupled with minimalist silver links and oxfords.",
      category: "Formal Elegance",
      imgColor: "bg-tertiary/20 border border-tertiary/30",
      outfitId: "monochrome-discipline",
    },
    17: {
      time: "2:00 PM • Coffee Date",
      title: "Autumn Breeze",
      description: "Off-white cashmere knit paired with high-rise denim and beige boots.",
      category: "Smart Casual",
      imgColor: "bg-primary/20 border border-primary/30",
      outfitId: "casual-sophisticate",
    },
    18: {
      time: "9:00 AM • Airport Travel",
      title: "Metro Transit",
      description: "Charcoal oversized hoodie, luxury track pants, and vintage trainers.",
      category: "Athleisure",
      imgColor: "bg-surface-container-high",
      outfitId: "casual-sophisticate",
    },
    19: {
      time: "1:00 PM • Gallery Tour",
      title: "Creative Canvas",
      description: "Structured utility jacket with rolled sleeves and raw-selvedge denim.",
      category: "Artistic/Alternative",
      imgColor: "bg-surface-bright",
      outfitId: "urban-transitional",
    },
  };

  const activeAgenda = agendas[selectedDate] || agendas["15"];

  return (
    <Layout title="Planner">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="font-display text-3xl mb-2 tracking-wide">Planner</h1>
          <p className="text-on-surface-variant text-sm font-medium">October 2024</p>
        </div>
      </div>

      {/* Dynamic Date Track */}
      <div className="flex space-x-4 overflow-x-auto hide-scrollbar pb-6 mb-8 border-b border-white/5">
        {dates.map((date) => {
          const isSelected = selectedDate === date.day;
          return (
            <button
              key={date.day}
              onClick={() => setSelectedDate(date.day)}
              className={`flex-shrink-0 flex flex-col items-center justify-center w-14 h-20 rounded-full transition-all duration-300 shadow-md cursor-pointer ${
                isSelected
                  ? "bg-on-surface text-surface scale-105"
                  : "border border-white/10 hover:border-white/20 text-on-surface"
              }`}
            >
              <span className={`text-[10px] mb-2 font-bold tracking-widest ${isSelected ? "opacity-90" : "text-on-surface-variant"}`}>
                {date.label}
              </span>
              <span className="font-display text-xl font-semibold">{date.day}</span>
            </button>
          );
        })}
      </div>

      {/* Dynamic Curated Agenda Item Card */}
      <div className="glass-panel p-6 rounded-xl flex flex-col sm:flex-row gap-5 items-center shadow-2xl transition-all duration-500 hover:border-tertiary/10">
        {/* Color Block Thumbnail */}
        <div className={`w-24 h-24 sm:w-28 sm:h-28 rounded-lg shrink-0 flex items-center justify-center shadow-inner ${activeAgenda.imgColor}`}>
          <span className="material-symbols-outlined text-3xl opacity-40 select-none">
            checkroom
          </span>
        </div>
        <div className="flex-1 text-center sm:text-left">
          <p className="text-[10px] text-tertiary tracking-widest uppercase font-bold mb-1">
            {activeAgenda.time}
          </p>
          <h3 className="font-display text-2xl font-semibold mb-2 text-on-surface">
            {activeAgenda.title}
          </h3>
          <p className="text-sm text-on-surface-variant leading-relaxed max-w-xl">
            {activeAgenda.description}
          </p>
          <div className="mt-4 flex flex-wrap justify-center sm:justify-start gap-4 items-center">
            <span className="text-[10px] uppercase bg-white/5 border border-white/10 px-2.5 py-1 rounded-full text-on-surface-variant font-medium">
              {activeAgenda.category}
            </span>
            <Link
              to={`/app/outfit/${activeAgenda.outfitId || "modern-minimalist"}`}
              className="text-xs text-on-surface font-semibold underline hover:text-tertiary transition-colors"
            >
              View Details
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Planner;
