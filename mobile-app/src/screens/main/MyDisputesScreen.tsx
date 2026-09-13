import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { HomeStackParamList, UnifiedCaseFile, DisputeStatus } from '../../types';
import { Colors, Typography, Spacing, Radius, Shadow } from '../../theme';
import { getDisputes } from '../../services/disputesService';

type Props = {
  navigation: NativeStackNavigationProp<HomeStackParamList, 'MyDisputes'>;
};

// Hardcoded demo cardholder ID matching backend seed data
const DEMO_CARDHOLDER_ID = 'usr_alice_01';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  SUBMITTED: { label: 'Submitted', color: Colors.statusSubmitted, bg: '#2A1F0A' },
  EVIDENCE_PENDING: { label: 'Evidence Pending', color: Colors.statusSubmitted, bg: '#2A1F0A' },
  EVIDENCE_INGESTED: { label: 'Analyzing', color: Colors.statusInProgress, bg: '#0A1A2A' },
  IN_ANALYSIS: { label: 'In Analysis', color: Colors.statusInProgress, bg: '#0A1A2A' },
  SCORING_EVALUATED: { label: 'Scoring', color: Colors.statusEvaluated, bg: '#1A0A2A' },
  AUTO_RESOLVED: { label: 'Resolved ✓', color: Colors.statusResolved, bg: '#0A2A1A' },
  CLOSED: { label: 'Closed', color: Colors.statusResolved, bg: '#0A2A1A' },
  MANUAL_REVIEW_QUEUE: { label: 'Under Review', color: Colors.statusManual, bg: '#2A1200' },
  ADMIN_OVERRIDDEN: { label: 'Overridden', color: Colors.statusOverridden, bg: '#0F0A2A' },
  RESOLUTION_NOTIFIED: { label: 'Notified', color: Colors.statusResolved, bg: '#0A2A1A' },
  REJECTED: { label: 'Rejected', color: Colors.statusRejected, bg: '#2A0A0A' },
};

export default function MyDisputesScreen({ navigation }: Props) {
  const [disputes, setDisputes] = useState<UnifiedCaseFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'active' | 'resolved'>('active');
  const [error, setError] = useState<string | null>(null);

  const fetchDisputes = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const response = await getDisputes(DEMO_CARDHOLDER_ID);
      setDisputes(response.items);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load disputes.';
      setError(msg);
      // Fallback to empty state rather than crash
      setDisputes([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchDisputes();
    }, [])
  );

  const activeDisputes = disputes.filter(
    (d) => !['AUTO_RESOLVED', 'CLOSED', 'REJECTED'].includes(d.header.current_status)
  );
  const resolvedDisputes = disputes.filter(
    (d) => ['AUTO_RESOLVED', 'CLOSED', 'REJECTED'].includes(d.header.current_status)
  );
  const displayedDisputes = activeTab === 'active' ? activeDisputes : resolvedDisputes;

  const renderDisputeCard = ({ item }: { item: UnifiedCaseFile }) => {
    const status = item.header.current_status as DisputeStatus;
    const statusConf = STATUS_CONFIG[status] ?? { label: status, color: Colors.textMuted, bg: Colors.bgCard };
    const slaDate = new Date(item.header.sla_deadline);
    const now = new Date();
    const hoursLeft = Math.max(0, Math.floor((slaDate.getTime() - now.getTime()) / 3600000));

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('DisputeDetail', { disputeId: item.header.dispute_id })}
        activeOpacity={0.8}
      >
        <View style={styles.cardHeader}>
          <View>
            <Text style={styles.merchantName}>{item.transaction.merchant_name}</Text>
            <Text style={styles.caseRef}>{item.header.case_reference_number}</Text>
          </View>
          <Text style={styles.amount}>
            ${item.header.disputed_amount.toFixed(2)}
          </Text>
        </View>

        <View style={styles.cardFooter}>
          <View style={[styles.statusBadge, { backgroundColor: statusConf.bg }]}>
            <Text style={[styles.statusText, { color: statusConf.color }]}>
              {statusConf.label}
            </Text>
          </View>
          {!['AUTO_RESOLVED', 'CLOSED', 'REJECTED'].includes(status) && (
            <Text style={styles.slaText}>⏱ {hoursLeft}h remaining</Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>My Disputes</Text>
          <Text style={styles.subGreeting}>Card Member Dashboard</Text>
        </View>
        <Text style={styles.headerIcon}>⚖️</Text>
      </View>

      {/* Summary Cards */}
      <View style={styles.summaryRow}>
        <SummaryCard label="Total" value={disputes.length} color={Colors.primary} />
        <SummaryCard label="Active" value={activeDisputes.length} color={Colors.statusSubmitted} />
        <SummaryCard label="Resolved" value={resolvedDisputes.length} color={Colors.statusResolved} />
      </View>

      {/* Tab Selector */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'active' && styles.tabActive]}
          onPress={() => setActiveTab('active')}
        >
          <Text style={[styles.tabText, activeTab === 'active' && styles.tabTextActive]}>
            Active ({activeDisputes.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'resolved' && styles.tabActive]}
          onPress={() => setActiveTab('resolved')}
        >
          <Text style={[styles.tabText, activeTab === 'resolved' && styles.tabTextActive]}>
            Resolved ({resolvedDisputes.length})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>Loading disputes...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={() => fetchDisputes()}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : displayedDisputes.length === 0 ? (
        <EmptyState tab={activeTab} />
      ) : (
        <FlatList
          data={displayedDisputes}
          keyExtractor={(item) => item.header.dispute_id}
          renderItem={renderDisputeCard}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchDisputes(true)}
              tintColor={Colors.primary}
            />
          }
        />
      )}
    </SafeAreaView>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={[styles.summaryCard, { borderTopColor: color }]}>
      <Text style={[styles.summaryValue, { color }]}>{value}</Text>
      <Text style={styles.summaryLabel}>{label}</Text>
    </View>
  );
}

