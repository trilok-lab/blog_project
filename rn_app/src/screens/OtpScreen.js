import React, { useState } from 'react';
import { View } from 'react-native';
import { TextInput, Button, Text } from 'react-native-paper';
import client from '../api/client';

export default function OtpScreen({ route, navigation }) {
  const { mobile, purpose } = route.params || {};
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const verify = async () => {
    setLoading(true);
    setError('');
    try {
      await client.post('/accounts/otp/verify/', { mobile_no: mobile, purpose, code });
      navigation.goBack();
    } catch (e) {
      setError('Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 16 }}>
      <Text variant="titleLarge">Verify Mobile</Text>
      <Text>Sent to {mobile}</Text>
      <TextInput label="Code" value={code} onChangeText={setCode} keyboardType="number-pad" />
      {error ? <Text style={{ color: 'red', marginVertical: 8 }}>{error}</Text> : null}
      <Button mode="contained" onPress={verify} loading={loading} style={{ marginTop: 12 }}>Verify</Button>
    </View>
  );
}


