import { View } from 'react-native';

import { colors, radius, space } from '@/constants/design';
import type { CallStats } from '@/lib/api';
import { AppText } from './app-text';

type Tone = 'brand' | 'danger' | 'success';

export function StatTiles({ stats }: { stats: CallStats | null }) {
  return (
    <View style={{ flexDirection: 'row', gap: space.md }}>
      <StatTile tone="brand" value={stats?.scanned ?? 0} label="Calls scanned" />
      <StatTile tone="danger" value={stats?.threats_blocked ?? 0} label="Threats flagged" />
      <StatTile tone="success" value={stats?.marked_safe ?? 0} label="Marked safe" />
    </View>
  );
}

function StatTile({ tone, value, label }: { tone: Tone; value: number; label: string }) {
  const fg = { brand: colors.ink, danger: colors.danger, success: colors.success }[tone];
  return (
    <View
      style={{
        flex: 1,
        gap: space.xs,
        padding: space.lg,
        borderRadius: radius.lg,
        backgroundColor: 'rgba(243,241,251,0.75)',
        alignItems: 'center',
      }}>
      <AppText variant="title" color={fg} style={{ fontSize: 26, lineHeight: 30 }}>
        {value}
      </AppText>
      <AppText variant="caption" style={{ textAlign: 'center' }}>
        {label}
      </AppText>
    </View>
  );
}
