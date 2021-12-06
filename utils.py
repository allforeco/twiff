import os
import math
import time
import json
import logging
import pathlib
import datetime

from typing import *
from abc import abstractmethod, ABC

log = logging.getLogger(__name__)

class Keys:
    def __init__(self, path:str) -> None:
        self.path = path
        self.keys = self._load(self.path)
        
        self.bearer_token = self.keys['bearer_token']
        self.api_key = self.keys['api_key']
        self.api_key_secret = self.keys['api_key_secret']
        self.access_token = self.keys['access_token']
        self.access_token_secret = self.keys['access_token_secret']
        
        log.info('Keys loaded...')
        #self._show(self.keys)
        
    def _load(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f) 
        else:
            log.critical('No key file found "{}". Cannot authenticate Client without keys.'.format(path))
            
    def _show(self, keys):
        for key, val in keys.items():
            log.info('{}: {}'.format(key, val))
                   
class Cursor:
    def __init__(self, path:Optional[str]=None) -> None:
        self.path = path
        self.fresh_data = {'oldest_id':None, 'newest_id':None}
        self.data = self._load(self.path) 
        
        log.info('Loading... {}'.format(self.__repr__()))

    def __repr__(self):
        return repr('Cursor ({}): oldest_id={}, newest_id={}'.format(self.path, self.data['oldest_id'], self.data['newest_id']))
        
    def _load(self, path:str) -> Dict[str,int]:
        if path is not None:
            if os.path.exists(path):
                log.debug('Loading cursor from "{}"'.format(path))
                with open(path, 'r') as f: return json.load(f)
            else:
                log.debug('Provided cursor path "{}" does not exists... Defaulting to fresh cursor.'.format(path))
                return self.fresh_data
        else:
            log.debug('Loading fresh_cursor...'.format(path))
            return self.fresh_data            
    
    def _dump(self, path:str) -> None:
        log.info('Dumping cursor to "{}"'.format(path))
        with open(path, 'w') as f: json.dump(self.data, f)
    
    def _update(self, oldest_id:int, newest_id:int) -> None:
        # Update self.oldest_id if oldest_id is SMALLER (less recent than) currently stored
        if self.data['oldest_id'] is None:
            self.data['oldest_id'] = oldest_id
        else:
            self.data['oldest_id'] = oldest_id if oldest_id<self.data['oldest_id'] else self.data['oldest_id'] 
        
        # Updated self.newest_id if newest_id is LARGER (more recent than) currently stored
        if self.data['newest_id'] is None:
            self.data['newest_id'] = newest_id
        else:
            self.data['newest_id'] = newest_id if newest_id>self.data['newest_id'] else self.data['newest_id'] 
        log.info('Updated cursor: {}'.format(self.__repr__()))

    def _oldest_id(self) -> int:
        return self.data['oldest_id']
    
    def _newest_id(self) -> int:
        return self.data['newest_id']
    
    def _isnull(self) -> bool:
        return self._oldest_id()==None and self._newest_id()==None
    
class Data(ABC):
    def __init__(self, data:Dict) -> None:
        self.data = data
        
    def __repr__(self):
        return repr(['{}: {}'.format(key, val) for (key, val) in self.data.items()])
    
    def _dump(self, root_dir:str) -> None:
        if not os.path.exists(root_dir): os.mkdir(root_dir)
        with open(os.path.join(root_dir, self.id_str + '.json'), 'w') as f: json.dump(self.data, f)
            
    def _id(self):
        pass
        
