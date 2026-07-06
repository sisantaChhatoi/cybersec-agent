import { Ionicons } from '@expo/vector-icons';
import Constants, { ExecutionEnvironment } from 'expo-constants';
import { router, Tabs } from 'expo-router';
import { useEffect, useRef } from 'react';

import { colors } from '@/constants/design';
import { api } from '@/lib/api';
import { getToken } from '@/lib/auth';
import { setAlert } from '@/lib/alert-store';

const isExpoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;

export default function TabLayout() {
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    getToken().then((token) => {
      if (!token) router.replace('/onboarding');
    });

    if (!isExpoGo) {
      // Dynamic require keeps expo-notifications out of the module graph in Expo Go.
      // Both modules run side effects on load that crash Expo Go SDK 53+.
      const { registerForPushToken } =
        require('@/lib/notifications') as typeof import('@/lib/notifications');
      const Notifications = require('expo-notifications') as typeof import('expo-notifications');

      registerForPushToken()
        .then((token) => (token ? api.registerPushToken(token) : null))
        .catch(() => null);

      const notifListener = Notifications.addNotificationReceivedListener((notification) => {
        const data = notification.request.content.data as Record<string, unknown>;
        if (data?.type === 'scam_alert') {
          setAlert({
            scam: true,
            confidence: (data.confidence as number) ?? 1,
            reason: (data.reason as string) ?? '',
            red_flags: (data.red_flags as string[]) ?? [],
            caller: (data.caller as string | null) ?? null,
            received_at: new Date().toISOString(),
          });
        }
      });

      const responseListener = Notifications.addNotificationResponseReceivedListener(
        (response) => {
          const data = response.notification.request.content.data as Record<string, unknown>;
          if (data?.type === 'scam_alert') {
            router.navigate('/(tabs)/alerts');
          }
        },
      );

      cleanupRef.current = () => {
        notifListener.remove();
        responseListener.remove();
      };
    }

    return () => cleanupRef.current?.();
  }, []);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.brand,
        tabBarInactiveTintColor: colors.faint,
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
        tabBarShowLabel: false,
      }}>
      <Tabs.Screen
        name="index"
        options={{
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? 'home' : 'home-outline'} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons
              name={focused ? 'chatbubble-ellipses' : 'chatbubble-ellipses-outline'}
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="protection"
        options={{
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons
              name={focused ? 'shield-checkmark' : 'shield-checkmark-outline'}
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="alerts"
        options={{ href: null }}
      />
    </Tabs>
  );
}
