import { LinearGradient } from 'expo-linear-gradient';
import { StyleProp, View, ViewStyle } from 'react-native';

import { colors, gradients, radius, space } from '@/constants/design';

type Variant = 'default' | 'flat' | 'danger';
type Tint = 'tl' | 'tr' | 'bl' | 'br';

const BASE: ViewStyle = { borderRadius: radius.xl, padding: space.lg };

const TINT: Record<Tint, { start: { x: number; y: number }; end: { x: number; y: number } }> = {
  tl: { start: { x: 0, y: 0 }, end: { x: 1, y: 1 } },
  tr: { start: { x: 1, y: 0 }, end: { x: 0, y: 1 } },
  bl: { start: { x: 0, y: 1 }, end: { x: 1, y: 0 } },
  br: { start: { x: 1, y: 1 }, end: { x: 0, y: 0 } },
};

/** Standard surface container. Default/flat carry a borderless corner wash; `tint` sets which corner. */
export function Card({
  children,
  variant = 'default',
  tint = 'tl',
  style,
}: {
  children: React.ReactNode;
  variant?: Variant;
  tint?: Tint;
  style?: StyleProp<ViewStyle>;
}) {
  if (variant === 'danger') {
    return (
      <View
        style={[
          BASE,
          { backgroundColor: colors.dangerTint, borderWidth: 1, borderColor: colors.dangerBorder },
          style,
        ]}>
        {children}
      </View>
    );
  }
  const dir = TINT[tint];
  return (
    <LinearGradient colors={gradients.card} start={dir.start} end={dir.end} style={[BASE, style]}>
      {children}
    </LinearGradient>
  );
}