class Tweet(Data):
    def __init__(self, data:Dict) -> None:
        super(Tweet, self).__init__(data)
        
        # Fixed Attributes
        self.id = self.data['id']
        self.id_str = str(self.id)
        self.lang = self.data['lang'] 
        self.created_at = self.data['created_at']
        self.author_id = self.data['author_id']
        self.author_id_str = str(self.author_id)
        self.conversation_id = self.data['conversation_id']
        self.conversation_id_str = str(self.conversation_id) 
        self.text = self.data['text']
        
        # Conditional Attributes
        self.in_reply_to_user_id = self.data['in_reply_to_user_id'] if 'in_reply_to_user_id' in self.data else None
        self.referenced_tweets = self.data['referenced_tweets'] if 'referenced_tweets' in self.data else None
        
        # Entities
        self.entities = self.data['entities']
        self.hashtags = self.entities['hashtags'] if 'hashtags' in self.entities else None
        self.mentions = self.entities['mentions'] if 'mentions' in self.entities else None 
        
    def _id(self):
        return self.id_str
        
class User(Data):
    def __init__(self, data:Dict) -> None:
        super(User, self).__init__(data)
        
        # Fixed Attributed
        self.description = self.data['description']
        self.created_at = self.data['created_at']
        self.verified = self.data['verified'] 
        self.description = self.data['description']
        self.url = self.data['url']
        self.name = self.data['name']
        self.id = self.data['id']
        self.id_str = str(self.id)
        self.username = self.data['username']
        
        # Conditional Attributes
        self.entities = self.data['entities'] if 'entities' in self.data else None
        self.location = self.data['location'] if 'location' in self.data else None
        
    def _id(self):
        return self.id_str
    
class Error(Data):
    def __init__(self, data:Dict) -> None:
        super(Error, self).__init__(data)
        self.parameter = data['parameter']
        self.resource_id = data['resource_id']
        self.value = data['value']
        self.detail = data['detail']
        self.title = data['title']
        self.resource_type = data['resource_type']
        
class Metadata(Data):
    def __init__(self, data:Dict) -> None:
        super(Metadata, self).__init__(data)
        self.newest_id = self.data['newest_id'] if 'newest_id' in self.data else None
        self.oldest_id = self.data['oldest_id'] if 'oldest_id' in self.data else None
        self.result_count = self.data['result_count']
        
        self.since_id = self.oldest_id
        self.until_id = self.newest_id
        
class Results:
    def __init__(self, response:Optional[Dict]=None) -> None:
        if response is not None:
            self.metadata = Metadata(response['meta']) 
            if self.metadata.result_count>0:
                self.tweets = {Tweet(data)._id():Tweet(data) for data in response['data']}
                self.users = {User(data)._id():User(data) for data in response['includes']['users']}
                self.errors = [Error(data) for data in response['errors']] if 'errors' in response else None
                log.info('Retrieved {} tweets and {} associated users.'.format(len(self.tweets), len(self.users)))
            else:
                log.warning('No tweets were retrieved.')
        
    def _dump(self, root_dir:str) -> None:
        if not os.path.exists(root_dir): os.mkdir(root_dir)
        [tweet._dump(os.path.join(root_dir, 'tweets')) for tweet in self.tweets.values()]
        [user._dump(os.path.join(root_dir, 'users')) for user in self.users.values()]    
        log.info('Dumping {} tweets and {} users to {}...'.format(len(self.tweets), len(self.users), root_dir))
        
    def _load(self, root_dir:str) -> None: 
        self.tweets = {Tweet(data)._id():Tweet(data) for data in self._load_items(root_dir, 'tweets')}
        self.users = {User(data)._id():User(data) for data in self._load_items(root_dir, 'users')}
            
    def _load_items(self, root_dir:str, item:str):
        item_dir = os.path.join(root_dir, item)
        if os.path.exists(item_dir):
            paths = list(pathlib.Path(item_dir).glob('*.json'))
            if len(paths):
                log.info('Loading {} {}...'.format(len(paths), item))
                items = []
                for path in paths:
                    with open(path, 'r') as f: 
                        items.append(json.load(f))
                return items
            else:
                log.warning('No {} exist for importing.'.format(item))
        else:
            log.warning('Export path "{}" does not exist.'.format(item_dir))
        
    def _show(self) -> None:
        for tweet in self.tweets.values():
            print('User: {} ({}):\n{}: {}\n---------------\n'
                  .format(self.users[tweet.author_id_str].name, tweet.author_id_str, tweet.id, tweet.text))