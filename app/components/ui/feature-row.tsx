import { Ionicons } from '@expo/vector-icons';
import { View } from 'react-native';

import { colors, space } from '@/constants/design';
import { AppText } from './app-text';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

export function FeatureRow({
  icon,
  title,
  description,
}: {
  icon: IconName;
  title: string;
  description: string;
}) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: space.md }}>
      <Ionicons name={icon} size={22} color={colors.muted} style={{ marginTop: 1 }} />
      <View style={{ flex: 1, gap: 2 }}>
        <AppText variant="subtitle" color={colors.body}>
          {title}
        </AppText>
        <AppText variant="caption">{description}</AppText>
      </View>
    </View>
  );
}