function EmptyState({ tab }: { tab: string }) {
  return (
    <View style={styles.center}>
      <Text style={styles.emptyIcon}>{tab === 'active' ? '✅' : '📭'}</Text>
      <Text style={styles.emptyTitle}>
        {tab === 'active' ? 'No Active Disputes' : 'No Resolved Disputes'}
      </Text>
      <Text style={styles.emptySubtext}>
        {tab === 'active'
          ? 'You have no active disputed charges. Use the + tab to file a new dispute.'
          : 'Resolved disputes will appear here.'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.md,
  },
  greeting: { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.textPrimary },
  subGreeting: { fontSize: Typography.sm, color: Colors.textSecondary },
  headerIcon: { fontSize: 28 },
  summaryRow: { flexDirection: 'row', gap: Spacing.sm, paddingHorizontal: Spacing.xl, marginBottom: Spacing.md },
  summaryCard: {
    flex: 1,
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.md,
    padding: Spacing.md,
    alignItems: 'center',
    borderTopWidth: 2,
    borderWidth: 1,
    borderColor: Colors.border,
    ...Shadow.card,
  },
  summaryValue: { fontSize: Typography['2xl'], fontWeight: Typography.extrabold },
  summaryLabel: { fontSize: Typography.xs, color: Colors.textMuted, marginTop: 2 },
  tabBar: { flexDirection: 'row', marginHorizontal: Spacing.xl, marginBottom: Spacing.base, backgroundColor: Colors.bgCard, borderRadius: Radius.md, padding: 4 },
  tab: { flex: 1, paddingVertical: Spacing.sm, alignItems: 'center', borderRadius: Radius.sm },
  tabActive: { backgroundColor: Colors.primary },
  tabText: { fontSize: Typography.sm, color: Colors.textSecondary, fontWeight: Typography.medium },
  tabTextActive: { color: '#fff', fontWeight: Typography.bold },
  list: { paddingHorizontal: Spacing.xl, gap: Spacing.md, paddingBottom: Spacing.xl },
  card: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.md,
    ...Shadow.card,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  merchantName: { fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.textPrimary },
  caseRef: { fontSize: Typography.xs, color: Colors.textMuted, marginTop: 2 },
  amount: { fontSize: Typography.lg, fontWeight: Typography.bold, color: Colors.textPrimary },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  statusBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: Radius.full },
  statusText: { fontSize: Typography.xs, fontWeight: Typography.semibold },
  slaText: { fontSize: Typography.xs, color: Colors.textSecondary },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: Spacing.md, paddingHorizontal: Spacing.xl },
  loadingText: { color: Colors.textSecondary, fontSize: Typography.base },
  errorIcon: { fontSize: 40 },
  errorText: { color: Colors.error, fontSize: Typography.sm, textAlign: 'center' },
  retryBtn: { backgroundColor: Colors.primary, borderRadius: Radius.md, paddingHorizontal: Spacing.xl, paddingVertical: Spacing.md },
  retryText: { color: '#fff', fontWeight: Typography.bold },
  emptyIcon: { fontSize: 48 },
  emptyTitle: { fontSize: Typography.lg, fontWeight: Typography.bold, color: Colors.textPrimary },
  emptySubtext: { fontSize: Typography.sm, color: Colors.textSecondary, textAlign: 'center', lineHeight: 22 },
});
