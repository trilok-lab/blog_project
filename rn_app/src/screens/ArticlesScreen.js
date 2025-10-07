import React, { useEffect, useState } from 'react';
import { View, FlatList, TouchableOpacity } from 'react-native';
import { Text, ActivityIndicator, Searchbar } from 'react-native-paper';
import client from '../api/client';

export default function ArticlesScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [query, setQuery] = useState('');

  const load = async (pageNum = 1, q = '') => {
    setLoading(true);
    try {
      const { data } = await client.get(`/articles/items/?page=${pageNum}&search=${encodeURIComponent(q)}`);
      setItems(pageNum === 1 ? data.results : [...items, ...data.results]);
      setNext(data.next);
      setPage(pageNum);
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    load(1, '');
  }, []);

  const renderItem = ({ item }) => (
    <TouchableOpacity onPress={() => navigation.navigate('ArticleDetail', { slug: item.slug })} style={{ padding: 12, borderBottomWidth: 1, borderColor: '#eee' }}>
      <Text variant="titleMedium">{item.title}</Text>
      {item.excerpt ? <Text>{item.excerpt}</Text> : null}
      <Text>Comments: {item.num_comments ?? 0}</Text>
      <Text>Read more</Text>
    </TouchableOpacity>
  );

  return (
    <View style={{ flex: 1 }}>
      <Searchbar placeholder="Search" value={query} onChangeText={setQuery} onSubmitEditing={() => load(1, query)} />
      {loading && page === 1 ? <ActivityIndicator style={{ marginTop: 16 }} /> : null}
      <FlatList
        data={items}
        renderItem={renderItem}
        keyExtractor={(it) => String(it.id)}
        onEndReached={() => next && load(page + 1, query)}
        onEndReachedThreshold={0.5}
      />
    </View>
  );
}


