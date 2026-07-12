import { Ionicons } from '@expo/vector-icons';
import { fetch } from 'expo/fetch';
import * as SecureStore from 'expo-secure-store';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  FlatList,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import Markdown from 'react-native-markdown-display';

import { AppText } from '@/components/ui/app-text';
import { API_URL } from '@/constants/config';
import { colors, radius, space } from '@/constants/design';
import { api, type ChatSummary } from '@/lib/api';
import { getToken } from '@/lib/auth';

type Msg = { id: string; role: 'user' | 'assistant'; content: string };

const DRAWER_WIDTH = Math.min(300, Dimensions.get('window').width * 0.82);
const LAST_CHAT_KEY = 'last_chat_id';

export default function ChatScreen() {
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [loadingChats, setLoadingChats] = useState(false);
  const [showIntro, setShowIntro] = useState(false);
  const [drawerMounted, setDrawerMounted] = useState(false);
  const flatListRef = useRef<FlatList<Msg>>(null);
  const drawerX = useRef(new Animated.Value(-DRAWER_WIDTH)).current;

  const loadChats = useCallback(async () => {
    setLoadingChats(true);
    try {
      setChats(await api.listChats());
    } catch {
      // silent
    } finally {
      setLoadingChats(false);
    }
  }, []);

  const openChat = useCallback(async (chatId: string) => {
    try {
      const detail = await api.getChat(chatId);
      setMessages(
        detail.messages.map((m, i) => ({
          id: `${chatId}-${i}`,
          role: m.role === 'agent' ? 'assistant' : 'user',
          content: m.message,
        })),
      );
      setActiveChatId(chatId);
      await SecureStore.setItemAsync(LAST_CHAT_KEY, chatId);
    } catch {
      // chat may no longer exist; leave a fresh new chat
    }
  }, []);

  useEffect(() => {
    SecureStore.getItemAsync('chat_intro_seen').then((v) => {
      if (!v) setShowIntro(true);
    });
    SecureStore.getItemAsync(LAST_CHAT_KEY).then((id) => {
      if (id) openChat(id);
    });
  }, [openChat]);

  const openDrawer = () => {
    loadChats();
    setDrawerMounted(true);
    Animated.timing(drawerX, { toValue: 0, duration: 220, useNativeDriver: true }).start();
  };

  const closeDrawer = () => {
    Animated.timing(drawerX, {
      toValue: -DRAWER_WIDTH,
      duration: 200,
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished) setDrawerMounted(false);
    });
  };

  const dismissIntro = () => {
    SecureStore.setItemAsync('chat_intro_seen', '1');
    setShowIntro(false);
  };

  const startNewChat = () => {
    setActiveChatId(null);
    setMessages([]);
    closeDrawer();
  };

  const selectChat = (id: string) => {
    openChat(id);
    closeDrawer();
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput('');

    const userMsg: Msg = { id: `u-${Date.now()}`, role: 'user', content: text };
    const assistantMsg: Msg = { id: `a-${Date.now()}`, role: 'assistant', content: '' };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    try {
      let chatId = activeChatId;
      if (!chatId) {
        const chat = await api.createChat();
        chatId = chat.chat_id;
        setActiveChatId(chatId);
        await SecureStore.setItemAsync(LAST_CHAT_KEY, chatId);
      }

      const token = await getToken();
      const res = await fetch(`${API_URL}/chatbot/chats/${chatId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let assembled = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const chunk = line.slice(6).replace(/\r$/, '');
              if (chunk && chunk !== '[DONE]') {
                assembled += JSON.parse(chunk);
                setMessages((prev) => [
                  ...prev.slice(0, -1),
                  { ...assistantMsg, content: assembled },
                ]);
              }
            }
          }
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { ...assistantMsg, content: 'Something went wrong. Please try again.' },
      ]);
    } finally {
      setStreaming(false);
    }
  };

  return (
    <SafeAreaView style={styles.root} edges={['top']}>
      <View style={styles.header}>
        <Pressable
          hitSlop={8}
          onPress={openDrawer}
          style={({ pressed }) => ({ opacity: pressed ? 0.6 : 1 })}>
          <Ionicons name="menu" size={26} color={colors.ink} />
        </Pressable>
        <AppText variant="heading" style={{ flex: 1, marginLeft: space.md }}>
          Chat
        </AppText>
        <Pressable
          onPress={startNewChat}
          style={({ pressed }) => [styles.newBtn, { opacity: pressed ? 0.8 : 1 }]}>
          <Ionicons name="create-outline" size={18} color={colors.ink} />
          <AppText variant="bodyStrong" color={colors.ink}>
            New
          </AppText>
        </Pressable>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={8}>
        {messages.length === 0 ? (
          <View style={styles.empty}>
            <Ionicons name="chatbubble-ellipses-outline" size={48} color={colors.faint} />
            <AppText variant="subtitle" color={colors.muted}>
              Ask anything suspicious
            </AppText>
            <AppText variant="caption" style={{ textAlign: 'center' }}>
              Describe a call, message, or number you&apos;re unsure about and get a risk
              assessment.
            </AppText>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(m) => m.id}
            contentContainerStyle={styles.messageList}
            onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: false })}
            renderItem={({ item }) => <MessageBubble msg={item} />}
          />
        )}

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Describe what's suspicious..."
            placeholderTextColor={colors.faint}
            multiline
            maxLength={1000}
            onSubmitEditing={sendMessage}
          />
          <Pressable
            onPress={sendMessage}
            disabled={!input.trim() || streaming}
            style={({ pressed }) => [
              styles.sendBtn,
              { opacity: !input.trim() || streaming ? 0.4 : pressed ? 0.7 : 1 },
            ]}>
            {streaming ? (
              <ActivityIndicator size="small" color={colors.white} />
            ) : (
              <Ionicons name="arrow-up" size={18} color={colors.white} />
            )}
          </Pressable>
        </View>
      </KeyboardAvoidingView>

      {drawerMounted ? (
        <ChatDrawer
          chats={chats}
          loading={loadingChats}
          activeId={activeChatId}
          translateX={drawerX}
          onSelect={selectChat}
          onNewChat={startNewChat}
          onClose={closeDrawer}
        />
      ) : null}

      <ChatIntroModal visible={showIntro} onClose={dismissIntro} />
    </SafeAreaView>
  );
}

function ChatDrawer({
  chats,
  loading,
  activeId,
  translateX,
  onSelect,
  onNewChat,
  onClose,
}: {
  chats: ChatSummary[];
  loading: boolean;
  activeId: string | null;
  translateX: Animated.Value;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onClose: () => void;
}) {
  const backdropOpacity = translateX.interpolate({
    inputRange: [-DRAWER_WIDTH, 0],
    outputRange: [0, 1],
  });
  return (
    <View style={StyleSheet.absoluteFill}>
      <Animated.View
        style={[StyleSheet.absoluteFill, styles.backdrop, { opacity: backdropOpacity }]}>
        <Pressable style={{ flex: 1 }} onPress={onClose} />
      </Animated.View>
      <Animated.View style={[styles.drawer, { transform: [{ translateX }] }]}>
        <SafeAreaView style={{ flex: 1 }} edges={['top']}>
          <View style={styles.drawerHead}>
            <AppText variant="heading">Your chats</AppText>
          </View>
          <Pressable onPress={onNewChat} style={styles.drawerNew}>
            <Ionicons name="create-outline" size={18} color={colors.ink} />
            <AppText variant="bodyStrong" color={colors.ink}>
              New chat
            </AppText>
          </Pressable>
          {loading ? (
            <View style={styles.drawerEmpty}>
              <ActivityIndicator color={colors.brand} />
            </View>
          ) : chats.length === 0 ? (
            <View style={styles.drawerEmpty}>
              <AppText variant="caption">No chats yet</AppText>
            </View>
          ) : (
            <FlatList
              data={chats}
              keyExtractor={(c) => c.chat_id}
              contentContainerStyle={{ padding: space.md, gap: space.xs }}
              renderItem={({ item }) => (
                <Pressable
                  onPress={() => onSelect(item.chat_id)}
                  style={({ pressed }) => [
                    styles.drawerRow,
                    item.chat_id === activeId && styles.drawerRowActive,
                    { opacity: pressed ? 0.7 : 1 },
                  ]}>
                  <Ionicons name="chatbubble-outline" size={17} color={colors.muted} />
                  <AppText
                    variant="bodyStrong"
                    color={colors.body}
                    numberOfLines={1}
                    style={{ flex: 1 }}>
                    {item.title}
                  </AppText>
                </Pressable>
              )}
            />
          )}
        </SafeAreaView>
      </Animated.View>
    </View>
  );
}

function ChatIntroModal({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const bullets = [
    'Speaks 22 Indian languages — Hindi, English, Hinglish and more',
    'Share a suspicious link to check it for fraud',
    'Powered by our fraud-intelligence graph',
  ];
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.introBackdrop}>
        <View style={styles.introCard}>
          <Ionicons name="chatbubbles-outline" size={30} color={colors.brandDark} />
          <AppText variant="heading">Your fraud assistant</AppText>
          <AppText variant="body" color={colors.body}>
            Describe a call or message, or share a suspicious link, and get an instant,
            plain-language risk read.
          </AppText>
          <View style={{ gap: space.sm, alignSelf: 'stretch' }}>
            {bullets.map((b) => (
              <View key={b} style={{ flexDirection: 'row', alignItems: 'center', gap: space.sm }}>
                <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                <AppText variant="caption" color={colors.body} style={{ flex: 1 }}>
                  {b}
                </AppText>
              </View>
            ))}
          </View>
          <AppText variant="caption" style={{ alignSelf: 'stretch' }}>
            It never asks for your OTP, PIN or password.
          </AppText>
          <Pressable onPress={onClose} style={styles.introBtn}>
            <AppText variant="bodyStrong" color={colors.white}>
              Got it
            </AppText>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

function MessageBubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === 'user';
  if (isUser) {
    return (
      <View style={[styles.bubble, styles.bubbleUser]}>
        <AppText variant="body" color={colors.white}>
          {msg.content || '…'}
        </AppText>
      </View>
    );
  }
  const content = (msg.content || '…').replace(/<br\s*\/?>/gi, '\n');
  return (
    <View style={styles.assistantBlock}>
      <Markdown style={mdStyles}>{content}</Markdown>
    </View>
  );
}

const mdStyles = {
  body: { color: colors.ink, fontSize: 15, lineHeight: 22 },
  paragraph: { color: colors.ink, fontSize: 15, lineHeight: 22, marginTop: 0, marginBottom: 6 },
  strong: { color: colors.ink, fontWeight: '600' as const },
  em: { color: colors.body },
  heading1: { color: colors.ink, fontSize: 18, fontWeight: '700' as const, marginBottom: 6 },
  heading2: { color: colors.ink, fontSize: 16, fontWeight: '700' as const, marginBottom: 4 },
  heading3: { color: colors.ink, fontSize: 15, fontWeight: '600' as const, marginBottom: 4 },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2 },
  code_inline: {
    backgroundColor: colors.surfaceAlt,
    color: colors.brand,
    borderRadius: 4,
    paddingHorizontal: 4,
    fontSize: 13,
  },
  fence: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.sm,
    padding: space.md,
    marginVertical: 6,
  },
  code_block: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.sm,
    padding: space.md,
    fontSize: 13,
    color: colors.ink,
  },
  link: { color: colors.brand },
  blockquote: {
    borderLeftWidth: 3,
    borderLeftColor: colors.brand,
    paddingLeft: space.md,
    marginVertical: 4,
    backgroundColor: colors.surfaceAlt,
    borderRadius: 4,
  },
};

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: space.xl,
    paddingTop: space.md,
    paddingBottom: space.sm,
  },
  newBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.xs,
    paddingHorizontal: space.md,
    paddingVertical: 7,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.borderStrong,
  },
  backdrop: { backgroundColor: 'rgba(0,0,0,0.4)' },
  drawer: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    width: DRAWER_WIDTH,
    backgroundColor: colors.surface,
    borderRightWidth: 1,
    borderRightColor: colors.border,
  },
  drawerHead: { paddingHorizontal: space.lg, paddingTop: space.md, paddingBottom: space.sm },
  drawerNew: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
    marginHorizontal: space.md,
    marginBottom: space.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.md,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceAlt,
  },
  drawerEmpty: { padding: space.xl, alignItems: 'center' },
  drawerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
    paddingHorizontal: space.md,
    paddingVertical: space.md,
    borderRadius: radius.md,
  },
  drawerRowActive: { backgroundColor: colors.surfaceAlt },
  introBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    padding: space.xl,
  },
  introCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: space.xxl,
    gap: space.md,
    alignItems: 'flex-start',
  },
  introBtn: {
    alignSelf: 'stretch',
    alignItems: 'center',
    backgroundColor: colors.brand,
    paddingVertical: 13,
    borderRadius: radius.md,
    marginTop: space.xs,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: space.xxl,
    gap: space.lg,
  },
  messageList: { padding: space.lg, gap: space.md, paddingBottom: space.xxl },
  bubble: {
    maxWidth: '80%',
    paddingHorizontal: space.lg,
    paddingVertical: space.md,
    borderRadius: radius.lg,
  },
  bubbleUser: { alignSelf: 'flex-end', backgroundColor: colors.brand, borderBottomRightRadius: 4 },
  assistantBlock: {
    alignSelf: 'stretch',
    paddingVertical: space.xs,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: space.sm,
    paddingHorizontal: space.lg,
    paddingVertical: space.md,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  input: {
    flex: 1,
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    fontSize: 15,
    color: colors.ink,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: colors.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
