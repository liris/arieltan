import twython
import time
import random
import simplejson, urllib
import logging
import sys


logger = logging.getLogger()
class Arieltan(object):
    def __init__(self, cfg, username, password):
        self.username = username
        self.twitter = twython.core.setup(username = username, password = password)
        self.cfg = cfg

    def post(self, filename):
        messages = open(filename).readlines()
        total = len(messages)
        message = unicode(random.choice(messages), "utf-8")
        message = message.strip()
        logger.info("post message: " + message)
        status = self.twitter.updateStatus(message)

    def follow(self):
        friends = self.twitter.getFriendsStatus(screen_name=self.username)
        followers = self.twitter.getFollowersStatus(screen_name=self.username)
        for follower in followers["users"]:
            if follower not in friends["users"]:
                logger.info("creating friendship with %s ..."  % follower["screen_name"])
                self.twitter.createFriendship(follower["id"])
                msg = self.cfg.get("greeting", "follow") % follower["screen_name"]
                msg = unicode(msg, "utf-8")
                status = self.twitter.updateStatus(msg)
                logger.info("created friendship")

    def _pop(self, statuses, match_func):
        if not statuses:
            return None
        while len(statuses):
            status = statuses.pop(0)
            if match_func(status):
                return status
            return None
    
    def retweet(self):
        statuses = self.twitter.getFriendsTimeline()
        def match(st):
            return st["user"]["screen_name"] != self.username
        
        status = self._pop(statuses, match)
        if not status:
            return
        status = self.twitter.reTweet(status["id"])
        logger.info("retweet " + str(status["id"]))

    def retweetByUser(self, user_names):
        retweeted = self.twitter.retweetedByMe()
        ids = [item["id"] for item in retweeted]
        for screen_name in user_names:
            statuses = self.twitter.getUserTimeline(screen_name=screen_name)
            id_ = statuses[0]["id"]
            if id_ not in ids:
                self.twitter.reTweet(id_)
                
    def searchRetweet(self):
        terms = self.cfg.get("search", "terms").split(",")
        term = random.choice(terms)
        logger.info("term: " + term)
        results = self.twitter.searchTwitter(term, lang=self.cfg.get("search", "lang"))
        logger.info("search result %d" % len(results))
        def match(st):
            return st["from_user"] != self.username
        
        status = self._pop(results["results"], match)
        if not status:
            return
        status = self.twitter.reTweet(status["id"])
        logger.info("retweet " + str(status["id"]) + " for " + term)
        
def wait_next_post(factor=1):
    wait_time = random.randint(60, 3600/factor)
    logger.info("waiting " + str(wait_time/60) + " mins...")
    time.sleep(wait_time)

def get_config():
    import ConfigParser
    parser = ConfigParser.SafeConfigParser()
    parser.read("config.ini")

    return parser
    
def main(argv):
    if len(argv) < 3:
        print argv[0] + " username pasword"
        return
    random.seed()
    cfg = get_config()
    retweet_ratio = cfg.getint("global", "retweet_ratio") -1
    retweet_wait_factor = cfg.getint("global", "retweet_wait_factor")
    search_ratio = cfg.getint("global", "search_ratio")
    tenki_ratio = cfg.getint("global", "tenki_ratio")
    arieltan = Arieltan(cfg, argv[1], argv[2])
    while True:
        try:
            arieltan.post("message.txt")
            arieltan.follow()
            if random.randint(0, tenki_ratio) == 0:
                arieltan.retweetByUser(["tenkijp", "tenki_tokyo"])
            for i in range(random.randint(0,retweet_ratio)):
                wait_next_post(retweet_wait_factor)
                if random.randint(0, search_ratio) == 0:
                    arieltan.retweet()
                else:
                    arieltan.searchRetweet()
            wait_next_post(retweet_wait_factor)
        except KeyboardInterrupt:
            return
        except Exception, e:
            logger.error(e)
            import traceback
            traceback.print_exc()
            wait_next_post()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
    logger.setLevel(logging.INFO)
    main(sys.argv)
