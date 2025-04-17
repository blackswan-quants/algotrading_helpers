# region imports
from AlgorithmImports import *
from nltk.sentiment import SentimentIntensityAnalyzer
# endregion

# region imports
from AlgorithmImports import *
from nltk.sentiment import SentimentIntensityAnalyzer
# endregion

class Study5CustomData(QCAlgorithm):
    """
    # Tesla Trading Algorithm Based on Musk Tweet Sentiment

    ## Algorithm Overview
    This algorithm trades TSLA stock based on sentiment analysis of Elon Musk's tweets.
    It takes long positions on positive sentiment and short positions on negative sentiment
    when tweets specifically mention Tesla or TSLA.

    ## Strategy Logic
    - Analyzes Elon Musk's tweets using NLTK's SentimentIntensityAnalyzer
    - Takes 100% long position when sentiment score > 0.5
    - Takes 100% short position when sentiment score < -0.5
    - Only considers tweets containing "tesla" or "tsla" (case insensitive)
    - Liquidates all positions 15 minutes before market close each day

    ## Data Sources
    - TSLA equity data at minute resolution
    - Custom data source of preprocessed Elon Musk tweets

    ## Parameters
    - Backtest period: November 1, 2012 to January 1, 2017
    - Initial capital: $100,000
    - Sentiment thresholds: ±0.5 for triggering trades
    """

    def initialize(self):
        """
        Initialize the algorithm with required settings and data subscriptions.
        
        This method:
        - Sets the backtest time period
        - Configures initial capital
        - Adds TSLA equity and Musk tweet data sources
        - Schedules the daily position exit before market close
        """
        self.set_start_date(2012, 11, 1)
        self.set_end_date(2017, 1, 1)
        self.set_cash(100000)

        self._tsla = self.add_equity("TSLA", Resolution.MINUTE).symbol
        self._musk = self.add_data(MuskTweet, "MUSKTWTS", Resolution.MINUTE).symbol

        self.schedule.on(self.date_rules.every_day(self._tsla),
        self.time_rules.before_market_close(self._tsla, 15),
        self._exit_positions)

    def on_data(self, data: Slice):
        """
        Process incoming data slices containing Musk tweet information.
        
        This method is called each time new data arrives and:
        - Extracts sentiment score and tweet content when Musk tweet data is available
        - Takes a 100% long position when sentiment score > 0.5
        - Takes a 100% short position when sentiment score < -0.5
        - Logs significant tweets (with absolute sentiment > 0.5)
        
        Parameters:
            data (Slice): Data slice containing market and custom data
        """
        if self._musk in data:
            score = data[self._musk].value
            content = data[self._musk].Tweet_value

        if score > 0.5:
            self.set_holdings(self._tsla, 1)
        elif score < -0.5:
            self.set_holdings(self._tsla, -1)

        if abs(score) > 0.5:
            self.log(f"score: {str(score)}, Tweet_Value: {content}")

    def _exit_positions(self):
        """
        Liquidate all positions in the portfolio.
        
        This method is scheduled to run 15 minutes before market close each day
        to ensure we don't hold positions overnight.
        """
        self.liquidate()

class MuskTweet(PythonData):
    """
    # MuskTweet Custom Data Source
    
    Custom data reader for processing Elon Musk tweet data. This class:
    - Retrieves preprocessed tweet data from a remote source
    - Performs sentiment analysis using NLTK
    - Filters tweets to only consider those mentioning Tesla or TSLA
    - Implements look-ahead bias prevention by adjusting timestamps
    
    The sentiment score is stored in the 'value' property, while the
    tweet content is stored in the 'Tweet_value' property.
    """

    sia = SentimentIntensityAnalyzer()

    def get_source(self, config, date, is_live_mode):
        """
        Provide the source URL for the Musk tweet data.
        
        This method returns a SubscriptionDataSource object pointing to the
        remote CSV file containing preprocessed Musk tweets.
        
        Parameters:
            config: Configuration for the data subscription
            date: Date for which we're requesting data
            is_live_mode: Boolean indicating if algorithm is running in live mode
            
        Returns:
            SubscriptionDataSource: Data source for the Musk tweets
        """
        source = "https://www.dropbox.com/scl/fi/7ff4n6bvzqnpl2r1poayp/MuskTweetsPreProcessed.csv?rlkey=15aamdr7fz8tb38ebosfuao0q&e=2&st=2xdff53b&dl=1"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.REMOTE_FILE)

    def reader(self, config, line, date, is_live_mode):
        """
        Process each line of the data file into a MuskTweet object.
        
        This method:
        - Parses the CSV line into timestamp and tweet content
        - Adds a 1-minute time adjustment to prevent look-ahead bias
        - Performs sentiment analysis if tweet contains "tesla" or "tsla"
        - Stores both the sentiment score and original tweet content
        
        Parameters:
            config: Configuration for the data subscription
            line: Single line from the data source
            date: Date for which we're processing data
            is_live_mode: Boolean indicating if algorithm is running in live mode
            
        Returns:
            MuskTweet: Processed tweet data object or None if line is invalid
        """
        if not(line.strip() and line[0].isdigit()):
            return None


        data = line.split(",")
        tweet = MuskTweet()

        try:
            tweet.symbol = config.symbol
            # adjusting to the end time of the data to overcome look-ahead bias
            tweet.time = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") + timedelta(minutes = 1)
            content = data[1].lower()

            if "tsla" in content or "tesla" in content:
                tweet.value = self.sia.polarity_scores(content)["compound"]
            else:
                tweet.value = 0

            tweet["Tweet_value"] = str(content)

        except ValueError:
            return None

        return tweet