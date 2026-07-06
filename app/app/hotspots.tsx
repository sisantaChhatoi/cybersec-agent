import { View } from 'react-native';

import { AppText } from '@/components/ui/app-text';
import { BackHeader } from '@/components/ui/back-header';
import { Card } from '@/components/ui/card';
import { FeatureRow } from '@/components/ui/feature-row';
import { GradientPanel } from '@/components/ui/gradient-panel';
import { Screen } from '@/components/ui/screen';
import { colors, gradients, radius, space } from '@/constants/design';

const PREVIEW = [
  {
    icon: 'git-network-outline' as const,
    title: 'Fraud rings',
    description: 'Numbers, UPI IDs and mule accounts that keep showing up together.',
  },
  {
    icon: 'location-outline' as const,
    title: 'Hotspot cities',
    description: 'Where scam calls cluster, ranked so enforcement can prioritise.',
  },
  {
    icon: 'card-outline' as const,
    title: 'High-risk accounts',
    description: 'Mule accounts flagged across many independent reports.',
  },
];

export default function HotspotsScreen() {
  return (
    <Screen>
      <BackHeader title="Fraud hotspots" />

      <GradientPanel colors={gradients.heroLight}>
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: space.sm,
            alignSelf: 'flex-start',
            backgroundColor: colors.brandTint,
            paddingHorizontal: space.md,
            paddingVertical: 6,
            borderRadius: radius.pill,
          }}>
          <AppText variant="label" color={colors.brand}>
            Coming soon
          </AppText>
        </View>
        <AppText variant="title">Scam networks, mapped</AppText>
        <AppText variant="body">
          A live view of the fraud-intelligence graph — the rings, cities and accounts behind the
          calls we flag.
        </AppText>
      </GradientPanel>

      <View style={{ gap: space.md }}>
        <AppText variant="label">What you&apos;ll see</AppText>
        <Card>
          <View style={{ gap: space.lg }}>
            {PREVIEW.map((p, i) => (
              <View key={p.title} style={{ gap: space.lg }}>
                {i > 0 ? <View style={{ height: 1, backgroundColor: colors.border }} /> : null}
                <FeatureRow icon={p.icon} title={p.title} description={p.description} />
              </View>
            ))}
          </View>
        </Card>
      </View>

      <AppText variant="caption" style={{ textAlign: 'center' }}>
        These are signals for awareness, not accusations.
      </AppText>
    </Screen>
  );
}
