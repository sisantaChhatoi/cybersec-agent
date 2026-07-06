import { Ionicons } from '@expo/vector-icons';
import { Pressable, View } from 'react-native';

import { colors, radius, space } from '@/constants/design';
import { AppText } from './app-text';
import { Card } from './card';
import { SectionHeader } from './section-header';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

export function FeatureBlock({
  eyebrow,
  headerIcon,
  haloIcon,
  title,
  description,
  bullets,
  cta,
  tint,
  onPress,
}: {
  eyebrow: string;
  headerIcon: IconName;
  haloIcon: IconName;
  title: string;
  description: string;
  bullets: string[];
  cta: string;
  tint: React.ComponentProps<typeof Card>['tint'];
  onPress: () => void;
}) {
  return (
    <View style={{ gap: space.md }}>
      <SectionHeader eyebrow={eyebrow} icon={headerIcon} />
      <Card tint={tint}>
        <View style={{ gap: space.lg }}>
          <Ionicons name={haloIcon} size={30} color={colors.brandDark} />
          <View style={{ gap: 4 }}>
            <AppText variant="heading">{title}</AppText>
            <AppText variant="body">{description}</AppText>
          </View>
          <View style={{ gap: space.sm }}>
            {bullets.map((b) => (
              <View key={b} style={{ flexDirection: 'row', alignItems: 'center', gap: space.sm }}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <AppText variant="caption" color={colors.body} style={{ flex: 1 }}>
                  {b}
                </AppText>
              </View>
            ))}
          </View>
          <Pressable
            onPress={onPress}
            style={({ pressed }) => ({
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'center',
              alignSelf: 'flex-start',
              gap: space.sm,
              backgroundColor: colors.brand,
              paddingVertical: 12,
              paddingHorizontal: space.xl,
              borderRadius: radius.md,
              opacity: pressed ? 0.85 : 1,
            })}>
            <AppText variant="bodyStrong" color={colors.white}>
              {cta}
            </AppText>
            <Ionicons name="arrow-forward" size={16} color={colors.white} />
          </Pressable>
        </View>
      </Card>
    </View>
  );
}
