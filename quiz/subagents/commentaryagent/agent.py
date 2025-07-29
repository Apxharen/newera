from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime
import feedparser
import json
from bs4 import BeautifulSoup
import time


#TOOLS

def get_finance_markets(tool_context: ToolContext, custom_instruments: str = "") -> str:
    """
    Fetches the latest closing data and recent news for major futures, forex pairs, and cryptocurrencies,
    comparing current close to previous close, and returns financial market data.

    This function retrieves the last 2 trading days of data and recent news published within the
    last 8 hours. It calculates the percentage change between the most recent close and
    the previous close, formatting the information into category-based summary.

    Args:
        custom_instruments (str): Optional comma-separated list of additional Yahoo Finance ticker symbols
                                 to include in the data (e.g., "AAPL,MSFT,TSLA")

    Returns:
        str: A string containing the financial market data with news.
             Returns an error message if data cannot be fetched.
    """
    # Define the default instruments grouped by category
    default_instruments = {
        "Index Futures": {
            'NQ=F': "Nasdaq 100 Futures",
            'ES=F': "S&P 500 E-mini Futures",
            'YM=F': "Dow Jones 30 Futures",
            'NKD=F': "Nikkei 225 Futures",
            'FDAX=F': "DAX 40 Futures",
        },
        "Commodity Futures": {
            'CL=F': "WTI Crude Oil Futures",
            'BZ=F': "Brent Crude Oil Futures",
            'GC=F': "Gold (XAU/USD) Futures",
        },
        "Cryptocurrency": {
            'BTC-USD': "Bitcoin",
        },
        "Forex Pairs": {
            'EURUSD=X': "EUR/USD",
            'USDJPY=X': "USD/JPY",
            'USDCAD=X': "USD/CAD",
            'GBPUSD=X': "GBP/USD",
        }
    }

    # Collect all default tickers into a single list
    all_tickers = []
    for category in default_instruments:
        all_tickers.extend(list(default_instruments[category].keys()))

    # Add custom instruments if provided
    custom_tickers = []
    if custom_instruments.strip():
        custom_tickers = [ticker.strip().upper() for ticker in custom_instruments.split(',') if ticker.strip()]
        all_tickers.extend(custom_tickers)

    # Determine the time window for news (last 8 hours)
    current_time = datetime.now()
    eight_hours_ago_timestamp = int((current_time - timedelta(hours=8)).timestamp())

    try:
        # Download historical data for the last 5 trading days to ensure we get at least 2 closes
        data = yf.download(
            all_tickers,
            period="5d",
            interval="1d",
            progress=False
        )

        if data.empty or data['Close'].dropna(how='all').empty:
            return "Could not retrieve market data. Please try again later."

        # --- Calculate Percentage Change between most recent close and previous close ---
        close_prices = data['Close'].dropna(how='all')
        
        if len(close_prices) < 2:
            return "Insufficient market data available for comparison."
        
        # Get the last two trading days' closing prices
        most_recent_close = close_prices.iloc[-1]
        previous_close = close_prices.iloc[-2]
        percentage_change = ((most_recent_close - previous_close) / previous_close) * 100

        # Get the dates for the comparison
        most_recent_date = close_prices.index[-1].strftime('%Y-%m-%d')
        previous_date = close_prices.index[-2].strftime('%Y-%m-%d')

        # --- Build the Financial Markets String ---
        markets_data = f"Financial Markets Data (Close-to-Close Comparison):\n"
        markets_data += f"Latest Close ({most_recent_date}) vs Previous Close ({previous_date}) as of {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        markets_data += "=" * 70 + "\n\n"

        # Generate data for each default category
        for category, instruments in default_instruments.items():
            markets_data += f"--- {category} ---\n"
            for ticker, name in instruments.items():
                # --- Price Data ---
                if ticker in percentage_change.index and not pd.isna(percentage_change[ticker]):
                    current_price = most_recent_close[ticker]
                    change = percentage_change[ticker]
                    
                    if change > 0:
                        direction = f"+{change:.2f}%"
                    else:
                        direction = f"{change:.2f}%"
                        
                    markets_data += f"- {name}: {current_price:,.2f} ({direction})\n"
                else:
                    markets_data += f"- {name} ({ticker}): Data unavailable\n"

                # --- News Fetching ---
                try:
                    index_ticker = yf.Ticker(ticker)
                    news = index_ticker.news
                    
                    # Filter news for articles published in the last 8 hours
                    recent_news = [
                        article for article in news 
                        if article.get('provider_publish_time', 0) > eight_hours_ago_timestamp
                    ]
                    
                    if recent_news:
                        # The news list is already sorted, so the first item is the most recent
                        latest_article = recent_news[0]
                        title = latest_article['title']
                        publisher = latest_article['publisher']
                        markets_data += f"  📰 Recent News ({publisher}): \"{title}\"\n"
                except Exception:
                    # Silently pass if news fetching fails for one ticker
                    pass
            markets_data += "\n"

        # Add custom instruments section if any were provided
        if custom_tickers:
            markets_data += "--- Custom Instruments ---\n"
            for ticker in custom_tickers:
                if ticker in percentage_change.index and not pd.isna(percentage_change[ticker]):
                    current_price = most_recent_close[ticker]
                    change = percentage_change[ticker]
                    
                    if change > 0:
                        direction = f"+{change:.2f}%"
                    else:
                        direction = f"{change:.2f}%"
                        
                    markets_data += f"- {ticker}: {current_price:,.2f} ({direction})\n"
                else:
                    markets_data += f"- {ticker}: Data unavailable\n"

                # --- News Fetching for custom instruments ---
                try:
                    custom_ticker_obj = yf.Ticker(ticker)
                    news = custom_ticker_obj.news
                    
                    recent_news = [
                        article for article in news 
                        if article.get('provider_publish_time', 0) > eight_hours_ago_timestamp
                    ]
                    
                    if recent_news:
                        latest_article = recent_news[0]
                        title = latest_article['title']
                        publisher = latest_article['publisher']
                        markets_data += f"  📰 Recent News ({publisher}): \"{title}\"\n"
                except Exception:
                    pass
            markets_data += "\n"

        return markets_data

    except Exception as e:
        return f"An error occurred while fetching market data: {e}"


