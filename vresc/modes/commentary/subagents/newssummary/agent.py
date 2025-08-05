from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import feedparser
import json
from bs4 import BeautifulSoup
import time
from datetime import datetime
import requests
from urllib.parse import urljoin, urlparse


async def news_summary(tool_context: ToolContext, num_articles: int = 5) -> str:
    """
    Fetches the most recent top financial news articles from the Yahoo Finance RSS feed and retrieves their full content.

    This function retrieves the latest news headlines and fetches the full article content from each link. The articles are returned directly to the LLM for analysis and summarization.

    Args:
        num_articles (int): The number of recent news articles to retrieve and fetch content for. Defaults to 5.

    Returns:
        str: A formatted string containing all the fetched articles with their titles, publication dates, links, and full content. Each article is clearly separated and numbered for easy processing.
    """
    YAHOO_FINANCE_RSS_URL = "https://finance.yahoo.com/rss/topstories"
    
    try:
        # Parse the RSS feed
        feed = feedparser.parse(YAHOO_FINANCE_RSS_URL)

        if feed.bozo:
            # Bozo bit is set to 1 if the feed is malformed
            raise Exception(f"Error parsing RSS feed: {feed.bozo_exception}")

        articles_list = []
        # Limit the number of articles to process
        articles_to_process = feed.entries[:num_articles]

        for entry in articles_to_process:
            # Get basic article info
            published_time_struct = entry.get('published_parsed', time.gmtime())
            published_datetime = datetime.fromtimestamp(time.mktime(published_time_struct))
            
            # Try to fetch full article content
            full_content = ""
            try:
                # Add headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(entry.link, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to extract main content - Yahoo Finance articles usually have content in specific divs
                # Look for common content containers
                content_selectors = [
                    '[data-module="ArticleBody"]',
                    '.caas-body',
                    '.article-body',
                    '[data-test-locator="ArticleBody"]',
                    '.story-body',
                    'article'
                ]
                
                content_found = False
                for selector in content_selectors:
                    content_elements = soup.select(selector)
                    if content_elements:
                        # Extract text from all paragraphs in the content area
                        paragraphs = content_elements[0].find_all('p')
                        if paragraphs:
                            full_content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                            content_found = True
                            break
                
                # Fallback: if no specific content area found, try to get all paragraphs
                if not content_found:
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        # Filter out very short paragraphs (likely navigation/footer text)
                        meaningful_paragraphs = [p.get_text().strip() for p in paragraphs 
                                               if len(p.get_text().strip()) > 50]
                        if meaningful_paragraphs:
                            full_content = ' '.join(meaningful_paragraphs[:10])  # Limit to first 10 substantial paragraphs
                
                # If still no content, fall back to RSS summary
                if not full_content:
                    if hasattr(entry, 'summary'):
                        soup_summary = BeautifulSoup(entry.summary, 'html.parser')
                        full_content = soup_summary.get_text().strip()
                    else:
                        full_content = "Content could not be extracted from this article."
                        
            except Exception as content_error:
                # If content fetching fails, use RSS summary as fallback
                if hasattr(entry, 'summary'):
                    soup_summary = BeautifulSoup(entry.summary, 'html.parser')
                    full_content = soup_summary.get_text().strip()
                else:
                    full_content = f"Error fetching article content: {str(content_error)}"
            
            article_item = {
                "title": entry.title,
                "link": entry.link,
                "published_utc": published_datetime.isoformat() + "Z",
                "content": full_content
            }
            articles_list.append(article_item)
            
        # Return the articles data directly to the LLM for processing
        articles_text = "Here are the fetched financial news articles:\n\n"
        
        for i, article in enumerate(articles_list, 1):
            articles_text += f"=== ARTICLE {i} ===\n"
            articles_text += f"Title: {article['title']}\n"
            articles_text += f"Published: {article['published_utc']}\n"
            articles_text += f"Link: {article['link']}\n"
            articles_text += f"Content: {article['content']}\n\n"
        
        return articles_text

    except Exception as e:
        return f"Error fetching financial news: {str(e)}\nPlease try again or check if the news source is accessible."


news_summary_agent = Agent(
    name="NewsSummaryAgent",
    model="gemini-2.5-flash", 
    instruction="""
    You are a financial news specialist focused on gathering and summarizing the latest financial news.
    
    Your workflow:
    1. Use the news_summary tool to fetch the most recent 5 financial news articles with their full content from Yahoo Finance RSS feed

    2. Read the raw articles data and provide very detailed summaries of the articles. Structure your output as
        "Article 1: <summary of article 1>, Article 2: <summary of article 2>, Article 3: <summary of article 3>, Article 4: <summary of article 4>, Article 5: <summary of article 5>"
    """,
    description="Fetches financial news articles, summarizes them using LLM analysis, and saves structured summaries.",
    tools=[news_summary],
    output_key="news_summary_data",
)