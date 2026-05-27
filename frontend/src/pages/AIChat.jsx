import React, { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/layout/Layout";
import { apiSendChatMessage } from "../utils/dashboardStore";

export const AIChat = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "ai",
      text: "Good morning Julian! I am your VOGUE.AI personal stylist. Tell me what event or look we are planning today, and I'll scour your wardrobe for the perfect aesthetic!",
      time: "9:00 AM",
      suggestedOutfitId: null
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userText = inputValue;
    const currentTime = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMsg = {
      id: Date.now(),
      sender: "user",
      text: userText,
      time: currentTime,
      suggestedOutfitId: null
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    try {
      // Package full conversation context to Gemini API
      const data = await apiSendChatMessage(userText, messages, "default_user");
      
      const aiTime = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "ai",
          text: data.reply || "I encountered a minor anomaly while cross-indexing your closet metrics. Tell me more about the occasion and we can try again.",
          time: aiTime,
          suggestedOutfitId: data.suggested_outfit_id || null
        }
      ]);
    } catch (err) {
      console.error("Stylist chatbot endpoint error:", err);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Layout title="AI Stylist" hideNav>
      <div className="flex flex-col h-[calc(100vh-140px)] md:h-[calc(100vh-120px)] max-w-4xl mx-auto pb-4">
        
        {/* Chat Message Viewport */}
        <div className="flex-1 overflow-y-auto space-y-6 pb-6 pr-2 hide-scrollbar">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-4 animate-fade-in ${
                msg.sender === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* Avatar Icon */}
              {msg.sender === "ai" ? (
                <div className="w-10 h-10 rounded-full bg-tertiary/20 flex items-center justify-center shrink-0 border border-tertiary/30 shadow-md">
                  <span className="material-symbols-outlined text-tertiary text-xl select-none">
                    auto_awesome
                  </span>
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center shrink-0 border border-primary/30 shadow-md">
                  <span className="material-symbols-outlined text-primary text-xl select-none">
                    person
                  </span>
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={`glass-panel p-4 rounded-2xl max-w-[80%] md:max-w-[70%] shadow-lg transition-all duration-300 flex flex-col justify-between ${
                  msg.sender === "user"
                    ? "rounded-tr-sm bg-white/5 border-primary/10"
                    : "rounded-tl-sm border-tertiary/10 ai-glow"
                }`}
              >
                <div className="text-sm leading-relaxed text-on-surface">
                  {msg.text}
                </div>

                {/* Suggested Look Action Button CTA */}
                {msg.suggestedOutfitId && (
                  <button
                    onClick={() => navigate(`/app/outfit/${msg.suggestedOutfitId}`)}
                    className="mt-4 px-4 py-2 bg-on-surface text-background text-[10px] uppercase font-bold tracking-widest rounded-lg flex items-center gap-1.5 hover:bg-tertiary hover:text-on-tertiary transition-all cursor-pointer shadow-md select-none self-start active:scale-95 border border-white/5"
                  >
                    <span className="material-symbols-outlined text-[14px]">checkroom</span>
                    View Suggested Look
                  </button>
                )}

                <span className="text-[10px] text-on-surface-variant block mt-2 text-right opacity-60 select-none">
                  {msg.time}
                </span>
              </div>
            </div>
          ))}

          {/* Luxury Bouncing Dot Typing Indicator Loader */}
          {isTyping && (
            <div className="flex items-start gap-4 animate-fade-in select-none">
              <div className="w-10 h-10 rounded-full bg-tertiary/20 flex items-center justify-center shrink-0 border border-tertiary/30 shadow-md">
                <span className="material-symbols-outlined text-tertiary text-xl animate-pulse">
                  auto_awesome
                </span>
              </div>
              <div className="glass-panel p-4 rounded-2xl rounded-tl-sm border-tertiary/10 ai-glow max-w-[80%] md:max-w-[70%] shadow-lg">
                <div className="flex items-center gap-1.5 py-1 px-2">
                  <span className="w-2 h-2 rounded-full bg-tertiary animate-bounce" style={{ animationDelay: "0s" }}></span>
                  <span className="w-2 h-2 rounded-full bg-tertiary/80 animate-bounce" style={{ animationDelay: "0.2s" }}></span>
                  <span className="w-2 h-2 rounded-full bg-tertiary/60 animate-bounce" style={{ animationDelay: "0.4s" }}></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Tactile Message Input */}
        <form
          onSubmit={handleSend}
          className="relative flex items-end gap-3 glass-panel rounded-2xl p-2.5 mb-2 focus-within:border-tertiary/40 transition-colors shadow-2xl"
        >
          <Link
            to="/app/camera"
            className="p-3 text-on-surface-variant hover:text-on-surface rounded-xl hover:bg-white/5 flex items-center justify-center transition-all shrink-0 border border-white/5"
            aria-label="Upload photo"
          >
            <span className="material-symbols-outlined text-2xl">
              add_photo_alternate
            </span>
          </Link>
          <input
            className="w-full bg-transparent border-none focus:outline-none focus:ring-0 py-3 text-sm text-on-surface placeholder-on-surface-variant/50 pr-4 disabled:opacity-50"
            placeholder={isTyping ? "Stylist is analyzing closet..." : "Ask your stylist..."}
            value={inputValue}
            disabled={isTyping}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className="p-3 bg-on-surface hover:bg-tertiary text-background hover:text-on-tertiary transition-all duration-300 rounded-xl flex items-center justify-center cursor-pointer shrink-0 shadow-md active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
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
