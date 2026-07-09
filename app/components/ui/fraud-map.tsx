import { View } from 'react-native';

import { AppText } from '@/components/ui/app-text';
import { colors, radius, space } from '@/constants/design';
import type { FraudHotspot } from '@/lib/api';

export function FraudMap({ hotspots }: { hotspots: FraudHotspot[] }) {
  if (hotspots.filter((h) => h.lat && h.lon).length === 0) return null;

  // Needs react-native-webview — placeholder until wired in native build
  return (
    <View
      style={{
        height: 200,
        borderRadius: radius.xl,
        backgroundColor: colors.card,
        alignItems: 'center',
        justifyContent: 'center',
        gap: space.sm,
      }}>
      <AppText variant="caption" style={{ color: colors.muted, textAlign: 'center' }}>
        {hotspots.length} hotspot{hotspots.length !== 1 ? 's' : ''} detected — map view coming soon
      </AppText>
    </View>
  );
}
