import { Ionicons } from '@expo/vector-icons';
import { View } from 'react-native';

import { colors, space } from '@/constants/design';
import type { CallSummary } from '@/lib/api';
import { AppText } from './app-text';

export function CallList({ calls }: { calls: CallSummary[] }) {
  return (
    <View style={{ gap: space.lg }}>
      {calls.map((c, i) => (
        <View key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: space.md }}>
          <Ionicons
            name={c.flagged ? 'warning' : 'checkmark-circle'}
            size={20}
            color={c.flagged ? colors.danger : colors.success}
          />
          <View style={{ flex: 1, gap: 1 }}>
            <AppText variant="bodyStrong" color={colors.body}>
              {c.flagged ? 'Scam flagged' : 'No scam detected'}
            </AppText>
            <AppText variant="caption">{subtitle(c)}</AppText>
          </View>
        </View>
      ))}
    </View>
  );
}

function subtitle(c: CallSummary): string {
  const when = new Date(c.started_at).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
  if (!c.ended_at) return `${when} · ongoing`;
  const secs = Math.max(0, Math.round((+new Date(c.ended_at) - +new Date(c.started_at)) / 1000));
  const dur = secs >= 60 ? `${Math.floor(secs / 60)}m ${secs % 60}s` : `${secs}s`;
  return `${when} · ${dur}`;
}
