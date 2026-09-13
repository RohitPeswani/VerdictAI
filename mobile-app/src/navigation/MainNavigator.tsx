import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text, View } from 'react-native';
import { MainTabParamList, HomeStackParamList, FileDisputeStackParamList } from '../types';
import { Colors, Typography } from '../theme';

// Screens
import MyDisputesScreen from '../screens/main/MyDisputesScreen';
import DisputeDetailScreen from '../screens/main/DisputeDetailScreen';
import DisputeWizardScreen from '../screens/main/DisputeWizardScreen';
import DisputeSuccessScreen from '../screens/main/DisputeSuccessScreen';
import NotificationsScreen from '../screens/main/NotificationsScreen';
import ProfileScreen from '../screens/main/ProfileScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const FileStack = createNativeStackNavigator<FileDisputeStackParamList>();

// ─── Nested stacks ────────────────────────────────────────────────────────

function HomeStackNavigator() {
  return (
    <HomeStack.Navigator screenOptions={{ headerShown: false }}>
      <HomeStack.Screen name="MyDisputes" component={MyDisputesScreen} />
      <HomeStack.Screen name="DisputeDetail" component={DisputeDetailScreen} />
    </HomeStack.Navigator>
  );
}

function FileDisputeStackNavigator() {
  return (
    <FileStack.Navigator screenOptions={{ headerShown: false }}>
      <FileStack.Screen name="DisputeWizard" component={DisputeWizardScreen} />
      <FileStack.Screen name="DisputeSuccess" component={DisputeSuccessScreen} />
    </FileStack.Navigator>
  );
}

// ─── Tab Icon ────────────────────────────────────────────────────────────

function TabIcon({ icon, label, focused }: { icon: string; label: string; focused: boolean }) {
  return (
    <View style={{ alignItems: 'center', gap: 2 }}>
      <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>{icon}</Text>
      <Text style={{
        fontSize: Typography.xs,
        color: focused ? Colors.tabActive : Colors.tabInactive,
        fontWeight: focused ? Typography.semibold : Typography.regular,
      }}>
        {label}
      </Text>
    </View>
  );
}

// ─── Main Tab Navigator ──────────────────────────────────────────────────

export default function MainNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: {
          backgroundColor: Colors.tabBackground,
          borderTopWidth: 1,
          borderTopColor: Colors.border,
          height: 72,
          paddingBottom: 8,
          paddingTop: 8,
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStackNavigator}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="🏠" label="Home" focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="FileDisputeTab"
        component={FileDisputeStackNavigator}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="⚖️" label="Dispute" focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="NotificationsTab"
        component={NotificationsScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="🔔" label="Alerts" focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="👤" label="Profile" focused={focused} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}
