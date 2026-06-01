'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  MessageSquare, 
  FileText, 
  Image as ImageIcon, 
  Mic, 
  Code, 
  Settings, 
  Search,
  Menu,
  X,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { name: 'Chat', icon: MessageSquare, href: '/' },
  { name: 'PDF Intel', icon: FileText, href: '/pdf' },
  { name: 'Vision', icon: ImageIcon, href: '/vision' },
  { name: 'Voice', icon: Mic, href: '/voice' },
  { name: 'Code Assist', icon: Code, href: '/code' },
  { name: 'Search', icon: Search, href: '/search' },
];

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);
  const pathname = usePathname();

  return (
    <>
      {/* Mobile Toggle */}
      <button 
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-[var(--color-surface)] rounded-full hover:bg-[var(--color-surface-hover)] transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar Content */}
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div 
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="w-64 h-full bg-[var(--color-background)] flex flex-col flex-shrink-0 z-40 relative"
          >
            {/* Logo Area */}
            <div className="p-6 flex items-center gap-2">
              <Sparkles className="text-white" size={24} />
              <h1 className="text-xl font-medium tracking-tight text-white">Nova-AI</h1>
            </div>

            {/* Nav Links */}
            <div className="flex-1 overflow-y-auto py-6 px-3 flex flex-col gap-2 scrollbar-hide">
              <div className="text-xs font-semibold text-gray-400 mb-2 px-3 uppercase tracking-wider">Workspaces</div>
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link 
                    key={item.name} 
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-full transition-all duration-200 group ${
                      isActive 
                        ? 'bg-[var(--color-surface-hover)] text-white font-medium' 
                        : 'text-gray-400 hover:bg-[var(--color-surface)] hover:text-gray-200'
                    }`}
                  >
                    <Icon size={20} className={isActive ? 'text-white' : 'group-hover:text-gray-300 transition-colors'} />
                    <span className="text-[15px]">{item.name}</span>
                  </Link>
                );
              })}
            </div>

            {/* Bottom Section */}
            <div className="p-4">
              <Link 
                href="/settings"
                className="flex items-center gap-3 px-3 py-2.5 rounded-full text-gray-400 hover:bg-[var(--color-surface)] hover:text-gray-200 transition-colors"
              >
                <Settings size={20} />
                <span className="text-[15px]">Settings</span>
              </Link>
              
              {/* User Profile Mock */}
              <div className="mt-4 flex items-center gap-3 px-3 py-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-violet-500 flex items-center justify-center text-xs font-bold shadow-md">
                  AD
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">Aditya Gore</span>
                  <span className="text-xs text-gray-500">Premium Plan</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
