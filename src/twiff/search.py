import os
import sys
import json
import tweepy
import logging
import datetime
import argparse

from typing import *

from twiff import load_module

log = logging.getLogger(__name__)

def search(client:Any, cursor:str, query:str, max_requests:Optional[int]=100) -> Tuple[Dict, Dict, list, Dict]:
    """ Search Tweets
    
        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 450 requests per 15-minute window shared among all users of your app
    
        Args:
            client (): 
            cursor (str):
            query (str):
            max_requests (Optional[int]=100): 
            
        Returns:
            tweets (Dict): 
            users (Dict): 
            errors (list): 
            metadata (Dict): 
            
        Example::
            >>>
            >>>
            >>>
            
    """
    tweets, users, errors, metadata = {}, {}, [], {}
    
    # Prepare cursors for retrieving tweets.
    from twiff.utils.cursor import Cursor
    new_cursor = Cursor()
    old_cursor = Cursor(cursor)
    
    # Search for tweets
    responses = client.search_recent_tweets(query=query, 
                                            expansions=['author_id', 'entities.mentions.username', 'geo.place_id', 'in_reply_to_user_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id'],
                                            max_results=max_requests, 
                                            place_fields=['country', 'country_code', 'full_name', 'geo', 'id', 'name', 'place_type'],
                                            since_id=old_cursor._newest_id(),
                                            tweet_fields=['author_id', 'conversation_id', 'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id', 'lang', 'referenced_tweets', 'reply_settings', 'source', 'text', 'withheld'],
                                            until_id=new_cursor._oldest_id(),
                                            user_fields=['created_at', 'description', 'entities', 'id', 'location', 'name', 'url', 'username', 'verified', 'withheld']
                                           )

    # Process tweet data
    if 'data' in responses:
        for tweet in responses['data']:
            tweets[tweet['id']] = tweet
    
    # Process user data
    if 'includes' in responses:
        for user in responses['includes']['users']:
            users[user['id']] = user

    # Process error data
    if 'errors' in responses:
        for error in responses['errors']:
            errors.append(error)

    # Process metadata data
    metadata = responses['meta']

    # Update cursor
    if metadata['result_count']:
        new_cursor._update(metadata['oldest_id'], metadata['newest_id'])
        new_cursor._dump(cursor)
    
    log.info(f"Retrieved {len(tweets)} tweets and {len(users)} associated users. Encountered {len(errors)} errors.")
            
    return tweets, users, errors, metadata
    
    
def like(client:Any, tweets:Dict, max_requests:Optional[int]=100) -> None:
    """ Likes tweets using associated tweet id.
    
        Using max_likes may be necessary depending on whether you can afford to respect wait limits for all retrieved tweets.
        
        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 50 requests per 15-minute window per each authenticated user
    
        Args:
            X
            
        Returns:
            X
            
        Example::
            X
            
    """
    if max_requests:
        for idx, (id_str, tweet) in enumerate(tweets.items()):
            if idx>=max_requests: break
            client.like(id_str)
                       
    
def parse(tweets:Dict, users:Dict, tweet_parser:Callable) -> Dict:
    """ Handles parsing of tweets using the provided tweet parsing method.
    
        NOTE: 
            Contract for returned parsed tweet should be a dictionary containing the necessary key, value pairs that
            the response_generator can use to determine an approriate response from. 
    
        Args:
            tweets (Dict):
            tweet_parser (Callable): 
            
        Returns:
            parsed_tweets (Dict): Dictionary containing parsed tweets. Key=tweet_id, Values=...
            
        Example::
            >>> x
            >>> y
            
    """
    parsed_tweets = {}
    for idx, (id_str, tweet) in enumerate(tweets.items()):
        parsed_tweets[id_str] = tweet_parser(tweet, users)
    log.info(f"Successfully parsed {len([None for val in parsed_tweets.values() if val is not None])} tweets out of {len(tweets)}.")
        
    return parsed_tweets
 

