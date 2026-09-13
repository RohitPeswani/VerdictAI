import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  StatusBar,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../../types';
import { Colors, Typography, Spacing, Radius } from '../../theme';

type Props = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Login'>;
};

export default function LoginScreen({ navigation }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Missing Fields', 'Please enter your email and password.');
      return;
    }
    setLoading(true);
    // TODO Phase 4: integrate with auth endpoint (POST /api/v1/auth/login)
    // Simulate a brief delay then navigate to OTP
    setTimeout(() => {
      setLoading(false);
      navigation.navigate('Verification', { email: email.trim() });
    }, 800);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
              <Text style={styles.backIcon}>←</Text>
            </TouchableOpacity>
            <Text style={styles.logoIcon}>⚖️</Text>
            <Text style={styles.title}>Sign In</Text>
            <Text style={styles.subtitle}>
              Access your VerdictAI card member account
            </Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Email Address</Text>
              <TextInput
                style={styles.input}
                placeholder="cardholder@email.com"
                placeholderTextColor={Colors.textMuted}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                value={email}
                onChangeText={setEmail}
              />
            </View>

            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Password</Text>
              <View style={styles.passwordContainer}>
                <TextInput
                  style={[styles.input, { flex: 1, borderWidth: 0 }]}
                  placeholder="••••••••"
                  placeholderTextColor={Colors.textMuted}
                  secureTextEntry={!showPassword}
                  value={password}
                  onChangeText={setPassword}
                />
                <TouchableOpacity
                  onPress={() => setShowPassword(!showPassword)}
                  style={styles.eyeButton}
                >
                  <Text style={styles.eyeIcon}>{showPassword ? '🙈' : '👁️'}</Text>
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity style={styles.forgotPassword}>
              <Text style={styles.forgotText}>Forgot Password?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.loginButton, loading && styles.loginButtonDisabled]}
              onPress={handleLogin}
              disabled={loading}
              activeOpacity={0.85}
            >
              <Text style={styles.loginButtonText}>
                {loading ? 'Signing in...' : 'Sign In →'}
              </Text>
            </TouchableOpacity>

            {/* Divider */}
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or continue with</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Biometric Button */}
            <TouchableOpacity style={styles.biometricButton} activeOpacity={0.85}>
              <Text style={styles.biometricIcon}>🔑</Text>
              <Text style={styles.biometricText}>Sign in with Biometrics</Text>
            </TouchableOpacity>
          </View>

          {/* Demo Credentials Note */}
          <View style={styles.demoNote}>
            <Text style={styles.demoTitle}>🔧 Demo Credentials (Dev Only)</Text>
            <Text style={styles.demoText}>
              Cardholder ID: usr_alice_01{'\n'}
              Any email & password will work in mock mode.
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep },
  scrollContent: { padding: Spacing.xl, gap: Spacing.xl },
  header: { alignItems: 'center', gap: Spacing.sm },
  backBtn: { alignSelf: 'flex-start', padding: Spacing.sm },
  backIcon: { fontSize: 22, color: Colors.textPrimary },
  logoIcon: { fontSize: 36 },
  title: { fontSize: Typography['2xl'], fontWeight: Typography.bold, color: Colors.textPrimary },
  subtitle: { fontSize: Typography.sm, color: Colors.textSecondary, textAlign: 'center' },
  form: { gap: Spacing.base },
  fieldGroup: { gap: Spacing.xs },
  label: { fontSize: Typography.sm, fontWeight: Typography.medium, color: Colors.textSecondary },
  input: {
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    fontSize: Typography.base,
    color: Colors.textPrimary,
  },
  passwordContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: Spacing.base,
  },
  eyeButton: { padding: Spacing.sm },
  eyeIcon: { fontSize: 18 },
  forgotPassword: { alignSelf: 'flex-end' },
  forgotText: { fontSize: Typography.sm, color: Colors.primary, fontWeight: Typography.medium },
  loginButton: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.lg,
    paddingVertical: Spacing.base,
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  loginButtonDisabled: { opacity: 0.6 },
  loginButtonText: { fontSize: Typography.md, fontWeight: Typography.bold, color: '#fff' },
  divider: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.border },
  dividerText: { fontSize: Typography.xs, color: Colors.textMuted },
  biometricButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    paddingVertical: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.sm,
  },
  biometricIcon: { fontSize: 20 },
  biometricText: { fontSize: Typography.base, color: Colors.textPrimary, fontWeight: Typography.medium },
  demoNote: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.md,
    padding: Spacing.base,
    borderLeftWidth: 3,
    borderLeftColor: Colors.warning,
    gap: Spacing.xs,
  },
  demoTitle: { fontSize: Typography.sm, fontWeight: Typography.bold, color: Colors.warning },
  demoText: { fontSize: Typography.xs, color: Colors.textSecondary, lineHeight: 18 },
});
