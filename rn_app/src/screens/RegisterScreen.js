import React, { useState } from 'react';
import { View } from 'react-native';
import { TextInput, Button, Text } from 'react-native-paper';
import client from '../api/client';

export default function RegisterScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mobile, setMobile] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const register = async () => {
    setLoading(true);
    setError('');
    try {
      await client.post('/accounts/register/', { username, email, password, mobile_no: mobile });
      await client.post('/accounts/otp/send/', { mobile_no: mobile, purpose: 'register' });
      navigation.navigate('OTP', { mobile, purpose: 'register' });
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || 'Registration failed';
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 16 }}>
      <Text variant="titleLarge">Register</Text>
      <TextInput label="Username" value={username} onChangeText={setUsername} autoCapitalize="none" />
      <TextInput label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" />
      <TextInput label="Password" value={password} onChangeText={setPassword} secureTextEntry />
      <TextInput label="Mobile" value={mobile} onChangeText={setMobile} />
      {error ? <Text style={{ color: 'red', marginVertical: 8 }}>{error}</Text> : null}
      <Button mode="contained" onPress={register} loading={loading} style={{ marginTop: 12 }}>Register</Button>
    </View>
  );
}


