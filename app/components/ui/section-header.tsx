import { Ionicons } from '@expo/vector-icons';
import { View } from 'react-native';

import { colors, space } from '@/constants/design';
import { AppText } from './app-text';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

/** Icon + light short eyebrow + a rule line to the right, as a section separator. */
export function SectionHeader({ eyebrow, icon }: { eyebrow: string; icon: IconName }) {
  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: space.sm,
        paddingLeft: space.sm,
      }}>
      <Ionicons name={icon} size={15} color={colors.ink} />
      <AppText variant="label" color={colors.ink}>
        {eyebrow}
      </AppText>
      <View style={{ flex: 1, height: 1, backgroundColor: colors.border, marginLeft: space.xs }} />
    </View>
  );
}
