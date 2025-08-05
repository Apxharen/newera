from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime
import feedparser
import json
from bs4 import BeautifulSoup
import time


async def get_finance_markets(tool_context: ToolContext, custom_instruments: str = "") -> str:
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
    # Define the default instruments grouped by category - use most reliable tickers
    default_instruments = {
        "Cryptocurrency": {
            'BTC-USD': "Bitcoin",
            'ETH-USD': "Ethereum",
            'ADA-USD': "Cardano",
        },
        "Major Stocks": {
            'AAPL': "Apple Inc.",
            'MSFT': "Microsoft Corporation", 
            'GOOGL': "Alphabet Inc.",
            'TSLA': "Tesla Inc.",
            'AMZN': "Amazon.com Inc.",
            'META': "Meta Platforms Inc.",
        },
        "Major Indices": {
            '^GSPC': "S&P 500",
            '^DJI': "Dow Jones Industrial Average",
            '^IXIC': "NASDAQ Composite",
        },
        "Forex Pairs": {
            'EURUSD=X': "EUR/USD",
            'GBPUSD=X': "GBP/USD",
            'USDJPY=X': "USD/JPY",
        },
        "Commodity Futures": {
            'GC=F': "Gold Futures",
            'CL=F': "WTI Crude Oil Futures",
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
        # Build results dictionary to store individual ticker data
        ticker_data = {}
        successful_tickers = []
        
        # Fetch data for each ticker individually with retry logic
        for ticker in all_tickers:
            try:
                # Download data for individual ticker
                individual_data = yf.download(
                    ticker,
                    period="2d",  # Shorter period for better reliability
                    interval="1d",
                    progress=False,
                    auto_adjust=True
                )
                
                if not individual_data.empty and 'Close' in individual_data.columns:
                    close_prices = individual_data['Close'].dropna()
                    if len(close_prices) >= 2:
                        current_price = float(close_prices.iloc[-1])
                        previous_price = float(close_prices.iloc[-2])
                        change_pct = float(((current_price - previous_price) / previous_price) * 100)
                        
                        ticker_data[ticker] = {
                            'current_price': current_price,
                            'previous_price': previous_price,
                            'change_pct': change_pct,
                            'date': close_prices.index[-1].strftime('%Y-%m-%d')
                        }
                        successful_tickers.append(ticker)
                    elif len(close_prices) == 1:
                        # Only current price available
                        current_price = float(close_prices.iloc[-1])
                        ticker_data[ticker] = {
                            'current_price': current_price,
                            'previous_price': None,
                            'change_pct': None,
                            'date': close_prices.index[-1].strftime('%Y-%m-%d')
                        }
                        successful_tickers.append(ticker)
            except Exception as e:
                print(f"Failed to fetch data for {ticker}: {e}")
                continue
        
        if not successful_tickers:
            return "Could not retrieve any market data. Please try again later."
        
        # Get the most recent date from successful tickers
        most_recent_date = ticker_data[successful_tickers[0]]['date']

        # --- Build the Financial Markets String ---
        markets_data = f"Financial Markets Data:\n"
        markets_data += f"Latest data as of {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        markets_data += "=" * 60 + "\n\n"

        # Generate data for each default category
        for category, instruments in default_instruments.items():
            markets_data += f"--- {category} ---\n"
            category_has_data = False
            
            for ticker, name in instruments.items():
                if ticker in ticker_data:
                    data = ticker_data[ticker]
                    current_price = data['current_price']
                    
                    # Format price change if available
                    if data['change_pct'] is not None:
                        change = data['change_pct']
                        if change > 0:
                            direction = f"+{change:.2f}%"
                        else:
                            direction = f"{change:.2f}%"
                        markets_data += f"- {name}: ${current_price:,.2f} ({direction})\n"
                    else:
                        markets_data += f"- {name}: ${current_price:,.2f} (change unavailable)\n"
                    
                    category_has_data = True
                    
                    # --- News Fetching (only for successful tickers) ---
                    try:
                        ticker_obj = yf.Ticker(ticker)
                        news = ticker_obj.news
                        
                        # Filter news for articles published in the last 8 hours
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
                        # Silently pass if news fetching fails
                        pass
                else:
                    markets_data += f"- {name} ({ticker}): Data unavailable\n"
            
            if not category_has_data:
                markets_data += "  No data available for this category\n"
            markets_data += "\n"

        # Add custom instruments section if any were provided
        if custom_tickers:
            markets_data += "--- Custom Instruments ---\n"
            for ticker in custom_tickers:
                if ticker in ticker_data:
                    data = ticker_data[ticker]
                    current_price = data['current_price']
                    
                    if data['change_pct'] is not None:
                        change = data['change_pct']
                        if change > 0:
                            direction = f"+{change:.2f}%"
                        else:
                            direction = f"{change:.2f}%"
                        markets_data += f"- {ticker}: ${current_price:,.2f} ({direction})\n"
                    else:
                        markets_data += f"- {ticker}: ${current_price:,.2f} (change unavailable)\n"
                    
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
                else:
                    markets_data += f"- {ticker}: Data unavailable\n"
            markets_data += "\n"

        return markets_data

    except Exception as e:
        error_msg = f"An error occurred while fetching market data: {e}"
        return error_msg


finance_markets_agent = Agent(
    name="FinanceMarketsAgent", 
    model="gemini-2.5-flash",
    instruction="""
    You are a financial markets data specialist focused on retrieving and presenting market information.
    
    Your role:
    1. Use the get_finance_markets tool to fetch current financial market data including:
       - Cryptocurrency (Bitcoin, Ethereum, Cardano) - Most reliable data source
       - Major Stocks (Apple, Microsoft, Google, Tesla, Amazon, Meta) - High-volume stocks
       - Major Indices (S&P 500, Dow Jones, NASDAQ Composite) - Core market indicators
       - Forex Pairs (EUR/USD, GBP/USD, USD/JPY) - Major currency pairs
       - Commodity Futures (Gold, WTI Crude Oil) - Key commodities
    
    2. The tool fetches data individually for each ticker to maximize reliability
    
    3. Return the complete market data as your response - it will be automatically saved to session state
    
    When called, immediately use the get_finance_markets tool and return the complete market data.
    """,
    description="Fetches comprehensive financial market data including futures, forex, crypto, and recent market news.",
    tools=[get_finance_markets],
    output_key="finance_markets_data",
)