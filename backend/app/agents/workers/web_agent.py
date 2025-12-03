from typing import Dict, Any, List, Optional
import logging
import aiohttp
import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from ...llm.lmstudio_client import lmstudio_client

logger = logging.getLogger(__name__)

class WebAgent:
    """Agent for web scraping and analysis"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.agent_type = "web"
        self.supported_tasks = [
            "scrape_website",
            "extract_structured_data",
            "analyze_web_content"
        ]
        self.supported_tasks.append("analyze_section")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def process(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a web-related task with the given parameters"""
        if task_type not in self.supported_tasks:
            raise ValueError(f"Unsupported task type: {task_type}")
        
        logger.info(f"Processing {task_type} with parameters: {parameters}")
        
        # Route to the appropriate handler method
        handler = getattr(self, f"handle_{task_type}", None)
        if not handler or not callable(handler):
            raise NotImplementedError(f"No handler for task type: {task_type}")
        
        return await handler(parameters)
    
    async def fetch_url(self, url: str) -> str:
        """Fetch the content of a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise
    
    async def handle_scrape_website(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape content from a website"""
        url = parameters.get("url", "")
        max_pages = parameters.get("max_pages", 1)
        
        if not url:
            raise ValueError("No URL provided for scraping")
        
        # Parse the base URL
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Fetch the initial page
        content = await self.fetch_url(url)
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract main content (this is a simple example - you might want to customize this)
        text_content = ' '.join([p.get_text().strip() for p in soup.find_all('p')])
        
        # Extract links if we're crawling multiple pages
        links = []
        if max_pages > 1:
            # Get all links from the page
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Convert relative URLs to absolute
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                # Only follow links from the same domain
                if urlparse(href).netloc == parsed_url.netloc:
                    links.append(href)
            
            # Limit the number of pages to crawl
            links = list(set(links))[:max_pages - 1]
            
            # Fetch additional pages
            additional_pages = await asyncio.gather(
                *[self.fetch_url(link) for link in links],
                return_exceptions=True
            )
            
            # Process additional pages
            for page_content in additional_pages:
                if isinstance(page_content, Exception):
                    logger.warning(f"Error fetching page: {page_content}")
                    continue
                
                page_soup = BeautifulSoup(page_content, 'html.parser')
                text_content += ' ' + ' '.join([p.get_text().strip() for p in page_soup.find_all('p')])
        
        return {
            "url": url,
            "content": text_content,
            "links_crawled": len(links) + 1,  # +1 for the initial page
            "metadata": {
                "domain": parsed_url.netloc,
                "content_type": "text/plain",
                "content_length": len(text_content)
            }
        }
    
    async def handle_extract_structured_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from web content"""
        content = parameters.get("content", "")
        
        if not content:
            # If no content provided, try to fetch from URL
            url = parameters.get("url")
            if not url:
                raise ValueError("Either 'content' or 'url' must be provided")
            
            content = await self.fetch_url(url)
        
        # Use LLM to extract structured data
        prompt = f"""
        Extract structured data from the following web content. 
        Return a JSON object with the following structure:
        
        {{
            "title": "Page title",
            "author": "Author name if available",
            "publish_date": "Publication date if available",
            "summary": "Brief summary of the content",
            "key_topics": ["list", "of", "key", "topics"],
            "entities": {{
                "people": [],
                "organizations": [],
                "locations": [],
                "drugs": [],
                "diseases": []
            }}
        }}
        
        Content:
        {content[:10000]}... [truncated]
        """
        
        response = await lmstudio_client.ask_llm([{"role": "user", "content": prompt}])
        
        try:
            # Try to parse the response as JSON
            import json
            structured_data = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, returning as text")
            structured_data = {"extracted_data": response}
        
        return {
            "extracted_data": structured_data,
            "metadata": {
                "content_length": len(content),
                "extraction_method": "llm_analysis"
            }
        }
    
    async def handle_analyze_web_content(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze web content for specific information"""
        content = parameters.get("content", "")
        analysis_type = parameters.get("analysis_type", "general")
        
        if not content:
            # If no content provided, try to fetch from URL
            url = parameters.get("url")
            if not url:
                raise ValueError("Either 'content' or 'url' must be provided")
            
            content = await self.fetch_url(url)
        
        # Customize the prompt based on the analysis type
        if analysis_type == "scientific_study":
            prompt = f"""
            Analyze the following scientific study for key information:
            
            {content[:15000]}... [truncated]
            
            Please extract:
            1. Study objectives
            2. Methodology
            3. Key findings
            4. Conclusions
            5. Limitations
            6. Relevance to pharmaceutical research
            """
        elif analysis_type == "news_article":
            prompt = f"""
            Analyze the following news article for key information:
            
            {content[:15000]}... [truncated]
            
            Please provide:
            1. Main topic
            2. Key facts and figures
            3. Sources and references
            4. Potential biases
            5. Implications for the pharmaceutical industry
            """
        else:  # general analysis
            prompt = f"""
            Analyze the following web content and provide a detailed summary:
            
            {content[:15000]}... [truncated]
            
            Include:
            1. Main topics covered
            2. Key points
            3. Any notable facts or statistics
            4. Author's perspective or bias
            5. Overall significance
            """
        
        analysis = await lmstudio_client.ask_llm([{"role": "user", "content": prompt}])
        
        return {
            "analysis": analysis,
            "metadata": {
                "analysis_type": analysis_type,
                "content_length": len(content),
                "source": parameters.get("url", "direct_content")
            }
        }

    async def handle_analyze_section(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generic web-domain analysis for MasterAgent."""
        query = parameters.get("query", "")
        context = parameters.get("context", {})
        prompt = f"Search and synthesize relevant web-based evidence for the query: {query}\nContext: {context}\nSummarize authoritative sources and key findings." 
        response = await lmstudio_client.ask_llm([{"role": "user", "content": prompt}])
        return {"analysis": response, "metadata": {"analysis_type": "web_evidence"}}
