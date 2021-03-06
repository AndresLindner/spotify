import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyDAO:
    MAX_QUERY_RESULTS = 50

    def __init__(self):
        client_credentials_manager = SpotifyClientCredentials()
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def get_all_playlist_by_category(self, category, query_results=50):
        playlists_refs = []
        print('querying all playlists with category: {}', category)
        playlists = self.sp.category_playlists(category_id=category, limit=query_results)['playlists']
        while playlists:
            playlists_refs = playlists_refs + playlists['items']
            if playlists['next']:
                playlists = self.sp.next(playlists)['playlists']
            else:
                playlists = None
        print('completed {} playlists for: {}'.format(len(playlists_refs), category))
        return playlists_refs

    def enrich_playlist(self, user_id, playlist_id):
        tracks_refs = []
        playlist = self.sp.user_playlist(user_id, playlist_id)
        tracks = playlist['tracks']
        while tracks:
            tracks_refs = tracks_refs + [tr for tr in playlist['tracks']['items'] if tr['track']['id'] is not None]
            if tracks['next']:
                tracks = self.sp.next(tracks)
            else:
                tracks = None
        playlist['tracks']['items'] = tracks_refs
        audio_features = self.enrich_audio_features([tr['track']['id'] for tr in tracks_refs])
        for i in range(0, len(audio_features)):
            playlist['tracks']['items'][i]['track']['audio_features'] = audio_features[i]
        print('enriched playlist:{}'.format(playlist['name']))
        return playlist

    def enrich_audio_features(self, track_ids):
        audio_features = []
        for i in range(0, len(track_ids), self.MAX_QUERY_RESULTS):
            audio_features += self.sp.audio_features(tracks=track_ids[i:i + self.MAX_QUERY_RESULTS])

        return audio_features

    def get_list_of_categories(self, country=None, locale=None):
        cat_refs = [];
        categories = self.sp.categories(country, locale, limit=self.MAX_QUERY_RESULTS)['categories']
        while categories:
            cat_refs += categories['items'];
            if categories['next']:
                categories = self.sp.next(categories)['categories']
            else:
                categories = None
        return [ref['id'] for ref in cat_refs]

    def search(self, q, type='playlist', market=None, max_results=None):
        res_refs = []

        type_map = {
            'playlist': 'playlists',
            'track': 'tracks',
            'album': 'albums',
            'artist': 'artists',
        }

        results = self.sp.search(q, self.MAX_QUERY_RESULTS, type=type, market=market)[type_map[type]]
        while results:
            res_refs += results['items']
            if max_results is not None and len(res_refs) + self.MAX_QUERY_RESULTS > max_results:
                break
            if results['next']:
                results = self.sp.next(results)[type_map[type]]
            else:
                results = None
        return res_refs
