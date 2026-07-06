import { LinearGradient } from 'expo-linear-gradient';
import { StyleProp, ViewStyle } from 'react-native';

import { radius, space } from '@/constants/design';

export function GradientPanel({
  colors: stops,
  children,
  style,
}: {
  colors: readonly [string, string, ...string[]];
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <LinearGradient
      colors={stops}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[{ borderRadius: radius.xl, padding: space.xxl, gap: space.lg }, style]}>
      {children}
    </LinearGradient>
  );
}
