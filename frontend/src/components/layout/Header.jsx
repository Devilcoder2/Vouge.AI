import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

export const Header = ({ title = "VOGUE.AI", showBack = false }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => {
    if (path === "/app") {
      return location.pathname === "/app";
    }
    return location.pathname.startsWith(path);
  };

  const navLinks = [
    { label: "Home", path: "/app" },
    { label: "Wardrobe", path: "/app/wardrobe" },
    { label: "AI Stylist", path: "/app/chat" },
    { label: "Discovery", path: "/app/discover" },
    { label: "Planner", path: "/app/planner" },
  ];

  return (
    <header className="fixed top-0 left-0 w-full z-50 bg-surface/95 backdrop-blur-xl border-b border-white/5 h-16 flex items-center px-4 md:px-8 shadow-md">
      {/* Mobile-only menu icon or back button */}
      <div className="flex md:hidden items-center shrink-0 w-12">
        {showBack ? (
          <button
            onClick={() => navigate(-1)}
            className="hover:opacity-70 text-primary p-2 -ml-2 flex items-center justify-center transition-opacity cursor-pointer"
            aria-label="Go back"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
        ) : (
          <button
            className="hover:opacity-70 text-primary p-2 -ml-2 flex items-center justify-center transition-opacity cursor-pointer"
            aria-label="Menu"
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
        )}
      </div>

      {/* Desktop-only back button (only visible if showBack is true) */}
      {showBack && (
        <div className="hidden md:flex items-center shrink-0 mr-4">
          <button
            onClick={() => navigate(-1)}
            className="hover:opacity-70 text-primary p-2 flex items-center justify-center transition-opacity cursor-pointer"
            aria-label="Go back"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
        </div>
      )}

      {/* Logo container */}
      <div className="flex-1 md:flex-initial flex justify-center md:justify-start items-center">
        <Link
          to="/app"
          className="font-display text-xl md:text-2xl tracking-[0.2em] uppercase font-semibold text-on-surface hover:opacity-90 transition-opacity"
        >
          {title}
        </Link>
      </div>

      {/* Desktop navigation menu */}
      <nav className="hidden md:flex flex-1 justify-center items-center gap-8">
        {navLinks.map((link) => {
          const active = isActive(link.path);
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`text-[10px] uppercase tracking-widest transition-all duration-300 relative py-1.5 ${
                active
                  ? "text-primary font-bold"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              {link.label}
              {active && (
                <span className="absolute bottom-0 left-0 w-full h-[2px] bg-primary rounded-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Right controls (shopping bag & avatar) */}
      <div className="flex items-center gap-4 shrink-0 justify-end w-12 md:w-auto">
        <button
          className="hover:opacity-70 text-primary p-2 flex items-center justify-center transition-all cursor-pointer"
          aria-label="Shopping Cart"
        >
          <span className="material-symbols-outlined text-2xl">shopping_bag</span>
        </button>

        {/* Desktop Profile avatar image */}
        <Link
          to="/app/profile"
          className="hidden md:block w-9 h-9 rounded-full overflow-hidden border border-white/20 hover:border-white/40 transition-colors"
        >
          <img
            alt="User Avatar"
            className="w-full h-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuCUhrbSCCyvL4gMnA4wJKdCIy8rVXkUi-RbzyXY0huiYdfDG1hbrZTi-unXTQtHZr7f0ylpE97bhRPNcOAuBoGKXLZ9h6MkdQTX2Ta77wOdUoQSSmQB-gtnME4J5WbRKBfLHRHGbjQ9nvppXanviB6KFDGHhH3UASuuDBy4oIWLee_5z-H844_4Mt1y2nDji5MV2TT9xd2rZAt5yi9SC4sfotZz_y65OxC_DpSb0DD2ZGoAr5G5CWtbh_ouFF8GyRaY91qgXtX9DUof"
          />
        </Link>
      </div>
    </header>
  );
};

export default Header;