def news_summary(tool_context: ToolContext, num_articles: int = 5) -> str:
    """
    Fetches the most recent top financial news articles from the Yahoo Finance RSS feed.

    This function retrieves the latest news headlines, summaries, and links. It is useful for getting a quick overview of the most important events currently affecting the financial markets.

    Args:
        num_articles (int): The number of recent news articles to retrieve. Defaults to 5.

    Returns:
        str: A JSON string representing a list of dictionaries. Each dictionary contains details for a single news article, including 'title', 'link', 'published_utc', and 'summary'. Returns an error message if the feed cannot be fetched.
    """
    YAHOO_FINANCE_RSS_URL = "https://finance.yahoo.com/rss/topstories"
    
    try:
        # Parse the RSS feed
        feed = feedparser.parse(YAHOO_FINANCE_RSS_URL)

        if feed.bozo:
            # Bozo bit is set to 1 if the feed is malformed
            raise Exception(f"Error parsing RSS feed: {feed.bozo_exception}")

        news_list = []
        # Limit the number of articles to process
        articles_to_process = feed.entries[:num_articles]

        for entry in articles_to_process:
            # Try to get summary from different possible attributes
            summary_text = ""
            if hasattr(entry, 'summary'):
                # The summary often contains HTML, use BeautifulSoup to clean it
                soup = BeautifulSoup(entry.summary, 'html.parser')
                summary_text = soup.get_text()
            elif hasattr(entry, 'description'):
                # Sometimes it's called description instead
                soup = BeautifulSoup(entry.description, 'html.parser')
                summary_text = soup.get_text()
            elif hasattr(entry, 'content'):
                # Or it might be in content
                if isinstance(entry.content, list) and len(entry.content) > 0:
                    soup = BeautifulSoup(entry.content[0].value, 'html.parser')
                    summary_text = soup.get_text()
                else:
                    soup = BeautifulSoup(str(entry.content), 'html.parser')
                    summary_text = soup.get_text()
            else:
                # Fallback to title if no summary is available
                summary_text = "No summary available"
            
            # published_parsed is a time.struct_time, convert to ISO 8601 UTC string
            published_time_struct = entry.get('published_parsed', time.gmtime())
            published_datetime = datetime.fromtimestamp(time.mktime(published_time_struct))
            
            news_item = {
                "title": entry.title,
                "link": entry.link,
                "published_utc": published_datetime.isoformat() + "Z",
                "summary": summary_text.strip()
            }
            news_list.append(news_item)
            
        return json.dumps(news_list, indent=2)

    except Exception as e:
        error_message = {
            "error": "Failed to fetch or parse financial news.",
            "details": str(e)
        }
        return json.dumps(error_message, indent=2)


#AGENTS
commentaryagent = Agent(
    name="CommentaryAgent",
    instruction="""
    You are a financial markets agent specialized in providing comprehensive market analysis and news summaries.
    
    You have two tools:
    
    1. get_finance_markets - Provides financial markets data for:
       DEFAULT INSTRUMENTS:
       - Index Futures: Nasdaq 100, S&P 500 E-mini, Dow Jones 30, Nikkei 225, DAX 40
       - Commodity Futures: WTI Crude Oil, Brent Crude Oil, Gold (XAU/USD)
       - Cryptocurrency: Bitcoin
       - Forex Pairs: EUR/USD, USD/JPY, USD/CAD, GBP/USD
       
       CUSTOM INSTRUMENTS:
       If a user requests data for instruments NOT in the default list above, you can pass them as custom_instruments parameter using Yahoo Finance ticker symbols (comma-separated).

    2. news_summary - Fetches the latest financial news from Yahoo Finance RSS feed
    
    INSTRUCTIONS:
    When users request market information, you should:
    1. Call news_summary() to get latest financial news
    2. Call get_finance_markets() (with custom_instruments if needed for specific requests)
    3. Present the information in TWO clear sections:
    
    📰 NEWS SUMMARY:
    - Summarize the key financial news in exactly 2 bullet points based on the news_summary results
    
    📈 FINANCE MARKETS:
    - Present the financial markets data from get_finance_markets
    
    USAGE EXAMPLES:
    - Standard request: Call both tools without parameters
    - Custom instruments: Call get_finance_markets(custom_instruments="AAPL,MSFT,TSLA") for specific stocks
    - Always provide both news and markets sections in your response
    """,
    description="Provides comprehensive financial market data and news summaries with close-to-close price comparisons and latest financial news.",
    tools=[get_finance_markets, news_summary],
)