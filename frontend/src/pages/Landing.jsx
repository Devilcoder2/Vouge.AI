import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CardContainer, CardBody, CardItem } from "@/components/ui/3d-card";

// Premium dynamic lens distortion and spotlight character hover effect
const LensHeading = ({ line1, line2, inline = false, isH1 = false, className = "", style = {}, justifyClass = "justify-center md:justify-start" }) => {
  const [hoveredChar, setHoveredChar] = useState(null); // { lineIndex, charIndex }
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setCoords({ x, y });
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setHoveredChar(null);
  };

  const renderLine = (text, lineIndex, extraClass = "") => {
    const chars = Array.from(text);
    return (
      <span className={`inline-block whitespace-nowrap ${extraClass}`}>
        {chars.map((char, charIndex) => {
          const isSpace = char === " ";
          
          let scale = 1;
          let color = "inherit";
          let shadow = "none";

          if (hoveredChar && hoveredChar.lineIndex === lineIndex) {
            const dist = Math.abs(hoveredChar.charIndex - charIndex);
            if (dist === 0) {
              scale = 1.35;
              color = "rgba(255, 255, 255, 1)";
              shadow = "0 0 15px rgba(255, 255, 255, 0.6), 0 0 30px var(--color-primary)";
            } else if (dist === 1) {
              scale = 1.2;
              color = "rgba(235, 235, 235, 0.9)";
              shadow = "0 0 8px rgba(255, 255, 255, 0.3)";
            } else if (dist === 2) {
              scale = 1.08;
              color = "rgba(210, 210, 210, 0.85)";
            }
          }

          return (
            <span
              key={charIndex}
              onMouseEnter={() => !isSpace && setHoveredChar({ lineIndex, charIndex })}
              onMouseMove={() => !isSpace && hoveredChar?.charIndex !== charIndex && setHoveredChar({ lineIndex, charIndex })}
              className="inline-block transition-all duration-200 ease-out select-none"
              style={{
                transform: `scale(${scale}) translateY(${scale > 1 ? -(scale - 1) * 10 : 0}px)`,
                color: color,
                textShadow: shadow,
                padding: isSpace ? "0 0.1em" : "0 0.02em",
                transformOrigin: "bottom center",
              }}
            >
              {isSpace ? "\u00A0" : char}
            </span>
          );
        })}
      </span>
    );
  };

  const HeadingTag = isH1 ? "h1" : "h2";

  return (
    <HeadingTag
      className={`${className} relative cursor-default select-none`}
      style={style}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* soft radial spotlight background glow behind text */}
      {isHovered && (
        <span
          className="absolute inset-0 pointer-events-none transition-opacity duration-500 rounded-full blur-2xl"
          style={{
            background: `radial-gradient(150px circle at ${coords.x}px ${coords.y}px, rgba(200, 198, 197, 0.08) 0%, transparent 100%)`,
            zIndex: -1,
          }}
        />
      )}
      
      {inline ? (
        <span className={`flex flex-wrap items-center gap-[0.2em] ${justifyClass}`}>
          {line1 && renderLine(line1, 0)}
          {line2 && renderLine(line2, 1, "italic font-extrabold text-on-surface")}
        </span>
      ) : (
        <>
          {line1 && (
            <span className={line2 ? "block mb-1 md:mb-2" : "block"}>
              {renderLine(line1, 0)}
            </span>
          )}
          {line2 && (
            <span className="block">
              {renderLine(line2, 1, "italic font-extrabold text-on-surface")}
            </span>
          )}
        </>
      )}
    </HeadingTag>
  );
};

