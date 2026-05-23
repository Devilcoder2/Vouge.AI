import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";

export const AIChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "ai",
      text: "Good morning! Preparing for your event tonight? I've found a few options.",
      time: "9:00 AM",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;

    const currentTime = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMsg = {
      id: Date.now(),
      sender: "user",
      text: inputValue,
      time: currentTime,
    };

    setMessages((prev) => [...prev, userMsg]);
    const userText = inputValue;
    setInputValue("");

    // Simulate AI Stylist response
    setTimeout(() => {
      let responseText =
        "That sounds lovely! Let's style that with your charcoal wool trench to match the brisk evening weather.";
      const lowerText = userText.toLowerCase();

      if (lowerText.includes("formal") || lowerText.includes("party")) {
        responseText =
          "For tonight's formal setup, I highly suggest matching your black silk slip dress with the off-white cashmere cardigan. Classy, yet effortless!";
      } else if (lowerText.includes("casual") || lowerText.includes("sporty")) {
        responseText =
          "Let's lean into upscale leisure. I'd go with your oversized neutral knit top and standard utility slim fit bottoms.";
      } else if (lowerText.includes("hello") || lowerText.includes("hi")) {
        responseText =
          "Hello! I am your VOGUE.AI stylist. Tell me what event or look we are planning today, and I'll scour your wardrobe for the perfect aesthetic!";
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "ai",
          text: responseText,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    }, 900);
  };

  return (
    <Layout title="AI Stylist" hideNav>
      <div className="flex flex-col h-[calc(100vh-140px)] md:h-[calc(100vh-120px)] max-w-4xl mx-auto">
        {/* Chat Message Viewport */}
        <div className="flex-1 overflow-y-auto space-y-6 pb-6 pr-2 hide-scrollbar">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-4 ${
                msg.sender === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* Avatar Icon */}
              {msg.sender === "ai" ? (
                <div className="w-10 h-10 rounded-full bg-tertiary/20 flex items-center justify-center shrink-0 border border-tertiary/30 shadow-md">
                  <span className="material-symbols-outlined text-tertiary text-xl">
                    auto_awesome
                  </span>
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center shrink-0 border border-primary/30 shadow-md">
                  <span className="material-symbols-outlined text-primary text-xl">
                    person
                  </span>
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={`glass-panel p-4 rounded-2xl max-w-[80%] md:max-w-[70%] shadow-lg transition-all duration-300 ${
                  msg.sender === "user"
                    ? "rounded-tr-sm bg-white/5 border-primary/10"
                    : "rounded-tl-sm border-tertiary/10 ai-glow"
                }`}
              >
                <p className="text-sm leading-relaxed text-on-surface">
                  {msg.text}
                </p>
                <span className="text-[10px] text-on-surface-variant block mt-2 text-right opacity-60">
                  {msg.time}
                </span>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Tactile Message Input */}
        <form
          onSubmit={handleSend}
          className="relative flex items-end gap-3 glass-panel rounded-2xl p-2.5 mb-2 focus-within:border-tertiary/40 transition-colors shadow-2xl"
        >
          <Link
            to="/app/camera"
            className="p-3 text-on-surface-variant hover:text-on-surface rounded-xl hover:bg-white/5 flex items-center justify-center transition-all shrink-0"
            aria-label="Upload photo"
          >
            <span className="material-symbols-outlined text-2xl">
              add_photo_alternate
            </span>
          </Link>
          <input
            className="w-full bg-transparent border-none focus:outline-none focus:ring-0 py-3 text-sm text-on-surface placeholder-on-surface-variant/50 pr-4"
            placeholder="Ask your stylist..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <button
            type="submit"
            className="p-3 bg-on-surface hover:bg-tertiary text-surface hover:text-on-tertiary transition-all duration-300 rounded-xl flex items-center justify-center cursor-pointer shrink-0 shadow-md active:scale-95"
            aria-label="Send message"
          >
            <span className="material-symbols-outlined text-xl">send</span>
          </button>
        </form>
      </div>
    </Layout>
  );
};

export default AIChat;
