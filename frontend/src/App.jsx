import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider, Helmet } from "react-helmet-async";

// Pages
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import AIChat from "./pages/AIChat";
import Wardrobe from "./pages/Wardrobe";
import Planner from "./pages/Planner";
import GenericScreen from "./pages/GenericScreen";
import InventoryCategory from "./pages/InventoryCategory";

export const App = () => {
  return (
    <HelmetProvider>
      <BrowserRouter>
        {/* Global base SEO settings */}
        <Helmet>
          <title>VOGUE.AI - Premium AI Fashion Stylist</title>
          <meta
            name="description"
            content="Digitize your wardrobe, discover curated styling options, and chat with your personal AI Stylist."
          />
          <meta name="theme-color" content="#121317" />
        </Helmet>

        <Routes>
          {/* Public Landing / Introduction Page */}
          <Route
            path="/"
            element={
              <>
                <Helmet>
                  <title>VOGUE.AI | The Future of Personal Style</title>
                  <meta
                    name="description"
                    content="A sophisticated AI ecosystem designed to digitize your wardrobe and augment your fashion intelligence with precision analytics."
                  />
                </Helmet>
                <Landing />
              </>
            }
          />

          {/* Main Application Routes under `/app` Namespace */}
          <Route
            path="/app"
            element={
              <>
                <Helmet>
                  <title>Dashboard | VOGUE.AI</title>
                  <meta
                    name="description"
                    content="View today's curated look and see your digitized wardrobe insights."
                  />
                </Helmet>
                <Dashboard />
              </>
            }
          />
          <Route
            path="/app/chat"
            element={
              <>
                <Helmet>
                  <title>AI Stylist Chat | VOGUE.AI</title>
                  <meta
                    name="description"
                    content="Consult your AI fashion stylist for real-time outfit advice."
                  />
                </Helmet>
                <AIChat />
              </>
            }
          />
          <Route
            path="/app/wardrobe"
            element={
              <>
                <Helmet>
                  <title>My Wardrobe | VOGUE.AI</title>
                  <meta
                    name="description"
                    content="Browse your digitized wardrobe categorized into tops, bottoms, and outerwear."
                  />
                </Helmet>
                <Wardrobe />
              </>
            }
          />
          <Route
            path="/app/planner"
            element={
              <>
                <Helmet>
                  <title>Outfit Planner | VOGUE.AI</title>
                  <meta
                    name="description"
                    content="Plan and schedule your curated daily looks matching your calendar agenda."
                  />
                </Helmet>
                <Planner />
              </>
            }
          />

          {/* Application Stubs & Fallbacks */}
          <Route
            path="/app/discover"
            element={<GenericScreen title="Discovery Feed" />}
          />
          <Route
            path="/app/profile"
            element={<GenericScreen title="Profile" />}
          />
          <Route
            path="/app/aesthetic"
            element={<GenericScreen title="Aesthetic Definition" />}
          />
          <Route
            path="/app/inventory/:categoryId"
            element={
              <>
                <Helmet>
                  <title>My Inventory | VOGUE.AI</title>
                  <meta
                    name="description"
                    content="Browse your digitized wardrobe collection archive."
                  />
                </Helmet>
                <InventoryCategory />
              </>
            }
          />
          <Route
            path="/app/item/edit"
            element={<GenericScreen title="Edit Item" />}
          />
          <Route
            path="/app/analysis"
            element={<GenericScreen title="Wardrobe Analysis" />}
          />
          <Route
            path="/app/camera"
            element={<GenericScreen title="Camera Capture" />}
          />
          <Route
            path="/app/processing"
            element={<GenericScreen title="Processing Scan" />}
          />
          <Route
            path="/app/verify"
            element={<GenericScreen title="Verify Item" />}
          />
          <Route
            path="/app/outfit"
            element={<GenericScreen title="Outfit Details" />}
          />
          <Route
            path="/app/recommendations"
            element={<GenericScreen title="Daily Recs" />}
          />
          <Route
            path="/app/unlock"
            element={<GenericScreen title="Unlock Look" />}
          />

          {/* Catch-all Wildcard Route */}
          <Route
            path="*"
            element={<GenericScreen title="Page Not Found" />}
          />
        </Routes>
      </BrowserRouter>
    </HelmetProvider>
  );
};

export default App;
