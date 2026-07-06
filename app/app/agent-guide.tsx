import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import { useState } from 'react';
import { Linking, Pressable, View } from 'react-native';

import { AppText } from '@/components/ui/app-text';
import { BackHeader } from '@/components/ui/back-header';
import { Card } from '@/components/ui/card';
import { GradientPanel } from '@/components/ui/gradient-panel';
import { IconBadge } from '@/components/ui/icon-badge';
import { Screen } from '@/components/ui/screen';
import { AGENT_PHONE_NO } from '@/constants/app';
import { colors, gradients, radius, space } from '@/constants/design';

const DISPLAY_NO = AGENT_PHONE_NO.replace(/(\+\d)(\d{3})(\d{3})(\d{4})/, '$1 $2 $3 $4');

const STEPS = [
  { title: 'On a call that feels off, tap Add call', description: 'Keep the caller on the line.' },
  { title: `Dial CallGuard — ${DISPLAY_NO}`, description: 'Or paste the number you copied above.' },
  { title: 'Tap Merge calls', description: 'The guard joins the line and starts listening.' },
  {
    title: 'Keep talking',
    description: 'The moment it hears a scam pattern, you get an instant alert.',
  },
];

export default function AgentGuideScreen() {
  return (
    <Screen>
      <BackHeader title="Try the agent" />
      <DialCard />
      <Steps />
      <PrivacyNote />
    </Screen>
  );
}

function DialCard() {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await Clipboard.setStringAsync(AGENT_PHONE_NO);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <GradientPanel colors={gradients.heroLight}>
      <AppText variant="label">Add the guard to a call</AppText>
      <AppText variant="title" color={colors.body}>
        {DISPLAY_NO}
      </AppText>
      <View style={{ flexDirection: 'row', gap: space.md }}>
        <Pressable
          onPress={() => Linking.openURL(`tel:${AGENT_PHONE_NO}`)}
          style={({ pressed }) => ({
            flexDirection: 'row',
            alignItems: 'center',
            gap: space.sm,
            backgroundColor: colors.brand,
            paddingVertical: 12,
            paddingHorizontal: space.xl,
            borderRadius: radius.md,
            opacity: pressed ? 0.85 : 1,
          })}>
          <Ionicons name="call" size={18} color={colors.white} />
          <AppText variant="bodyStrong" color={colors.white}>
            Call now
          </AppText>
        </Pressable>
        <Pressable
          onPress={copy}
          style={({ pressed }) => ({
            flexDirection: 'row',
            alignItems: 'center',
            gap: space.sm,
            backgroundColor: colors.surface,
            borderWidth: 1,
            borderColor: colors.border,
            paddingVertical: 12,
            paddingHorizontal: space.xl,
            borderRadius: radius.md,
            opacity: pressed ? 0.85 : 1,
          })}>
          <Ionicons name={copied ? 'checkmark' : 'copy-outline'} size={18} color={colors.muted} />
          <AppText variant="bodyStrong" color={colors.body}>
            {copied ? 'Copied' : 'Copy'}
          </AppText>
        </Pressable>
      </View>
    </GradientPanel>
  );
}

function Steps() {
  return (
    <Card>
      <View style={{ gap: space.xl }}>
        {STEPS.map((s, i) => (
          <View
            key={s.title}
            style={{ flexDirection: 'row', alignItems: 'flex-start', gap: space.md }}>
            <View
              style={{
                width: 28,
                height: 28,
                borderRadius: radius.pill,
                backgroundColor: colors.brandTint,
                alignItems: 'center',
                justifyContent: 'center',
              }}>
              <AppText variant="bodyStrong" color={colors.brand}>
                {i + 1}
              </AppText>
            </View>
            <View style={{ flex: 1, gap: 2, paddingTop: 2 }}>
              <AppText variant="subtitle">{s.title}</AppText>
              <AppText variant="caption">{s.description}</AppText>
            </View>
          </View>
        ))}
      </View>
    </Card>
  );
}

function PrivacyNote() {
  return (
    <Card variant="flat">
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.md }}>
        <IconBadge name="lock-closed-outline" tone="success" size="sm" />
        <AppText variant="caption" style={{ flex: 1 }}>
          CallGuard listens only to flag scams. You add it yourself, and nothing else leaves your
          call.
        </AppText>
      </View>
    </Card>
  );
}
