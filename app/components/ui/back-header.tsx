import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, View } from 'react-native';

import { colors, space, type TypeVariant } from '@/constants/design';
import { AppText } from './app-text';

export function BackHeader({
  title,
  variant = 'heading',
}: {
  title: string;
  variant?: TypeVariant;
}) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.sm }}>
      <Pressable
        hitSlop={8}
        onPress={() => router.back()}
        style={({ pressed }) => ({ opacity: pressed ? 0.6 : 1, marginLeft: -4 })}>
        <Ionicons name="chevron-back" size={26} color={colors.ink} />
      </Pressable>
      <AppText variant={variant}>{title}</AppText>
    </View>
  );
}
