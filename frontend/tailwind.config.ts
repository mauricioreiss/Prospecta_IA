import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Design System - 40+ demographic friendly
        primary: {
          DEFAULT: '#1E3A5F', // Deep Navy
          light: '#2D4A6F',
          dark: '#152B47',
        },
        accent: {
          DEFAULT: '#3B82F6', // Blue CTA
          hover: '#2563EB',
        },
        success: '#22C55E',
        warning: '#F59E0B',
        error: '#EF4444',
        surface: '#F8FAFC',
        text: {
          DEFAULT: '#1E293B',
          muted: '#64748B',
        },
        // Lead temperature colors
        gold: '#FFD700',
        silver: '#C0C0C0',
        bronze: '#CD7F32',
      },
      fontSize: {
        // Larger base for 40+ readability
        base: '18px',
        lg: '20px',
        xl: '24px',
        '2xl': '30px',
        '3xl': '36px',
      },
      spacing: {
        // Larger touch targets
        'btn': '52px',
      },
      borderRadius: {
        'card': '12px',
      },
    },
  },
  plugins: [],
}

export default config
