import json
import logging
from pathlib import Path

from typing import *

from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class ReplyGenerator(ABC):
    """ ...
    """
    def __init__(self, path:str) -> None:
        self.path = Path(path)
        with open(self.path, 'r') as fp:
            self.responses = json.load(fp)
    
    @abstractmethod
    def __call__(self, parsed_tweet:Dict) -> str:
        """ Generate reponse based on parsed_tweet.
        
            Args:
                parsed_tweet (Dict): Parsed tweet
                    response (str): Type of response suggested.
                    data (Dict): Parsed data.
                    
            Returns:
                response (str): Response text for the reply tweet.
                
            Example::
                >>> if parsed_tweet['response']=='success':
                        return self.responses['tweet-parse-success']
                    else:
                        return self.responses['tweet-parse-failed']
        """
        pass

    
class T4FReplyGenerator(ReplyGenerator):
    """ INSERT CLASS DESCRIPTION & ARGUMENTS + EXAMPLE HERE
    
    """

    def __init__(self, path: str) -> None:
        '''
        Initialise the ReplyGenerator instance.
        '''
        super(T4FReplyGenerator, self).__init__(path)

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
        sResponseType = "tweet-parse-" + parsed_tweet["response"]
        if parsed_tweet["response"] == "success":
            if "tweettype" in parsed_tweet:
                sResponse = self.responses[sResponseType + "-" + parsed_tweet["tweettype"]]
                if parsed_tweet["data"]["num_people"] == 1:
                    sPerson = "person"
                else:
                    sPerson = "people"
                return sResponse.format(parsed_tweet["data"]["num_people"],
                                        sPerson,
                                        parsed_tweet["data"]["location"],
                                        parsed_tweet["data"]["organization"],
                                        parsed_tweet["data"]["url"])
            else:
                return self.responses[sResponseType]
        else:
            if "errors" in parsed_tweet:
                if parsed_tweet["errors"] is not None:
                    sResponse = self.responses[sResponseType + "-" + parsed_tweet["errors"][0]]
                    if sResponse == "":
                        return None
                    return sResponse.format(parsed_tweet["data"]["organization"],
                                            parsed_tweet["data"]["location"],
                                            parsed_tweet["data"]["num_people"])
                else:
                    return self.responses['tweet-parse-failed']
            else:
                return self.responses['tweet-parse-failed']