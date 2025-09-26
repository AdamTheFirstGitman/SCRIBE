/** @type {import('tailwindcss').Config} */

const { fontFamily } = require('tailwindcss/defaultTheme')

module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Colors optimized for Plume & Mimir
      colors: {
        // Primary brand colors
        plume: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#8B5CF6', // Main Plume color
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
        mimir: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#059669', // Main Mimir color
          600: '#047857',
          700: '#065f46',
          800: '#064e3b',
          900: '#022c22',
        },

        // Extended gray scale for dark theme
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
          950: '#0a0a0a', // Extra dark for main background
        },

        // Semantic colors
        success: {
          50: '#ecfdf5',
          500: '#10b981',
          600: '#059669',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        },
        info: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
        },
      },

      // Typography
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', ...fontFamily.sans],
        mono: ['Fira Code', 'SF Mono', 'Monaco', ...fontFamily.mono],
      },

      // Spacing for consistent rhythm
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },

      // Extended shadows for depth
      boxShadow: {
        'soft': '0 2px 8px 0 rgba(0, 0, 0, 0.1)',
        'medium': '0 4px 12px 0 rgba(0, 0, 0, 0.15)',
        'hard': '0 8px 24px 0 rgba(0, 0, 0, 0.2)',
        'glow': '0 0 20px rgba(139, 92, 246, 0.3)',
        'glow-mimir': '0 0 20px rgba(5, 150, 105, 0.3)',
      },

      // Animation and transitions
      transitionDuration: {
        '400': '400ms',
      },
      transitionTimingFunction: {
        'bounce-soft': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },

      // Custom animations
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        'recording': {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.1)', opacity: '0.8' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'thinking': {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1)' },
        }
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-in': 'slide-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
        'recording': 'recording 1.5s ease-in-out infinite',
        'thinking': 'thinking 1.4s ease-in-out infinite both',
      },

      // Custom borders
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },

      // Grid system
      gridTemplateColumns: {
        'sidebar': '300px 1fr',
        'chat': '1fr 300px',
      },

      // Z-index scale
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },

      // Backdrop blur
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [
    // Typography plugin for better text rendering
    require('@tailwindcss/typography'),

    // Forms plugin for better form styling
    require('@tailwindcss/forms')({
      strategy: 'class',
    }),

    // Container queries plugin
    require('@tailwindcss/container-queries'),

    // Custom utilities
    function({ addUtilities, theme }) {
      const newUtilities = {
        '.text-balance': {
          'text-wrap': 'balance',
        },
        '.scrollbar-hide': {
          '-ms-overflow-style': 'none',
          'scrollbar-width': 'none',
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        },
        '.scrollbar-thin': {
          'scrollbar-width': 'thin',
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: theme('colors.gray.100'),
          },
          '&::-webkit-scrollbar-thumb': {
            background: theme('colors.gray.300'),
            'border-radius': '3px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: theme('colors.gray.400'),
          },
        },
        '.glass': {
          'backdrop-filter': 'blur(10px)',
          'background-color': 'rgba(255, 255, 255, 0.1)',
        },
        '.glass-dark': {
          'backdrop-filter': 'blur(10px)',
          'background-color': 'rgba(0, 0, 0, 0.2)',
        },
      }
      addUtilities(newUtilities)
    },

    // Add safe area support for mobile
    function({ addUtilities }) {
      addUtilities({
        '.safe-top': {
          'padding-top': 'env(safe-area-inset-top)',
        },
        '.safe-bottom': {
          'padding-bottom': 'env(safe-area-inset-bottom)',
        },
        '.safe-left': {
          'padding-left': 'env(safe-area-inset-left)',
        },
        '.safe-right': {
          'padding-right': 'env(safe-area-inset-right)',
        },
      })
    },
  ],
}