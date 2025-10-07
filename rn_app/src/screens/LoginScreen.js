import React, { useState } from 'react';
import { View } from 'react-native';
import { TextInput, Button, Text } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import client from '../api/client';

export default function LoginScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const login = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await client.post('/accounts/login/', { username, password });
      await AsyncStorage.setItem('token', data.access);
      navigation.goBack();
    } catch (e) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 16 }}>
      <Text variant="titleLarge">Login</Text>
      <TextInput label="Username" value={username} onChangeText={setUsername} autoCapitalize="none" />
      <TextInput label="Password" value={password} onChangeText={setPassword} secureTextEntry />
      {error ? <Text style={{ color: 'red', marginVertical: 8 }}>{error}</Text> : null}
      <Button mode="contained" onPress={login} loading={loading} style={{ marginTop: 12 }}>Login</Button>
      <Button onPress={() => navigation.navigate('Register')} style={{ marginTop: 8 }}>Create account</Button>
    </View>
  );
}


