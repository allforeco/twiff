import json

from pathlib import Path

from typing import *

class ReplyGenerator:
    """ ...
    """
    def __init__(self, path:str) -> None:
        self.path = Path(path)
        with open(self.path, 'r') as fp:
            self.responses = json.load(fp)
    
    def __call__(self, parsed_tweet:Dict) -> str:
        """ Generate reponse based on parsed_tweet.
        
            Args:
                parsed_tweet (Dict): Parsed tweet
                    response (str): Type of response suggested.
                    data (Dict): Parsed data.
                    
            Returns:
                response (str): Response text for the reply tweet.
        """
        if parsed_tweet['response']=='success':
            return self.responses['tweet-parse-success']
        else:
            return self.responses['tweet-parse-failed']
        
# -----------------------------------------------------
# ---------------- New code from here -----------------
# -----------------------------------------------------

# Added _v2 to the new methods as some conflict with existing methods

class ReplyGenerator_v2:
    """ ...
    """

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        with open(self.path, 'r') as fp:
            self.responses = json.load(fp)

    def __call__(self, parsed_tweet: Dict) -> str:
        """ Generate response based on parsed_tweet.

            Args:
                parsed_tweet (Dict): Parsed tweet
                    response (str): Type of response suggested.
                    data (Dict): Parsed data.

            Returns:
                response (str): Response text for the reply tweet.
        """

        # Find the correct response
        sResponseType = "tweet-parse-" + parsed_tweet['response']
        if parsed_tweet['response'] == 'success':
            if "tweettype" in parsed_tweet:
                sResponse = self.responses[sResponseType + "-" + parsed_tweet["tweettype"]]
                return sResponse.format(parsed_tweet["data"]["num_people"], parsed_tweet["data"]["location"],
                                        parsed_tweet["data"]["organization"])
            else:
                return self.responses[sResponseType]
        else:
            if "errors" in parsed_tweet:
                if "no_org_found" in parsed_tweet["errors"]:
                    sResponse = self.responses[sResponseType + "-no_org_found"]
                    return sResponse.format(parsed_tweet["data"]["organization"])
                if "no_country_found" in parsed_tweet["errors"]:
                    sResponse = self.responses[sResponseType + "-no_country_found"]
                    return sResponse.format(parsed_tweet["data"]["location"])
                if "no_city_found" in parsed_tweet["errors"]:
                    sResponse = self.responses[sResponseType + "-no_city_found"]
                    return sResponse.format(parsed_tweet["data"]["location"])
                if "no_people_found" in parsed_tweet["errors"]:
                    sResponse = self.responses[sResponseType + "-no_people_found"]
                    return sResponse.format(parsed_tweet["data"]["num_people"])
            else:
                return self.responses['tweet-parse-failed']
