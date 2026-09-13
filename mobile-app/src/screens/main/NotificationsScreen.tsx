import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { Colors, Typography, Spacing, Radius } from '../../theme';

interface Notification {
  id: string;
  icon: string;
  title: string;
  body: string;
  time: string;
  read: boolean;
  type: 'resolved' | 'update' | 'warning' | 'info';
}

// Illustrative mock notifications matching real lifecycle events
const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    icon: '✅',
    title: 'Dispute Auto-Resolved',
    body: 'Your dispute against Apple Store Online ($1,299.00) has been resolved in your favor. Refund processing.',
    time: '2 mins ago',
    read: false,
    type: 'resolved',
  },
  {
    id: '2',
    icon: '🔍',
    title: 'Evidence Analysis Complete',
    body: 'VerdictAI has completed analyzing all evidence for Case CAS-7C9E6679. Fair-Weighing score generated.',
    time: '1 hour ago',
    read: false,
    type: 'update',
  },
  {
    id: '3',
    icon: '⏱',
    title: 'SLA Warning — 4 Hours Left',
    body: 'Merchant SLA response window is expiring soon for your Amazon.com dispute ($124.50).',
    time: '3 hours ago',
    read: true,
    type: 'warning',
  },
  {
    id: '4',
    icon: '📋',
    title: 'Dispute Submitted',
    body: 'Your dispute for Starbucks Coffee ($15.75) has been filed. Case file sealed with SHA-256 hash.',
    time: 'Yesterday',
    read: true,
    type: 'info',
  },
  {
    id: '5',
    icon: '📊',
    title: 'Case Assigned to Analyst',
    body: 'Your borderline dispute has been routed to a Dispute-Ops analyst for manual review.',
    time: '2 days ago',
    read: true,
    type: 'info',
  },
];

const TYPE_COLORS = {
  resolved: Colors.statusResolved,
  update: Colors.statusInProgress,
  warning: Colors.statusManual,
  info: Colors.primary,
};

export default function NotificationsScreen() {
  const unreadCount = MOCK_NOTIFICATIONS.filter((n) => !n.read).length;

  const renderNotification = ({ item }: { item: Notification }) => (
    <View style={[styles.card, !item.read && styles.cardUnread]}>
      <View style={[styles.iconCircle, { backgroundColor: `${TYPE_COLORS[item.type]}20` }]}>
        <Text style={styles.icon}>{item.icon}</Text>
      </View>
      <View style={styles.cardBody}>
        <View style={styles.cardHeader}>
          <Text style={styles.title}>{item.title}</Text>
          {!item.read && <View style={styles.unreadDot} />}
        </View>
        <Text style={styles.body}>{item.body}</Text>
        <Text style={styles.time}>{item.time}</Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Notifications</Text>
          {unreadCount > 0 && (
            <Text style={styles.headerSub}>{unreadCount} unread alert{unreadCount > 1 ? 's' : ''}</Text>
          )}
        </View>
        <Text style={styles.bellIcon}>🔔</Text>
      </View>

      <FlatList
        data={MOCK_NOTIFICATIONS}
        keyExtractor={(item) => item.id}
        renderItem={renderNotification}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>📭</Text>
            <Text style={styles.emptyText}>No notifications yet</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: Spacing.xl, paddingTop: Spacing.lg, paddingBottom: Spacing.md,
  },
  headerTitle: { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.textPrimary },
  headerSub: { fontSize: Typography.sm, color: Colors.primary, marginTop: 2 },
  bellIcon: { fontSize: 26 },
  list: { padding: Spacing.xl, gap: Spacing.md },
  card: {
    flexDirection: 'row', gap: Spacing.md,
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg,
    padding: Spacing.base, borderWidth: 1, borderColor: Colors.border,
  },
  cardUnread: { borderColor: Colors.primary + '60' },
  iconCircle: {
    width: 44, height: 44, borderRadius: 22,
    alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  icon: { fontSize: 22 },
  cardBody: { flex: 1, gap: Spacing.xs },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: Typography.sm, fontWeight: Typography.semibold, color: Colors.textPrimary, flex: 1 },
  unreadDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.primary, marginLeft: Spacing.xs },
  body: { fontSize: Typography.xs, color: Colors.textSecondary, lineHeight: 18 },
  time: { fontSize: Typography.xs, color: Colors.textMuted },
  empty: { alignItems: 'center', paddingTop: Spacing['4xl'], gap: Spacing.md },
  emptyIcon: { fontSize: 48 },
  emptyText: { fontSize: Typography.base, color: Colors.textMuted },
});
