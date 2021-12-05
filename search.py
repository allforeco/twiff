import os
import sys
import tweepy
import logging
import datetime
import argparse

from utils import *
from typing import *

log = logging.getLogger(__name__)

def main(args:Dict) -> None:
    # Prepare cursors for retrieving tweets.
    new_cursor = Cursor()
    old_cursor = Cursor(args.cursor_path)
    
    retrieved_count = 0
    
    # Load API keys
    keys = Keys(args.key_path)

    # Initialise tweepy client
    client = tweepy.Client(keys.bearer_token, 
                           keys.api_key, keys.api_key_secret, 
                           keys.access_token, keys.access_token_secret,
                           return_type=dict, wait_on_rate_limit=True
                          )
    
    # Search for tweets
    for idx in range(args.max_tweets//args.max_results):
        log.info('----- [ Request {} ] -----'.format(idx+1))
        
        # Make search request...
        responses = client.search_recent_tweets(query=args.query, 
                                                expansions=['author_id', 'entities.mentions.username', 'geo.place_id', 'in_reply_to_user_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id'],
                                                max_results=10, 
                                                place_fields=['country', 'country_code', 'full_name', 'geo', 'id', 'name', 'place_type'],
                                                since_id=old_cursor._newest_id(),
                                                tweet_fields=['author_id', 'conversation_id', 'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id', 'lang', 'referenced_tweets', 'reply_settings', 'source', 'text', 'withheld'],
                                                until_id=new_cursor._oldest_id(),
                                                user_fields=['created_at', 'description', 'entities', 'id', 'location', 'name', 'url', 'username', 'verified', 'withheld'],
                                               )

        # Process response...
        results = Results(responses) 
        retrieved_count += results.metadata.result_count

        # Exit condition...
        if results.metadata.result_count:
            new_cursor._update(results.metadata.oldest_id, results.metadata.newest_id)
            results._dump(args.export_dir)
        else:
            if not new_cursor._isnull(): new_cursor._dump(args.cursor_path)
            log.info('Search complete, found {} tweets. Exiting...'.format(retrieved_count))
            break
    
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Twitter Search', 
                                     epilog='Please contact Sam Cantrill at sam.cantrill@gmail.com for further help.')
    
    parser.add_argument('--key_path', type=str, default='keys.json',
                        help='Path for storing API keys.')
    parser.add_argument('--cursor_path', type=str, default='cursor.json',
                        help='Path for storing cursor data.')
    
    parser.add_argument('--export_dir', type=str, default='exports',
                        help='Directory to export items to.')
    parser.add_argument('--log_dir', type=str, default='logs',
                        help='Directory to log runs to.')
    
    parser.add_argument('--query', type=str, default='(#twiff OR #Twiff) -is:retweet',
                        help='Query made to the Twitter API v2 service.') 
    
    parser.add_argument('--max_results', type=int, default=100,
                        help='Maximum number of results per page.') 
    parser.add_argument('--max_tweets', type=int, default=1000,
                        help='Maximum number of tweets per search.') 
    
    args = parser.parse_args()
                        
    # Create logging directory
    if not os.path.exists(args.log_dir): os.mkdir(args.log_dir)

    logging.basicConfig(format='[ %(asctime)s ] %(name)s (%(levelname)s): %(message)s', 
                        filename='{}/twiff_{}.log'.format(args.log_dir, datetime.datetime.now().strftime("%m%d%Y_%H%M%S")),
                        level=logging.INFO)
    
    # Log arguments
    log.info(args)
                        
    sys.exit(main(args))