import React, { useEffect, useState } from 'react';
import { View, FlatList } from 'react-native';
import { Text, ActivityIndicator, Chip, Button, TextInput } from 'react-native-paper';
import client from '../api/client';

export default function ArticleDetailScreen({ route }) {
  const { slug } = route.params || {};
  const [item, setItem] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [comment, setComment] = useState('');
  const [guestName, setGuestName] = useState('');
  const [guestMobile, setGuestMobile] = useState('');
  const [otp, setOtp] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const { data: found } = await client.get(`/articles/items/${slug}/`);
      if (found) setItem(found);
      const { data: comm } = await client.get(`/comments/?article=${found?.id}`);
      setComments(comm);
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => { load(); }, [slug]);

  const submitComment = async () => {
    try {
      await client.post('/comments/', {
        article: item.id,
        content: comment,
        author_name: guestName,
        author_mobile: guestMobile,
        code: otp,
      });
      setComment('');
      load();
    } catch (e) {}
  };

  const sendGuestOtp = async () => {
    await client.post('/accounts/otp/send/', { mobile_no: guestMobile, purpose: 'guest_comment' });
  };

  if (loading || !item) return <ActivityIndicator style={{ marginTop: 16 }} />;

  return (
    <View style={{ padding: 16 }}>
      <Text variant="headlineSmall">{item.title}</Text>
      <Text style={{ marginVertical: 8 }}>{item.description}</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
        {item.categories?.map((c) => (
          <Chip key={c.id} style={{ marginRight: 8 }}>{c.name}</Chip>
        ))}
      </View>

      <Text variant="titleMedium" style={{ marginTop: 16 }}>Comments</Text>
      <FlatList
        data={comments}
        keyExtractor={(c) => String(c.id)}
        renderItem={({ item: c }) => (
          <View style={{ paddingVertical: 8, borderBottomWidth: 1, borderColor: '#eee' }}>
            <Text>{c.author_name || 'User'}</Text>
            <Text>{c.content}</Text>
          </View>
        )}
      />

      <Text variant="titleSmall" style={{ marginTop: 12 }}>Add a comment</Text>
      <TextInput label="Name" value={guestName} onChangeText={setGuestName} />
      <TextInput label="Mobile" value={guestMobile} onChangeText={setGuestMobile} />
      <Button onPress={sendGuestOtp} style={{ marginTop: 8 }}>Send OTP</Button>
      <TextInput label="OTP" value={otp} onChangeText={setOtp} />
      <TextInput label="Comment" value={comment} onChangeText={setComment} multiline />
      <Button mode="contained" onPress={submitComment} style={{ marginTop: 12 }}>Submit</Button>
    </View>
  );
}


