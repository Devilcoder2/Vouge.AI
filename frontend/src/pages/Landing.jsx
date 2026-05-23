import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

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

  // Interaction scroll triggers and parallax effects
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

    const handleScroll = () => {
      const scrolled = window.pageYOffset;
      const parallaxImages = document.querySelectorAll(".parallax-img");

      parallaxImages.forEach((img) => {
        const speed = 0.15;
        const rect = img.parentElement.getBoundingClientRect();
        const visible = rect.top < window.innerHeight && rect.bottom > 0;

        if (visible) {
          const yPos = -(scrolled * speed);
          img.style.transform = `translateY(${yPos % 50}px) scale(1.1)`;
        }
      });
    };

    window.addEventListener("scroll", handleScroll);

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
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <div className="bg-background text-on-background font-body-md overflow-x-hidden bg-shimmer min-h-screen">
      {/* Top Navigation */}
      <header className="fixed top-0 left-0 w-full z-50 bg-surface/90 backdrop-blur-xl border-b border-white/5 h-24">
        <nav className="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop h-full max-w-container-max mx-auto">
          <a
            className="font-headline-md text-headline-md tracking-widest uppercase text-on-surface"
            href="#home"
          >
            VOGUE.AI
          </a>
          <div className="hidden md:flex items-center gap-12">
            <a
              className="font-body-md text-body-md text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#home"
            >
              Home
            </a>
            <a
              className="font-body-md text-body-md text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#features"
            >
              Features
            </a>
            <a
              className="font-body-md text-body-md text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#pricing"
            >
              Pricing
            </a>
            <a
              className="font-body-md text-body-md text-on-surface-variant hover:text-primary transition-all duration-300"
              href="#footer"
            >
              Footer
            </a>
          </div>
          <button
            onClick={() => navigate("/app")}
            className="bg-on-surface text-surface px-8 py-3 font-label-sm text-label-sm hover:opacity-80 transition-all active:scale-95 duration-300 cursor-pointer"
          >
            Get Started
          </button>
        </nav>
      </header>

      {/* Hero Section */}
      <section
        className="relative min-h-screen flex flex-col justify-end pb-32 pt-24 parallax-wrap"
        id="home"
      >
        <div className="absolute inset-0 z-0">
          <img
            alt="A cinematic, high-fashion editorial shot"
            className="w-full h-full object-cover opacity-60 hero-mask parallax-img"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAwwLcDs8_DUH0QmR_2bbHB72MMnUajVf-I_yzCKyL52jtmuip4fUUGqTYonztxyzb6kC9UiwswXlpyGdKIvsFeOCdDQydmsZEG5HbTHr025FV7PGmh8CVSK1x0O9CdXLbnFm6cc918bJxnHomRhnBw3xbkhKowGBqh7bh8XyluiUd-jnB8PrYAbGKiyeyL4mg8Z1hZeueemLQp6ukJRnP7IxU4fyM011FY-roc8BDiZKltI2qHnpLe8dppivXws9Ivj0vkfuYIp5G9"
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
            <h1
              className="font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface leading-tight mb-8 hero-reveal"
              style={{ animationDelay: "0.3s" }}
            >
              The Future of <br />
              <span className="italic font-normal">Personal Style.</span>
            </h1>
            <p
              className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mb-12 hero-reveal"
              style={{ animationDelay: "0.5s" }}
            >
              A sophisticated AI ecosystem designed to digitize your wardrobe and
              augment your fashion intelligence with precision analytics and generative
              vision.
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
              <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg mb-6 leading-tight">
                Your Closet, <br />
                Cloud-Sync'd.
              </h2>
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
            <div className="md:col-span-7 order-1 md:order-2 parallax-wrap">
              <div className="relative aspect-[4/3] bg-surface-container overflow-hidden group rounded-xl">
                <img
                  alt="Scanning digital interface"
                  className="w-full h-full object-cover grayscale brightness-75 group-hover:scale-105 transition-transform duration-1000 parallax-img"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuDEZYusF-y6VoJWopZ918BPL_DP_nPlisIHNjGTs8q7pI2rJT4QYdL58P_qIyweeoPcaivymXWnUM4W9pE5EX6Y7g-6Oxi5oKib-wuYNLnYyJYXOPhVt9gZo0xaD4skeDQlK7c6-ADLxcCjvzY_LOj2JjPtK8ML9C8IBcGZf3SvFr5Kxi5sf4dy8g5b86XFT444z0EQbnyP7qI240wUnaMtiUtdLwR9Dux9YXbnUBvxgaw3W2YRxUP5jx4RDYSvIbumrb13OGSpeiy5"
                />
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
              </div>
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
              <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg leading-tight">
                The Stylist That Knows You.
              </h2>
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
              <div className="md:col-span-1 bg-surface-container-high p-10 flex flex-col border border-white/5 hover:border-primary/20 transition-all duration-500 hover:scale-105 rounded-xl">
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
              <div className="relative overflow-hidden border border-white/5 group hover:scale-105 transition-all duration-700 parallax-wrap rounded-xl min-h-[400px]">
                <img
                  alt="Fashion accessories"
                  className="w-full h-full object-cover brightness-50 grayscale group-hover:scale-110 group-hover:brightness-75 transition-all duration-1000 parallax-img absolute inset-0"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCVt7Dk6LzSQuctVLdB4fUX7kOy6uau9dMxQe1owy64gQ9vY5Mt7-nv3-e158hYeq2x1FcKIJHuaJ_Bd6MoXpdNfFIdniU5R9MyHr2_bmTHGj5SsLBweJUSn1YfE_yPRDb4dlCsp_P83yihxw12_GRh5rlLL1qeoI7kE216TNzI_bGUPqjshftUrfTltKWlFNIo_VHu_Jc3G9_KKRCgal4tcv5xc8YKYkfXLS-GERPa4d6greV3K8XXlWKJuCDuL8BSB3SXPs6xQivK"
                />
                <div className="absolute bottom-10 left-10 right-10 z-10">
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
              <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg leading-tight">
                Fashion, Decoded.
              </h2>
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
            <div className="glass-card p-8 border-l-4 border-primary rounded-r-xl">
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
            <div className="glass-card p-8 border-l-4 border-outline rounded-r-xl">
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
            <div className="glass-card p-8 border-l-4 border-primary rounded-r-xl">
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
            <div className="glass-card p-8 border-l-4 border-outline rounded-r-xl">
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
                    <div className="bg-surface-container-highest aspect-[3/4] overflow-hidden group parallax-wrap rounded-xl">
                      <img
                        alt="Model shot"
                        className="w-full h-full object-cover opacity-80 group-hover:scale-110 transition-transform duration-1000 parallax-img"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4ACozDMUF9VhJhKTAA8UhCPAL7G8p7_YV3Vx9FRvWJCr1p_acLSEgAP3NBOB14yqJCF7FzUJPE-TlGcS5NcP2c9z1gICJqfjGWRsFvzl2CxGWcw2X106rt3HDNDm7uluKsbAroEPaA-fhh74KI_qyhNQJqgFQ4bd_pNBvsjlX1EgsmQYniR9epV-YnOlfCSvjkguH7e47xDXCQhY-q6VQhVmxe31rauxEy5ZNmp9jGnlUQQF720TF_kSuT0itRpF-HHBcxqzfABsk"
                      />
                    </div>
                    <div className="bg-surface-container-highest aspect-square overflow-hidden group parallax-wrap rounded-xl">
                      <img
                        alt="Chelsea boots"
                        className="w-full h-full object-cover opacity-80 group-hover:scale-110 transition-transform duration-1000 parallax-img"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuCIeqiplE_DNYSpHtH9xIcTCpJrYxw0hY1tCkMFi5y3pfpyFCO1_sltlueYKuq2SXT20orl1yMOzDd89-a6DsFLfOJISkHVst4QCckh-br3tPRRfLqdO4tcL9vJ3G1yMPyDnnzwa4PzUxrzsVNvsplwIG52S_I1RAVrHzG_la_NRha3IFx0WkJ6gc-lGuk8E58jKd2MJXR4NcdWVosuYJIMamu7Wp78JhfRIfvHRqH9eDDk3gAzBf4okZLy-dvhLxvW4erScwQ_GzHR"
                      />
                    </div>
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
                    <div className="bg-surface-container-highest aspect-[3/4] overflow-hidden group parallax-wrap rounded-xl">
                      <img
                        alt="Arrangement of clothing"
                        className="w-full h-full object-cover opacity-80 group-hover:scale-110 transition-transform duration-1000 parallax-img"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuBwPtrWSe3LkEKXLmXtnxr03TwofdkI8ZpR3rqI_Bm3Qu4KMK3R4G0uo5JglnrNect2mTNEgPI-GP1fAZgRuUTdnaFTYH14DLpPnVzDaOJs2b2pBh62QfE1AlZ4NjOWk6-VIHqHfUMsPqvSDqc1cuxqzclWgqknmvKJxXiNzEwwzbbQ7vEHk0ATJbUiRRCpJafBq4StqSia1tb0ldbXvdyl3P4yHQHzgrhRQppN4756YEKRMSJoD9v3-_FU5xxUzqjPXQcf48VcsdYY"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div className="md:col-span-5">
                <span className="font-label-sm text-label-sm text-primary mb-4 block">
                  04 — GAP ANALYSIS
                </span>
                <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg mb-8 leading-tight">
                  Unlock the Look.
                </h2>
                <p className="font-body-lg text-on-surface-variant mb-10 leading-relaxed">
                  Our intelligence engine identifies the missing pieces in your
                  collection. Instead of generic shopping, VOGUE.AI suggests specific
                  additions that multiply your existing outfit combinations by 3x.
                </p>
                <div className="space-y-6">
                  <div
                    onClick={() => navigate("/app")}
                    className="p-6 bg-white/5 border border-white/5 hover:border-primary/40 hover:scale-[1.02] transition-all duration-500 cursor-pointer shadow-lg hover:shadow-primary/5 rounded-xl"
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
                    className="p-6 bg-white/5 border border-white/5 hover:border-primary/40 hover:scale-[1.02] transition-all duration-500 cursor-pointer shadow-lg hover:shadow-primary/5 rounded-xl"
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
            <h2 className="font-headline-lg text-display-lg-mobile md:text-headline-lg mb-8 leading-tight">
              Tailored for Every Aspiration.
            </h2>
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