def retweet(client:Any, parsed_tweets:Dict, max_requests:Optional[int]=100) -> None:
    """ Likes tweets using associated tweet id.
    
        Using max_likes may be necessary depending on whether you can afford to respect wait limits for all retrieved tweets.
        
        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 50 requests per 15-minute window per each authenticated user
    
        Args:
            X
            
        Returns:
            X
            
        Example::
            X
            
    """
    if max_requests:
        success = 0
        for idx, (id_str, parsed_tweets) in enumerate(parsed_tweets.items()):
            if parsed_tweets["response"]=="success":
                client.retweet(id_str)
                success += 1
            if success>=max_requests: break
    log.info(f"Retweeted {success} tweets.")
            
    
def reply(client:Any, parsed_tweets:Dict, response_generator:Callable) -> None:
    """ Replies to the author of the parsed tweet as dictated by the provided response_generator.
        
        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 200 requests per 15-minute window per each authenticated user
    
    
        Args:
            client (tweepy.Client): Registered and X client.
            parsed_tweets (Dict): Parsed tweet data in dictionary format.
                Key (str): Unique ID corresponding to the tweet.
                Value (Dict):
                    num_people (int):
                    created_at (str):
                    organization (str):
                    location (str): 
            response_generator (Callable): Callable function to generate response based on parsed tweet data.
            
        Returns:
            None
            
        Example::
            >>> tweets = search(...)
            >>> parsed_tweets = twiff.utils.parse.parse_tweets(tweets)
            >>> reply(client, parsed_tweets, ...) # ...
            
    """
    for idx, (id_str, parsed_tweet) in enumerate(parsed_tweets.items()):
        response = response_generator(parsed_tweet)
        client.create_tweet(in_reply_to_tweet_id=id_str, text=response)


def main(args) -> None:
    # Log
    log.info(f"Running search using following arguments: {args}")
    
    # Configuration
    with open(args.config, 'r') as fp:
        config = json.load(fp) 
    log.info(f"Loaded configuration: {config}")
    
    # Load API keys
    with open(args.keys, 'r') as fp:
        keys = json.load(fp)
    
    # Initialise tweepy client
    from tweepy import Client
    client = Client(keys['bearer_token'], keys['api_key'], keys['api_key_secret'], keys['access_token'], keys['access_token_secret'], 
                    return_type=dict, wait_on_rate_limit=True)
    
    # Perform search using provided query.
    tweets, users, errors, metadata = search(client=client, **config["search"]["config"])
    
    # Like retrieved tweets: like all retrieved tweets
    like(client=client, tweets=tweets, **config["like"]["config"])
       
    # Attempt to parse tweets using provided method: parse according to pre-determined format
    parsed_tweets = parse(tweets=tweets, users=users, tweet_parser=load_module(config, "parse"))
    
    # Retweet retrieved tweets: retweet successfully parsed tweets
    retweet(client=client, parsed_tweets=parsed_tweets, **config['retweet']['config'])
    
    # Reply to parsed tweets using generated response: reply to all tweets with different responses
    reply(client=client, parsed_tweets=parsed_tweets, response_generator=load_module(config, "respond"))
    
    # Export/dump data to disk for longer-term storage.
    load_module(config, "export", data={id_str:tweet for (id_str, tweet) in tweets.items()}, subdir="tweets")
    load_module(config, "export", data={id_str:user for (id_str, user) in users.items()}, subdir="users")
    load_module(config, "export", data={id_str:data["data"] for (id_str, data) in parsed_tweets.items()}, subdir="parsed-tweets")
    
    
def get_arg_parser():
    parser = argparse.ArgumentParser(description='Twitter Search', 
                                     epilog='Please contact Sam for further help.')    
    parser.add_argument('--config', type=str,
                        help='Configuration file for running the job.') 
    parser.add_argument('--keys', type=str,
                        help='Path for storing API keys.')   
    return parser
    
    
if __name__=='__main__':
    args = get_arg_parser().parse_args() 
    main(args)