export const Landing = () => {
  const navigate = useNavigate();
  const [billingYearly, setBillingYearly] = useState(false);

  // Dynamic glass-card radial spotlight hover
  const handleMouseMove = (e) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.background = `radial-gradient(600px circle at ${x}px ${y}px, rgba(255,255,255,0.06), transparent 40%)`;
  };

  const handleMouseLeave = (e) => {
    e.currentTarget.style.background = "rgba(255, 255, 255, 0.02)";
  };

  // Interaction scroll triggers (excluding parallax)
  useEffect(() => {
    const observerOptions = {
      threshold: 0.15,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("active");

          const bars = entry.target.querySelectorAll(".bar-reveal");
          bars.forEach((bar) => {
            if (bar.dataset.width) {
              bar.style.width = bar.dataset.width;
            }
          });
        }
      });
    }, observerOptions);

    const revealElements = document.querySelectorAll(".reveal");
    revealElements.forEach((el) => observer.observe(el));

    // Initial check for reduced motion preferences
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.querySelectorAll(".bar-reveal").forEach((bar) => {
        if (bar.dataset.width) {
          bar.style.width = bar.dataset.width;
        }
      });
    }

    return () => {
      revealElements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  return (
    <div className="bg-background text-on-background font-body-md overflow-x-hidden bg-shimmer min-h-screen">
      {/* Top Navigation */}
      <header className="fixed top-0 left-0 w-full z-50 bg-surface/90 backdrop-blur-xl border-b border-white/5 h-16">
        <nav className="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop h-full max-w-container-max mx-auto">
          <a
            className="font-display text-2xl md:text-3xl font-extrabold tracking-[0.2em] uppercase text-on-surface hover:opacity-90 transition-opacity"
            href="#home"
          >
            VOGUE.AI
          </a>
          <div className="hidden md:flex items-center gap-12">
            <a
              className="font-body-md text-[11px] uppercase tracking-widest font-semibold text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#home"
            >
              Home
            </a>
            <a
              className="font-body-md text-[11px] uppercase tracking-widest font-semibold text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#features"
            >
              Features
            </a>
            <a
              className="font-body-md text-[11px] uppercase tracking-widest font-semibold text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#pricing"
            >
              Pricing
            </a>
            <a
              className="font-body-md text-[11px] uppercase tracking-widest font-semibold text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#footer"
            >
              Footer
            </a>
          </div>
          <button
            onClick={() => navigate("/app")}
            className="bg-on-surface text-surface px-6 py-2.5 font-label-sm text-xs font-bold uppercase tracking-widest hover:opacity-80 transition-all active:scale-95 duration-300 cursor-pointer"
          >
            Get Started
          </button>
        </nav>
      </header>

      {/* Hero Section */}
      <section
        className="relative min-h-screen flex flex-col justify-end pb-24 pt-32 parallax-wrap"
        id="home"
      >
        <div className="absolute inset-0 z-0">
          <img
            alt="A cinematic, high-fashion editorial shot of model wearing luxury coat"
            className="w-full h-full object-cover opacity-60 hero-mask"
            style={{ objectPosition: "center 18%" }}
            src="/assets/fashion_hero_bg.png"
          />
        </div>
        <div className="relative z-10 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto w-full">
          <div className="max-w-4xl">
            <span
              className="font-label-sm text-label-sm text-primary tracking-widest uppercase mb-6 block hero-reveal"
              style={{ animationDelay: "0.1s" }}
            >
              Augmented Fashion Intelligence
            </span>
            <LensHeading
              isH1={true}
              line1="The Future of"
              line2="Personal Style."
              className="font-display text-4xl sm:text-5xl md:text-7xl font-extrabold tracking-tight text-on-surface leading-[1.08] mb-8 hero-reveal"
            />
            <p
              className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mb-12 hero-reveal leading-relaxed"
              style={{ animationDelay: "0.5s" }}
            >
              A sophisticated AI ecosystem designed to{" "}
                digitize your wardrobe
              and augment your{" "}
                fashion intelligence
              with precision analytics and generative vision.
            </p>
            <div
              className="flex flex-wrap gap-6 items-center hero-reveal"
              style={{ animationDelay: "0.7s" }}
            >
              <button
                onClick={() => navigate("/app")}
                className="bg-on-surface text-surface px-10 py-5 font-label-sm text-label-sm hover:scale-105 transition-all active:scale-95 duration-500 shadow-xl shadow-white/5 cursor-pointer"
              >
                Get Started
              </button>
              <button
                onClick={() => navigate("/app")}
                className="border border-outline/30 text-on-surface px-10 py-5 font-label-sm text-label-sm hover:bg-white/5 hover:border-white transition-all duration-500 cursor-pointer"
              >
                View Atelier
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Wrapper */}
      <div id="features">
        {/* Feature 1: Wardrobe Digitization */}
        <section className="py-32 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto reveal">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter items-center">
            <div className="md:col-span-5 order-2 md:order-1">
              <span className="font-label-sm text-label-sm text-primary mb-4 block">
                01 — DIGITIZATION
              </span>
              <LensHeading
                line1="Your Closet,"
                line2="Cloud-Sync'd."
                className="font-display text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1] mb-6"
              />
              <p className="font-body-md text-on-surface-variant mb-8 leading-relaxed">
                Transform physical garments into high-fidelity digital assets. Our
                proprietary AI automatically removes backgrounds and identifies textile
                properties, creating a seamless virtual mirror of your physical
                wardrobe.
              </p>
              <ul className="space-y-4">
                <li className="flex items-center gap-4 text-on-surface-variant font-label-sm hover:text-on-surface transition-colors cursor-default">
                  <span
                    className="material-symbols-outlined text-primary"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    auto_fix_high
                  </span>
                  One-tap background isolation
                </li>
                <li className="flex items-center gap-4 text-on-surface-variant font-label-sm hover:text-on-surface transition-colors cursor-default">
                  <span
                    className="material-symbols-outlined text-primary"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    texture
                  </span>
                  Fabric and weave detection
                </li>
              </ul>
            </div>
            <div className="md:col-span-7 order-1 md:order-2">
              <CardContainer containerClassName="w-full py-0 select-none">
                <CardBody className="relative w-full aspect-[4/3] bg-surface-container overflow-hidden rounded-xl">
                  <CardItem translateZ="60" className="absolute inset-0 w-full h-full">
                    <img
                      alt="Scanning digital interface showing textile weave analyze"
                      className="w-full h-full object-cover grayscale brightness-75 block"
                      src="/assets/closet_scan_feature.png"
                    />
                  </CardItem>
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-64 h-64 border border-primary/20 bg-white/5 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center animate-float rounded-xl">
                      <span className="material-symbols-outlined text-primary text-4xl mb-2">
                        scan
                      </span>
                      <span className="font-label-sm uppercase tracking-widest text-[10px]">
                        Processing Textile...
                      </span>
                    </div>
                  </div>
                </CardBody>
              </CardContainer>
            </div>
          </div>
        </section>

        {/* Feature 2: Personal Stylist */}
        <section className="py-32 bg-surface-container-lowest/50 reveal">
          <div className="px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto">
            <div className="mb-20 text-center max-w-2xl mx-auto">
              <span className="font-label-sm text-label-sm text-primary mb-4 block">
                02 — CONVERSATIONAL AI
              </span>
              <LensHeading
                line1="The Stylist"
                line2="That Knows You."
                className="font-display text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1]"
                style={{ textAlign: "center" }}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Card 1 */}
              <div
                className="glass-card p-10 flex flex-col justify-between min-h-[400px] rounded-xl"
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              >
                <div>
                  <span className="material-symbols-outlined text-primary text-3xl mb-6">
                    wb_cloudy
                  </span>
                  <h3 className="font-headline-md mb-4 text-xl font-medium">
                    Environmentally Aware
                  </h3>
                  <p className="font-body-md text-on-surface-variant leading-relaxed">
                    Real-time weather integration ensures your style is never compromised
                    by the elements.
                  </p>
                </div>
                <div className="mt-8 border-t border-white/10 pt-6">
                  <div className="flex justify-between items-center text-label-sm">
                    <span className="text-on-surface-variant uppercase text-[10px]">
                      Current London
                    </span>
                    <span className="text-on-surface text-[11px] font-semibold">
                      14°C — Light Rain
                    </span>
                  </div>
                </div>
              </div>

              {/* Card 2 */}
              <div
                className="glass-card p-10 flex flex-col justify-between min-h-[400px] rounded-xl"
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              >
                <div className="flex-grow space-y-6">
                  <div className="bg-surface p-4 max-w-[80%] rounded-tr-xl rounded-br-xl border-l-2 border-primary animate-float">
                    <p className="font-body-md text-sm italic">
                      "What should I wear for a tech gala in Tokyo?"
                    </p>
                  </div>
                  <div
                    className="bg-primary-container p-4 max-w-[80%] ml-auto rounded-tl-xl rounded-bl-xl border-r-2 border-on-surface-variant animate-float"
                    style={{ animationDelay: "1s" }}
                  >
                    <p className="font-body-md text-sm">
                      "Given the humidity and occasion, I suggest the Charcoal Silk
                      Blouson..."
                    </p>
                  </div>
                </div>
                <div className="mt-8">
                  <h3 className="font-headline-md mb-2 text-xl font-medium">
                    Occasion Reasoning
                  </h3>
                  <p className="font-body-md text-on-surface-variant leading-relaxed">
                    Sophisticated logic for every calendar event.
                  </p>
                </div>
              </div>

              {/* Card 3 */}
              <div
                className="glass-card relative overflow-hidden min-h-[400px] rounded-xl flex flex-col justify-end p-10 group"
                onMouseMove={(e) => {
                  handleMouseMove(e);
                  const overlay = e.currentTarget.querySelector(".spotlight-overlay");
                  if (overlay) {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    overlay.style.background = `radial-gradient(600px circle at ${x}px ${y}px, rgba(255,255,255,0.06), transparent 40%)`;
                    overlay.style.opacity = "1";
                  }
                }}
                onMouseLeave={(e) => {
                  handleMouseLeave(e);
                  const overlay = e.currentTarget.querySelector(".spotlight-overlay");
                  if (overlay) {
                    overlay.style.background = "transparent";
                    overlay.style.opacity = "0";
                  }
                }}
              >
                <img
                  alt="Fashion accessories flatlay styling"
                  className="w-full h-full object-cover brightness-50 grayscale absolute inset-0 pointer-events-none transition-transform duration-700 group-hover:scale-105"
                  src="/assets/curation_collage_feature.png"
                />
                <div className="spotlight-overlay absolute inset-0 pointer-events-none transition-opacity duration-300 opacity-0 z-5" />
                <div className="relative z-10">
                  <h3 className="font-headline-md text-on-surface text-xl font-medium">
                    Curation Engine
                  </h3>
                  <p className="font-body-md text-on-surface-variant mt-2 leading-relaxed">
                    Driven by your aesthetic history.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature 3: Style DNA */}
        <section className="py-32 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto reveal">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter items-end mb-16">
            <div className="md:col-span-8">
              <span className="font-label-sm text-label-sm text-primary mb-4 block">
                03 — ANALYTICS
              </span>
              <LensHeading
                line1="Fashion,"
                line2="Decoded."
                inline={true}
                className="font-display text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1]"
              />
            </div>
            <div className="md:col-span-4 text-right">
              <button
                onClick={() => navigate("/app")}
                className="font-label-sm text-primary uppercase border-b border-primary/30 hover:border-primary transition-all duration-300 cursor-pointer"
              >
                Deep Dive Into Data
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div
              className="glass-card p-8 border-l-4 border-primary rounded-r-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <span className="text-3xl font-headline-md block mb-2 font-semibold">
                94%
              </span>
              <span className="font-label-sm uppercase text-on-surface-variant tracking-wider text-[11px]">
                Minimalist Affinity
              </span>
              <div className="w-full h-1 bg-white/5 mt-4 overflow-hidden rounded-full">
                <div
                  className="w-[0%] h-full bg-primary transition-all duration-[2s] ease-out bar-reveal"
                  data-width="94%"
                ></div>
              </div>
            </div>
            <div
              className="glass-card p-8 border-l-4 border-outline rounded-r-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <div className="flex gap-2 mb-2.5">
                <div className="w-4 h-4 bg-surface-container-highest rounded-[2px]"></div>
                <div className="w-4 h-4 bg-on-primary-container rounded-[2px]"></div>
                <div className="w-4 h-4 bg-secondary-container rounded-[2px]"></div>
              </div>
              <span className="font-label-sm uppercase text-on-surface-variant tracking-wider text-[11px]">
                Monochrome Bias
              </span>
              <div className="w-full h-1 bg-white/5 mt-4 overflow-hidden rounded-full">
                <div
                  className="w-[0%] h-full bg-outline transition-all duration-[2s] ease-out bar-reveal"
                  data-width="82%"
                ></div>
              </div>
            </div>
            <div
              className="glass-card p-8 border-l-4 border-primary rounded-r-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <span className="text-3xl font-headline-md block mb-2 font-semibold">
                $4.20
              </span>
              <span className="font-label-sm uppercase text-on-surface-variant tracking-wider text-[11px]">
                Avg. Cost Per Wear
              </span>
              <div className="w-full h-1 bg-white/5 mt-4 overflow-hidden rounded-full">
                <div
                  className="w-[0%] h-full bg-primary transition-all duration-[2s] ease-out bar-reveal"
                  data-width="60%"
                ></div>
              </div>
            </div>
            <div
              className="glass-card p-8 border-l-4 border-outline rounded-r-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <span className="text-3xl font-headline-md block mb-2 font-semibold">
                78%
              </span>
              <span className="font-label-sm uppercase text-on-surface-variant tracking-wider text-[11px]">
                Utilization Rate
              </span>
              <div className="w-full h-1 bg-white/5 mt-4 overflow-hidden rounded-full">
                <div
                  className="w-[0%] h-full bg-outline transition-all duration-[2s] ease-out bar-reveal"
                  data-width="78%"
                ></div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature 4: Gap Analysis */}
        <section className="py-32 bg-surface-container-low overflow-hidden reveal">
          <div className="px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-16 items-center">
              <div className="md:col-span-7">
                <div className="relative grid grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <CardContainer containerClassName="w-full py-0 select-none">
                      <CardBody className="relative w-full aspect-[3/4] bg-surface-container-highest overflow-hidden rounded-xl">
                        <CardItem translateZ="60" className="absolute inset-0 w-full h-full">
                          <img
                            alt="High-end editorial fashion portrait"
                            className="w-full h-full object-cover opacity-80 block"
                            src="/assets/fashion_portrait_gap.png"
                          />
                        </CardItem>
                      </CardBody>
                    </CardContainer>

                    <CardContainer containerClassName="w-full py-0 select-none">
                      <CardBody className="relative w-full aspect-square bg-surface-container-highest overflow-hidden rounded-xl">
                        <CardItem translateZ="60" className="absolute inset-0 w-full h-full">
                          <img
                            alt="Sleek black Chelsea leather boots"
                            className="w-full h-full object-cover opacity-80 block"
                            src="/assets/chelsea_boots_gap.png"
                          />
                        </CardItem>
                      </CardBody>
                    </CardContainer>
                  </div>
                  <div className="space-y-4 mt-12">
                    <div className="bg-primary/10 aspect-square flex items-center justify-center p-8 border border-primary/20 animate-float rounded-xl">
                      <div className="text-center">
                        <span className="material-symbols-outlined text-primary text-5xl mb-4">
                          search_insights
                        </span>
                        <p className="font-label-sm uppercase tracking-tighter text-[11px] font-bold leading-normal">
                          Analysis <br />
                          Complete
                        </p>
                      </div>
                    </div>

                    <CardContainer containerClassName="w-full py-0 select-none">
                      <CardBody className="relative w-full aspect-[3/4] bg-surface-container-highest overflow-hidden rounded-xl">
                        <CardItem translateZ="60" className="absolute inset-0 w-full h-full">
                          <img
                            alt="Minimalist collection of folded neutral clothing"
                            className="w-full h-full object-cover opacity-80 block"
                            src="/assets/clothing_layout_gap.png"
                          />
                        </CardItem>
                      </CardBody>
                    </CardContainer>
                  </div>
                </div>
              </div>
              <div className="md:col-span-5">
                <span className="font-label-sm text-label-sm text-primary mb-4 block">
                  04 — GAP ANALYSIS
                </span>
                <LensHeading
                  line1="Unlock"
                  line2="the Look."
                  inline={true}
                  className="font-display text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1] mb-8"
                />
                <p className="font-body-lg text-on-surface-variant mb-10 leading-relaxed">
                  Our intelligence engine identifies the missing pieces in your
                  collection. Instead of generic shopping, VOGUE.AI suggests specific
                  additions that multiply your existing outfit combinations by 3x.
                </p>
                <div className="space-y-6">
                  <div
                    onClick={() => navigate("/app")}
                    className="glass-card p-6 border border-white/5 hover:border-primary/40 hover:scale-[1.02] transition-all duration-500 cursor-pointer shadow-lg hover:shadow-primary/5 rounded-xl"
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                  >
                    <h4 className="font-headline-md text-lg mb-1 font-medium">
                      Smart Shoppable Links
                    </h4>
                    <p className="font-body-md text-sm text-on-surface-variant">
                      Direct integration with ethical luxury retailers.
                    </p>
                  </div>
                  <div
                    onClick={() => navigate("/app")}
                    className="glass-card p-6 border border-white/5 hover:border-primary/40 hover:scale-[1.02] transition-all duration-500 cursor-pointer shadow-lg hover:shadow-primary/5 rounded-xl"
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                  >
                    <h4 className="font-headline-md text-lg mb-1 font-medium">
                      Outfit Multipliers
                    </h4>
                    <p className="font-body-md text-sm text-on-surface-variant">
                      See how one new item unlocks 10+ new looks.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Pricing Section */}
      <section className="py-32 reveal" id="pricing">
        <div className="px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto">
          <div className="text-center mb-20">
            <span className="font-label-sm text-label-sm text-primary mb-4 block">
              INVESTMENT
            </span>
            <LensHeading
              line1="Tailored for"
              line2="Every Aspiration."
              inline={true}
              justifyClass="justify-center"
              className="font-display text-3xl md:text-5xl font-extrabold tracking-tight leading-[1.1] mb-8"
            />
            {/* Billing Toggle */}
            <div className="flex items-center justify-center gap-4 mt-8 select-none">
              <span
                className={`font-label-sm text-xs tracking-wider uppercase font-semibold transition-colors duration-300 ${
                  !billingYearly ? "text-on-surface" : "text-on-surface-variant"
                }`}
              >
                Monthly
              </span>
              <button
                onClick={() => setBillingYearly(!billingYearly)}
                className="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full bg-surface-container-highest border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                aria-label="Toggle Billing Cycle"
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-on-surface shadow ring-0 transition duration-200 ease-in-out ${
                    billingYearly
                      ? "translate-x-5 bg-background"
                      : "translate-x-0 bg-primary"
                  }`}
                />
              </button>
              <span
                className={`font-label-sm text-xs tracking-wider uppercase font-semibold transition-colors duration-300 ${
                  billingYearly ? "text-on-surface" : "text-on-surface-variant"
                }`}
              >
                Yearly
              </span>
              <span className="bg-primary/10 text-primary px-3 py-1 text-[10px] font-bold tracking-widest uppercase rounded-full border border-primary/20">
                2 Months Free
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Atelier Plan */}
            <div
              className="glass-card p-10 flex flex-col h-full rounded-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <div className="mb-10">
                <h3 className="font-headline-md mb-2 text-xl font-medium">Atelier</h3>
                <p className="font-body-md text-sm text-on-surface-variant mb-6 leading-relaxed">
                  Foundational style digitization.
                </p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-headline-md font-semibold">$0</span>
                  <span className="text-on-surface-variant font-label-sm text-[10px]">
                    /MO
                  </span>
                </div>
              </div>
              <ul className="flex-grow space-y-4 mb-10">
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Essential digitization (up to 50 items)
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Basic occasion styling
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Weather-aware recommendations
                </li>
              </ul>
              <button
                onClick={() => navigate("/app")}
                className="w-full border border-outline/30 py-4 font-label-sm uppercase tracking-widest text-[11px] hover:bg-white/5 transition-colors cursor-pointer rounded-xl"
              >
                Start Creating
              </button>
            </div>

            {/* Muse Plan (Recommended) */}
            <div
              className="glass-card p-10 flex flex-col h-full relative border-primary/40 ring-1 ring-primary/20 shadow-2xl shadow-primary/5 rounded-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-primary text-surface font-label-sm px-4 py-1 uppercase tracking-tighter text-[9px] font-bold rounded-[3px]">
                Recommended
              </div>
              <div className="mb-10">
                <h3 className="font-headline-md mb-2 text-xl font-medium">Muse</h3>
                <p className="font-body-md text-sm text-on-surface-variant mb-6 leading-relaxed">
                  Advanced AI style acceleration.
                </p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-headline-md font-semibold">
                    {billingYearly ? "$15" : "$19"}
                  </span>
                  <span className="text-on-surface-variant font-label-sm text-[10px]">
                    /MO
                  </span>
                </div>
              </div>
              <ul className="flex-grow space-y-4 mb-10">
                <li className="flex items-start gap-3 text-sm text-on-surface leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Unlimited wardrobe digitization
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Advanced AI aesthetic analysis
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Priority styling (instant responses)
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Multi-device cloud sync
                </li>
              </ul>
              <button
                onClick={() => navigate("/app")}
                className="w-full bg-on-surface text-surface py-4 font-label-sm uppercase tracking-widest text-[11px] hover:opacity-90 transition-opacity cursor-pointer rounded-xl font-bold"
              >
                Become a Muse
              </button>
            </div>

            {/* Couture Plan */}
            <div
              className="glass-card p-10 flex flex-col h-full rounded-xl"
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <div className="mb-10">
                <h3 className="font-headline-md mb-2 text-xl font-medium">Couture</h3>
                <p className="font-body-md text-sm text-on-surface-variant mb-6 leading-relaxed">
                  The pinnacle of digital fashion.
                </p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-headline-md font-semibold">
                    {billingYearly ? "$39" : "$49"}
                  </span>
                  <span className="text-on-surface-variant font-label-sm text-[10px]">
                    /MO
                  </span>
                </div>
              </div>
              <ul className="flex-grow space-y-4 mb-10">
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Everything in Muse
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Personal style consultant concierge
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Gap analysis shopping assistant
                </li>
                <li className="flex items-start gap-3 text-sm text-on-surface-variant leading-relaxed">
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 select-none">
                    check
                  </span>
                  Early access to luxury drops
                </li>
              </ul>
              <button
                onClick={() => navigate("/app")}
                className="w-full border border-outline/30 py-4 font-label-sm uppercase tracking-widest text-[11px] hover:bg-white/5 transition-colors cursor-pointer rounded-xl"
              >
                Apply for Couture
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        className="bg-surface-container-lowest border-t border-white/5"
        id="footer"
      >
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center w-full px-margin-mobile md:px-margin-desktop py-16 gap-gutter max-w-container-max mx-auto">
          <div className="space-y-4">
            <div className="font-headline-md text-headline-md text-on-surface uppercase tracking-widest text-xl font-semibold">
              VOGUE.AI
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-xs text-sm">
              © 2024 VOGUE.AI. The future of fashion intelligence.
            </p>
          </div>
          <div className="flex flex-wrap gap-8 md:gap-16">
            <a
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors focus:underline underline-offset-4 text-xs"
              href="#"
            >
              Journal
            </a>
            <a
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors focus:underline underline-offset-4 text-xs"
              href="#"
            >
              Privacy
            </a>
            <a
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors focus:underline underline-offset-4 text-xs"
              href="#"
            >
              Terms
            </a>
            <a
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors focus:underline underline-offset-4 text-xs"
              href="#"
            >
              Atelier
            </a>
            <a
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface transition-colors focus:underline underline-offset-4 text-xs"
              href="#"
            >
              Press
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
