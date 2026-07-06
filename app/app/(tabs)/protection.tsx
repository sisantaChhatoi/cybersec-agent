import { Ionicons } from '@expo/vector-icons';
import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, View } from 'react-native';

import { AppText } from '@/components/ui/app-text';
import { CallList } from '@/components/ui/call-list';
import { Card } from '@/components/ui/card';
import { FeatureBlock } from '@/components/ui/feature-block';
import { Screen } from '@/components/ui/screen';
import { SectionHeader } from '@/components/ui/section-header';
import { StatTiles } from '@/components/ui/stat-tiles';
import { TopBar } from '@/components/ui/top-bar';
import { colors, radius, space } from '@/constants/design';
import { api, ApiError, type CallStats, type CallSummary } from '@/lib/api';

const HOTSPOT_BULLETS = [
  'Live fraud rings and high-risk accounts',
  'Hotspot cities ranked by activity',
];

export default function ProtectionScreen() {
  const [stats, setStats] = useState<CallStats | null>(null);
  const [calls, setCalls] = useState<CallSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([api.getCallStats(), api.getRecentCalls(30)]);
      setStats(s);
      setCalls(c);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your activity.');
    } finally {
      setLoaded(true);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  return (
    <Screen>
      <TopBar title="Protection" />

      <View style={{ gap: space.md }}>
        <SectionHeader eyebrow="Your activity" icon="stats-chart-outline" />
        {!loaded ? (
          <View style={{ paddingVertical: space.xxl, alignItems: 'center' }}>
            <ActivityIndicator color={colors.brand} />
          </View>
        ) : error ? (
          <ErrorRow message={error} onRetry={load} />
        ) : (
          <StatTiles stats={stats} />
        )}
      </View>

      {loaded && !error && calls.length > 0 ? (
        <View style={{ gap: space.md }}>
          <SectionHeader eyebrow="All calls" icon="list-outline" />
          <Card>
            <CallList calls={calls} />
          </Card>
        </View>
      ) : loaded && !error ? (
        <View
          style={{
            backgroundColor: 'rgba(243,241,251,0.75)',
            borderRadius: radius.xl,
            padding: space.xl,
            alignItems: 'center',
            gap: space.sm,
          }}>
          <Ionicons name="call-outline" size={26} color={colors.muted} />
          <AppText variant="subtitle">No calls scanned yet</AppText>
          <AppText variant="caption" style={{ textAlign: 'center' }}>
            Add CallGuard to your next suspicious call and it will show up here.
          </AppText>
        </View>
      ) : null}

      <FeatureBlock
        tint="tr"
        eyebrow="Fraud intelligence"
        headerIcon="git-network-outline"
        haloIcon="map-outline"
        title="See the networks behind the scams."
        description="Explore the rings, mule accounts and hotspot cities our intelligence graph surfaces from thousands of reports."
        bullets={HOTSPOT_BULLETS}
        cta="View the map"
        // @ts-ignore route types regenerate on the next metro build
        onPress={() => router.push('/hotspots')}
      />
    </Screen>
  );
}

function ErrorRow({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View
      style={{
        padding: space.lg,
        borderRadius: radius.lg,
        backgroundColor: colors.dangerTint,
        borderWidth: 1,
        borderColor: colors.dangerBorder,
        gap: space.sm,
      }}>
      <AppText variant="bodyStrong" color={colors.danger}>
        {message}
      </AppText>
      <Pressable onPress={onRetry} style={({ pressed }) => ({ opacity: pressed ? 0.6 : 1 })}>
        <AppText variant="link">Try again</AppText>
      </Pressable>
    </View>
  );
}
