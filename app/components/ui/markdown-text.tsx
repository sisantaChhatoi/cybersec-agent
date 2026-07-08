import { Text, View } from 'react-native';

import { colors, space } from '@/constants/design';

type Segment = { text: string; bold: boolean };

function parseInline(line: string): Segment[] {
  const segments: Segment[] = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) segments.push({ text: line.slice(last, m.index), bold: false });
    segments.push({ text: m[1], bold: true });
    last = m.index + m[0].length;
  }
  if (last < line.length) segments.push({ text: line.slice(last), bold: false });
  return segments;
}

function InlineLine({ text, baseColor }: { text: string; baseColor: string }) {
  const segs = parseInline(text);
  return (
    <>
      {segs.map((s, i) => (
        <Text
          key={i}
          style={{
            fontWeight: s.bold ? '700' : '400',
            color: baseColor,
            fontSize: 14,
            lineHeight: 22,
          }}>
          {s.text}
        </Text>
      ))}
    </>
  );
}

interface Props {
  content: string;
  color?: string;
}

export function MarkdownText({ content, color = colors.ink }: Props) {
  const lines = content.split('\n');
  const nodes: React.ReactNode[] = [];

  lines.forEach((raw, i) => {
    const line = raw.trimEnd();

    // ### heading
    const hMatch = line.match(/^#{1,3}\s+(.+)/);
    if (hMatch) {
      nodes.push(
        <Text
          key={i}
          style={{ fontWeight: '700', fontSize: 14, color, lineHeight: 22, marginTop: i > 0 ? space.sm : 0 }}>
          {hMatch[1]}
        </Text>,
      );
      return;
    }

    // - bullet or * bullet
    const bMatch = line.match(/^[-*]\s+(.+)/);
    if (bMatch) {
      nodes.push(
        <View key={i} style={{ flexDirection: 'row', gap: 6, paddingLeft: space.sm }}>
          <Text style={{ color, fontSize: 14, lineHeight: 22 }}>{'•'}</Text>
          <Text style={{ flex: 1, fontSize: 14, lineHeight: 22, color }}>
            <InlineLine text={bMatch[1]} baseColor={color} />
          </Text>
        </View>,
      );
      return;
    }

    // numbered list  1. text
    const nMatch = line.match(/^(\d+)\.\s+(.+)/);
    if (nMatch) {
      nodes.push(
        <View key={i} style={{ flexDirection: 'row', gap: 6, paddingLeft: space.sm }}>
          <Text style={{ color, fontSize: 14, lineHeight: 22, fontWeight: '600' }}>
            {nMatch[1]}.
          </Text>
          <Text style={{ flex: 1, fontSize: 14, lineHeight: 22, color }}>
            <InlineLine text={nMatch[2]} baseColor={color} />
          </Text>
        </View>,
      );
      return;
    }

    // blank line — small gap
    if (line.trim() === '') {
      nodes.push(<View key={i} style={{ height: space.xs }} />);
      return;
    }

    // normal paragraph line
    nodes.push(
      <Text key={i} style={{ fontSize: 14, lineHeight: 22, color }}>
        <InlineLine text={line} baseColor={color} />
      </Text>,
    );
  });

  return <View style={{ gap: 2 }}>{nodes}</View>;
}
