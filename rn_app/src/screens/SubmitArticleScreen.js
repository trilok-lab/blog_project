import React, { useState } from 'react';
import { View } from 'react-native';
import { Text, TextInput, Button } from 'react-native-paper';
import client from '../api/client';

export default function SubmitArticleScreen({ navigation }) {
  const [title, setTitle] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const payThenSubmit = async () => {
    setLoading(true);
    setMessage('');
    try {
      const { data } = await client.post('/accounts/stripe/create-intent/');
      if (data.client_secret) {
        await client.post('/accounts/stripe/confirm/');
      }
      await client.post('/articles/items/', { title, excerpt, description });
      setMessage('Submitted. Awaiting approval.');
      setTitle(''); setExcerpt(''); setDescription('');
    } catch (e) {
      setMessage('Payment or submit failed (login required).');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ padding: 16 }}>
      <Text variant="titleLarge">Submit Article</Text>
      <TextInput label="Title" value={title} onChangeText={setTitle} />
      <TextInput label="Excerpt" value={excerpt} onChangeText={setExcerpt} />
      <TextInput label="Description" value={description} onChangeText={setDescription} multiline />
      {message ? <Text style={{ marginTop: 8 }}>{message}</Text> : null}
      <Button mode="contained" onPress={payThenSubmit} loading={loading} style={{ marginTop: 12 }}>Pay & Submit</Button>
      <Button onPress={() => navigation.navigate('Login')} style={{ marginTop: 8 }}>Login</Button>
    </View>
  );
}


