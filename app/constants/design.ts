// ──────────────────────────────────────────────────────────────────────────
// Design system tokens. Single source of truth for the app's look & feel.
// Principle: text stays near-monochrome (ink scale). Color is reserved for
// icons, primary actions, and the danger state — never decorative.
// ──────────────────────────────────────────────────────────────────────────

export const colors = {
  // Brand — aqua accent. Icon chips, links, small controls (NOT the primary button).
  brand: '#06B6D4',
  brandDark: '#0891B2',
  brandTint: '#CDEBF6',
  brandBorder: '#A9E0F1',

  // Ink — softened dark slate for headings + buttons (near-black was too harsh on the eye).
  ink: '#2C2A38',
  body: '#3B3A45',
  muted: '#6B6A78',
  faint: '#9E9DAB',

  // Surfaces — tinted neutral background so white cards read as raised, not flat.
  bg: '#ECEAF4',
  surface: '#FFFFFF',
  // Card fill — a gentle aqua tint (softer than before) so sections carry a hint of the accent.
  card: '#ECF3F8',
  surfaceAlt: '#F3F1FB',
  border: '#E5E2F0',
  borderStrong: '#D8D3EC',

  // Semantic — used sparingly, only where it carries meaning.
  danger: '#DC2626',
  dangerTint: '#FEF2F2',
  dangerBorder: '#FECACA',
  success: '#059669',
  successTint: '#ECFDF5',

  teal: '#0D9488',
  tealTint: '#CCFBF1',
  tealBorder: '#99F6E4',

  amber: '#D97706',
  amberTint: '#FEF3C7',
  amberBorder: '#FDE68A',

  // Companion accents — a curated set used alongside violet so icons/badges vary.
  cyan: '#0EA5E9',
  cyanTint: '#E3F4FD',

  pink: '#DB2777',
  pinkTint: '#FBE7F1',

  white: '#FFFFFF',
} as const;

// Spacing scale (4-pt grid). Reference everywhere instead of magic numbers.
export const space = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  huge: 40,
} as const;

export const radius = {
  sm: 10,
  md: 14,
  lg: 18,
  xl: 24,
  pill: 999,
} as const;

// Type scale. weight values are RN-accepted strings.
export const typography = {
  display: {
    fontFamily: 'Inter_700Bold',
    fontSize: 30,
    lineHeight: 36,
    letterSpacing: -0.6,
    color: colors.ink,
  },
  title: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 24,
    lineHeight: 30,
    letterSpacing: -0.4,
    color: colors.ink,
  },
  heading: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 18,
    lineHeight: 24,
    letterSpacing: -0.2,
    color: colors.ink,
  },
  subtitle: { fontFamily: 'Inter_600SemiBold', fontSize: 16, lineHeight: 22, color: colors.ink },
  body: { fontFamily: 'Inter_400Regular', fontSize: 15, lineHeight: 22, color: colors.body },
  bodyStrong: { fontFamily: 'Inter_600SemiBold', fontSize: 15, lineHeight: 22, color: colors.ink },
  caption: { fontFamily: 'Inter_400Regular', fontSize: 13, lineHeight: 19, color: colors.muted },
  label: {
    fontFamily: 'Inter_600SemiBold',
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.6,
    color: colors.muted,
    textTransform: 'uppercase',
  },
  link: { fontFamily: 'Inter_600SemiBold', fontSize: 14, lineHeight: 20, color: colors.brand },
} as const;

export const shadow = {
  card: {
    shadowColor: '#1B1B2F',
    shadowOpacity: 0.035,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 4 },
    elevation: 1,
  },
} as const;

export const gradients = {
  // Deep violet — for compact hero panels on secondary screens (white text).
  hero: ['#191430', '#5A2DB5', '#8B4FE6'],
  // Airy lavender → soft sky — fresh and cool, the main home hero (ink text).
  heroLight: ['#ECE9FE', '#E7EEFC', '#E3F4FC'],
  // Soft blue wash — tint concentrated in the top-left corner, the rest fades to the bg colour.
  card: ['#DDE9F5', '#ECEAF4', '#ECEAF4'],
} as const;

export type TypeVariant = keyof typeof typography;
