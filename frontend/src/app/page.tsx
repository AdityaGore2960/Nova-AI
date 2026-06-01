'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Paperclip,
  Mic,
  Image as ImageIcon,
  Sparkles,
  Compass,
  Lightbulb,
  Play,
  Code,
  ChevronDown,
  Zap,
  Brain,
  AlertCircle,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

type Message = {
  id: string;
  role: 'user' | 'ai';
  content: string;
  model?: string;
  provider?: 'openai' | 'gemini';
  error?: boolean;
};

type AIModel = {
  id: string;
  name: string;
  provider: 'openai' | 'gemini';
  description: string;
  badge?: string;
};

// ─── Constants ────────────────────────────────────────────────────────────────

const AI_SERVICE_URL = 'http://localhost:8000';

const MODELS: AIModel[] = [
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai', description: "OpenAI's most capable model" },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai', description: 'Fast and affordable', badge: 'Default' },
];

const PROVIDER_COLORS: Record<string, string> = {
  openai: '#10a37f',
};

const SUGGESTIONS = [
  { icon: Compass, text: 'Suggest beautiful places to see on an upcoming road trip', color: 'text-orange-400' },
  { icon: Lightbulb, text: 'Briefly summarize this concept: urban planning', color: 'text-yellow-400' },
  { icon: Play, text: 'Find YouTube videos about how to make sourdough bread', color: 'text-red-400' },
  { icon: Code, text: 'Help me write a Python script to automate my daily tasks', color: 'text-blue-400' },
];

// ─── Model Selector ───────────────────────────────────────────────────────────

function ModelSelector({
  selected,
  onChange,
}: {
  selected: AIModel;
  onChange: (m: AIModel) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const ProviderIcon = Zap;

  return (
    <div ref={ref} className="relative">
      <button
        id="model-selector-btn"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-medium transition-all
                   bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)] text-gray-300 border border-[var(--color-border)]"
      >
        <ProviderIcon
          size={14}
          style={{ color: PROVIDER_COLORS[selected.provider] }}
        />
        <span>{selected.name}</span>
        <ChevronDown
          size={14}
          className={`text-gray-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full mt-2 left-0 z-50 w-72 rounded-2xl border border-[var(--color-border)]
                       bg-[#1a1b1d] shadow-2xl overflow-hidden"
          >
            {/* OpenAI models */}
            <div className="px-3 py-3">
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold mb-2 px-1">
                OpenAI Models
              </p>
              {MODELS.map((m) => (
                <ModelOption key={m.id} model={m} selected={selected} onSelect={(m) => { onChange(m); setOpen(false); }} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ModelOption({
  model,
  selected,
  onSelect,
}: {
  model: AIModel;
  selected: AIModel;
  onSelect: (m: AIModel) => void;
}) {
  const isActive = model.id === selected.id;
  const Icon = Zap;
  return (
    <button
      onClick={() => onSelect(model)}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors mb-0.5 ${
        isActive
          ? 'bg-[var(--color-surface-hover)] text-white'
          : 'text-gray-400 hover:bg-[var(--color-surface)] hover:text-gray-200'
      }`}
    >
      <Icon size={15} style={{ color: PROVIDER_COLORS[model.provider], flexShrink: 0 }} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{model.name}</span>
          {model.badge && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-[var(--color-primary-500)]/20 text-[var(--color-primary-500)] font-semibold flex-shrink-0">
              {model.badge}
            </span>
          )}
        </div>
        <p className="text-[11px] text-gray-500 truncate">{model.description}</p>
      </div>
      {isActive && <Brain size={14} className="text-[var(--color-primary-500)] flex-shrink-0" />}
    </button>
  );
}

// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const providerColor = msg.provider ? PROVIDER_COLORS[msg.provider] : undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      {msg.role === 'ai' && (
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
          {msg.error ? (
            <AlertCircle size={22} className="text-red-400" />
          ) : (
            <Sparkles size={22} style={{ color: providerColor || 'var(--color-primary-500)' }} />
          )}
        </div>
      )}

      <div
        className={`max-w-[80%] text-[15px] leading-relaxed whitespace-pre-wrap ${
          msg.role === 'user'
            ? 'bg-[var(--color-surface)] text-[#e3e3e3] px-6 py-3 rounded-3xl'
            : msg.error
            ? 'text-red-400 py-2'
            : 'text-[#e3e3e3] py-2'
        }`}
      >
        {msg.content}
        {msg.role === 'ai' && msg.model && !msg.error && (
          <p className="text-[11px] text-gray-600 mt-2 font-medium">{msg.model}</p>
        )}
      </div>
    </motion.div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<AIModel>(
    MODELS.find((m) => m.id === 'gpt-4o-mini') ?? MODELS[0]
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = input.trim();
    if (!prompt || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: prompt,
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${AI_SERVICE_URL}/api/v1/chat/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel.id,
          messages: updatedMessages.map((m) => ({
            role: m.role === 'ai' ? 'assistant' : 'user',
            content: m.content,
          })),
          temperature: 0.7,
          max_tokens: 2048,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: data.content,
        model: data.model,
        provider: data.provider,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to reach AI service. Is the AI server running?'}`,
        error: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="flex flex-col h-full relative bg-[var(--color-background)]">
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 sticky top-0 z-10 bg-[var(--color-background)]">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-medium text-gray-300">Nova-AI</h2>
          <ModelSelector selected={selectedModel} onChange={setSelectedModel} />
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-400 bg-[var(--color-surface)] px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Online
          </div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-violet-500 flex items-center justify-center text-xs font-bold text-white shadow-md">
            AD
          </div>
        </div>
      </header>

      {/* ── Chat Area ── */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 scrollbar-hide flex flex-col">
        <div className="max-w-4xl mx-auto w-full flex-1 flex flex-col pb-36">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col mt-12 md:mt-24">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-2 mb-12"
              >
                <h1 className="text-5xl font-semibold text-gradient bg-clip-text inline-block">
                  Hello, Aditya
                </h1>
                <h2 className="text-5xl font-semibold text-[#444746]">How can I help you today?</h2>
                <p className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                  Using
                  <span
                    className="font-medium px-2 py-0.5 rounded-lg text-xs"
                    style={{
                      background: `${PROVIDER_COLORS[selectedModel.provider]}22`,
                      color: PROVIDER_COLORS[selectedModel.provider],
                    }}
                  >
                    {selectedModel.name}
                  </span>
                  — switch models from the header
                </p>
              </motion.div>

              {/* Suggestion Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {SUGGESTIONS.map((card, i) => (
                  <div
                    key={i}
                    className="bg-[var(--color-surface)] p-4 rounded-2xl h-48 flex flex-col justify-between hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer"
                    onClick={() => setInput(card.text)}
                  >
                    <p className="text-[#e3e3e3] text-[15px] leading-relaxed">{card.text}</p>
                    <div className="self-end p-2 bg-[var(--color-background)] rounded-full">
                      <card.icon className={card.color} size={20} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-4 justify-start"
                >
                  <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <Sparkles
                      size={22}
                      className="animate-pulse"
                      style={{ color: PROVIDER_COLORS[selectedModel.provider] }}
                    />
                  </div>
                  <div className="py-2 flex items-center gap-1.5">
                    {[0, 150, 300].map((delay) => (
                      <div
                        key={delay}
                        className="w-2 h-2 rounded-full animate-bounce"
                        style={{
                          animationDelay: `${delay}ms`,
                          background: PROVIDER_COLORS[selectedModel.provider],
                        }}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* ── Input Area ── */}
      <div className="absolute bottom-0 w-full p-4 bg-[var(--color-background)]">
        <div className="max-w-4xl mx-auto relative">
          <form
            id="chat-form"
            onSubmit={handleSend}
            suppressHydrationWarning
            className="bg-[var(--color-surface)] p-2 rounded-full flex items-center gap-2 transition-all border border-transparent focus-within:bg-[var(--color-surface-hover)] pr-4 shadow-sm"
          >
            <button
              type="button"
              id="attach-btn"
              suppressHydrationWarning
              className="p-3 text-[#c4c7c5] hover:text-[#e3e3e3] transition-colors hover:bg-[var(--color-background)] rounded-full ml-1"
            >
              <Paperclip size={20} />
            </button>

            <input
              id="chat-input"
              type="text"
              value={input}
              suppressHydrationWarning
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Message ${selectedModel.name}…`}
              className="flex-1 bg-transparent border-none outline-none text-[#e3e3e3] placeholder-[#c4c7c5] py-4 px-2 text-[16px]"
            />

            <div className="flex items-center gap-2">
              <button
                id="mic-btn"
                type="button"
                suppressHydrationWarning
                className="p-3 text-[#c4c7c5] hover:text-[#e3e3e3] transition-colors hover:bg-[var(--color-background)] rounded-full"
              >
                <Mic size={20} />
              </button>
              {input.trim() ? (
                <button
                  id="send-btn"
                  type="submit"
                  disabled={isLoading}
                  suppressHydrationWarning
                  className="p-3 text-black bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] transition-colors rounded-full shadow-sm disabled:opacity-50"
                >
                  <Send size={20} />
                </button>
              ) : (
                <button
                  id="image-btn"
                  type="button"
                  suppressHydrationWarning
                  className="p-3 text-[#c4c7c5] hover:text-[#e3e3e3] transition-colors hover:bg-[var(--color-background)] rounded-full"
                >
                  <ImageIcon size={20} />
                </button>
              )}
            </div>
          </form>
          <div className="text-center mt-3 text-xs text-[#c4c7c5]">
            Nova-AI may display inaccurate info — always verify important responses.
          </div>
        </div>
      </div>
    </div>
  );
}
