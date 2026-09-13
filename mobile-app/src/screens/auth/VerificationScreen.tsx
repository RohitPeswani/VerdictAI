import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  SafeAreaView,
  StatusBar,
  Alert,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { AuthStackParamList, RootStackParamList } from '../../types';
import { Colors, Typography, Spacing, Radius } from '../../theme';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp as RootNav } from '@react-navigation/native-stack';

type Props = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Verification'>;
  route: RouteProp<AuthStackParamList, 'Verification'>;
};

export default function VerificationScreen({ navigation, route }: Props) {
  const { email } = route.params;
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const inputRefs = useRef<TextInput[]>([]);
  const rootNav = useNavigation<RootNav<RootStackParamList, 'Auth'>>();

  const handleOtpChange = (text: string, index: number) => {
    const newOtp = [...otp];
    newOtp[index] = text;
    setOtp(newOtp);
    // Auto-focus next
    if (text && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyPress = (key: string, index: number) => {
    if (key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = () => {
    const code = otp.join('');
    if (code.length < 6) {
      Alert.alert('Incomplete Code', 'Please enter all 6 digits of your verification code.');
      return;
    }
    setLoading(true);
    // TODO Phase 4: POST /api/v1/auth/verify-otp
    // For now, any 6-digit code works in mock mode
    setTimeout(() => {
      setLoading(false);
      // Navigate to Main app stack
      rootNav.reset({ index: 0, routes: [{ name: 'Main' }] });
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
        <Text style={styles.backIcon}>←</Text>
      </TouchableOpacity>

      <View style={styles.content}>
        <Text style={styles.shieldIcon}>🔐</Text>
        <Text style={styles.title}>Verify Your Identity</Text>
        <Text style={styles.subtitle}>
          We sent a 6-digit code to{'\n'}
          <Text style={styles.emailHighlight}>{email}</Text>
        </Text>

        {/* OTP Input Grid */}
        <View style={styles.otpContainer}>
          {otp.map((digit, index) => (
            <TextInput
              key={index}
              ref={(ref) => { if (ref) inputRefs.current[index] = ref; }}
              style={[styles.otpInput, digit ? styles.otpInputFilled : null]}
              value={digit}
              onChangeText={(text) => handleOtpChange(text.slice(-1), index)}
              onKeyPress={({ nativeEvent }) => handleOtpKeyPress(nativeEvent.key, index)}
              keyboardType="number-pad"
              maxLength={1}
              textAlign="center"
              selectionColor={Colors.primary}
            />
          ))}
        </View>

        <TouchableOpacity
          style={[styles.verifyButton, loading && styles.verifyButtonDisabled]}
          onPress={handleVerify}
          disabled={loading}
          activeOpacity={0.85}
        >
          <Text style={styles.verifyButtonText}>
            {loading ? 'Verifying...' : 'Verify & Continue →'}
          </Text>
        </TouchableOpacity>

        {/* Resend */}
        <View style={styles.resendRow}>
          <Text style={styles.resendPrompt}>Didn't receive it? </Text>
          <TouchableOpacity disabled={resendTimer > 0}>
            <Text style={[styles.resendLink, resendTimer > 0 && styles.resendDisabled]}>
              {resendTimer > 0 ? `Resend in ${resendTimer}s` : 'Resend Code'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.securityNote}>
          <Text style={styles.securityText}>
            🔒 This verification protects your financial dispute account
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep, paddingHorizontal: Spacing.xl },
  backBtn: { paddingVertical: Spacing.base },
  backIcon: { fontSize: 22, color: Colors.textPrimary },
  content: { flex: 1, alignItems: 'center', gap: Spacing.lg, paddingTop: Spacing.xl },
  shieldIcon: { fontSize: 56 },
  title: { fontSize: Typography['2xl'], fontWeight: Typography.bold, color: Colors.textPrimary },
  subtitle: { fontSize: Typography.base, color: Colors.textSecondary, textAlign: 'center', lineHeight: 24 },
  emailHighlight: { color: Colors.primary, fontWeight: Typography.semibold },
  otpContainer: { flexDirection: 'row', gap: Spacing.sm, marginVertical: Spacing.md },
  otpInput: {
    width: 48,
    height: 56,
    borderRadius: Radius.md,
    borderWidth: 1.5,
    borderColor: Colors.border,
    backgroundColor: Colors.bgSurface,
    fontSize: Typography.xl,
    fontWeight: Typography.bold,
    color: Colors.textPrimary,
  },
  otpInputFilled: { borderColor: Colors.primary, backgroundColor: Colors.bgElevated },
  verifyButton: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.lg,
    paddingVertical: Spacing.base,
    paddingHorizontal: Spacing['3xl'],
    alignItems: 'center',
    width: '100%',
  },
  verifyButtonDisabled: { opacity: 0.6 },
  verifyButtonText: { fontSize: Typography.md, fontWeight: Typography.bold, color: '#fff' },
  resendRow: { flexDirection: 'row', alignItems: 'center' },
  resendPrompt: { fontSize: Typography.sm, color: Colors.textSecondary },
  resendLink: { fontSize: Typography.sm, color: Colors.primary, fontWeight: Typography.semibold },
  resendDisabled: { color: Colors.textMuted },
  securityNote: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    width: '100%',
  },
  securityText: { fontSize: Typography.xs, color: Colors.textMuted, textAlign: 'center' },
});
