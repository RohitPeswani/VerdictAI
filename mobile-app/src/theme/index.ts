/**
 * VerdictAI Design System & Theme Tokens
 * Aligned with Visily mobile wireframe color palette (Mayank Jayswal)
 */

export const Colors = {
  // Primary Brand
  primary: '#3B82F6',       // Blue 500 - CTAs, active tabs, links
  primaryDark: '#1D4ED8',   // Blue 700 - pressed states
  primaryLight: '#93C5FD',  // Blue 300 - highlights, icons on dark bg

  // Background Layer System
  bgDeep: '#0A0E1A',        // Near-black — root background
  bgCard: '#131929',        // Dark navy — cards, modals
  bgSurface: '#1C2440',     // Slightly lighter — input fields, list items
  bgElevated: '#243058',    // For popups, bottom sheets

  // Text
  textPrimary: '#F1F5F9',   // Off-white — headings, primary content
  textSecondary: '#94A3B8', // Slate 400 — subtext, labels
  textMuted: '#4B5563',     // Gray 600 — placeholders, disabled
  textInvert: '#0A0E1A',    // For use on light/colored backgrounds

  // Status Colors (mirror DisputeStatus)
  statusSubmitted: '#F59E0B',     // Amber — SUBMITTED, EVIDENCE_PENDING
  statusInProgress: '#3B82F6',    // Blue — EVIDENCE_INGESTED, IN_ANALYSIS
  statusEvaluated: '#8B5CF6',     // Violet — SCORING_EVALUATED
  statusResolved: '#10B981',      // Emerald — AUTO_RESOLVED, CLOSED
  statusManual: '#F97316',        // Orange — MANUAL_REVIEW_QUEUE
  statusRejected: '#EF4444',      // Red — REJECTED
  statusOverridden: '#6366F1',    // Indigo — ADMIN_OVERRIDDEN

  // UI Utilities
  border: '#1E2D4A',
  divider: '#1C2440',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',

  // Tab Bar
  tabActive: '#3B82F6',
  tabInactive: '#4B5563',
  tabBackground: '#0F1624',
} as const;

export const Typography = {
  // Font sizes (sp scale)
  xs: 11,
  sm: 13,
  base: 15,
  md: 17,
  lg: 20,
  xl: 24,
  '2xl': 28,
  '3xl': 34,

  // Font weights
  regular: '400' as const,
  medium: '500' as const,
  semibold: '600' as const,
  bold: '700' as const,
  extrabold: '800' as const,

  // Line heights
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.7,
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 56,
};

export const Radius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
};

export const Shadow = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  modal: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 12,
  },
};
