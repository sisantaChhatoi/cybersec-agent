import { Platform, View } from 'react-native';

import { AppText } from '@/components/ui/app-text';
import { colors, radius, space } from '@/constants/design';
import type { FraudHotspot } from '@/lib/api';

const RISK_HEX: Record<string, string> = {
  high: '#DC2626',
  medium: '#D97706',
  low: '#059669',
};

function buildMapHtml(hotspots: FraudHotspot[]): string {
  const markers = hotspots
    .filter((h) => h.lat && h.lon)
    .map((h) => {
      const color = RISK_HEX[h.risk_level] ?? '#06B6D4';
      const radius = h.incident_count > 5 ? 18 : h.incident_count > 2 ? 12 : 8;
      const popup = `
        <b>${h.region}</b><br/>
        ${h.state}<br/>
        ${h.incident_count} report${h.incident_count !== 1 ? 's' : ''}<br/>
        ${h.total_amount_lost > 0 ? '₹' + (h.total_amount_lost / 1000).toFixed(0) + 'K lost' : ''}
      `;
      return `L.circleMarker([${h.lat}, ${h.lon}], {
        radius: ${radius},
        color: '${color}',
        fillColor: '${color}',
        fillOpacity: 0.7,
        weight: 2
      }).bindPopup(\`${popup}\`).addTo(map);`;
    })
    .join('\n');

  return `<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body, #map { width: 100%; height: 100%; background: #ECEAF4; }
</style>
</head>
<body>
<div id="map"></div>
<script>
  const map = L.map('map', { zoomControl: true }).setView([22.5, 80.0], 4);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map);
  ${markers}
</script>
</body>
</html>`;
}

export function FraudMap({ hotspots }: { hotspots: FraudHotspot[] }) {
  if (hotspots.filter((h) => h.lat && h.lon).length === 0) return null;

  if (Platform.OS === 'web') {
    const html = buildMapHtml(hotspots);
    const src = `data:text/html;charset=utf-8,${encodeURIComponent(html)}`;
    return (
      <View
        style={{
          height: 280,
          borderRadius: radius.xl,
          overflow: 'hidden',
          backgroundColor: colors.card,
        }}>
        {/* @ts-ignore — iframe is valid on web */}
        <iframe
          src={src}
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="Fraud hotspot map"
        />
      </View>
    );
  }

  // Native: needs react-native-webview — show placeholder for now
  return (
    <View
      style={{
        height: 280,
        borderRadius: radius.xl,
        backgroundColor: colors.card,
        alignItems: 'center',
        justifyContent: 'center',
        gap: space.sm,
      }}>
      <AppText variant="caption" style={{ textAlign: 'center', color: colors.muted }}>
        Map view available in the APK build.
      </AppText>
    </View>
  );
}
