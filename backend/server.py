from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import time
import re
import validators
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
import aiohttp
import asyncio
from typing import List, Dict
import json
from newspaper import Article
import os
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI(title="Fake News Sniff API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/fakenews_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client.fakenews_db

# User Agent for scraping
ua = UserAgent()

class NewsAnalysisRequest(BaseModel):
    url_or_text: str

class NewsAnalysisResponse(BaseModel):
    suspicion_score: int
    factors: List[str]
    sources_checked: List[str]
    content_summary: str
    analysis_details: Dict

class NewsContentExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def extract_from_url(self, url: str) -> Dict:
        """Extract content from news URL using multiple methods"""
        try:
            # Method 1: Using newspaper3k
            article = Article(url, language='pt')
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 100:
                return {
                    'title': article.title or 'Sem título',
                    'content': article.text[:2000],  # Limit content
                    'authors': article.authors,
                    'publish_date': str(article.publish_date) if article.publish_date else None,
                    'source_url': url,
                    'method': 'newspaper3k'
                }
        except Exception as e:
            print(f"Newspaper3k failed: {e}")

        # Method 2: BeautifulSoup fallback
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ''
            title_selectors = ['h1', 'title', '.title', '.headline', '[class*="title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    title = title_elem.get_text().strip()
                    break
            
            # Extract content
            content = ''
            content_selectors = [
                'article', '.content', '.post-content', '.entry-content',
                '[class*="content"]', '[class*="article"]', 'main', '.main'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    content = content_elem.get_text().strip()
                    if len(content) > 100:
                        break
            
            if not content:
                # Fallback: get all p tags
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs[:10]])
            
            return {
                'title': title or 'Título não encontrado',
                'content': content[:2000] if content else 'Conteúdo não encontrado',
                'authors': [],
                'publish_date': None,
                'source_url': url,
                'method': 'beautifulsoup'
            }
            
        except Exception as e:
            print(f"BeautifulSoup extraction failed: {e}")
            return {
                'title': 'Erro na extração',
                'content': 'Não foi possível extrair o conteúdo',
                'authors': [],
                'publish_date': None,
                'source_url': url,
                'method': 'failed'
            }

class GoogleSearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search Google and return results"""
        try:
            # Format query for Google search
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={num_results}&hl=pt-BR"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find search result containers
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:num_results]:
                try:
                    # Extract title
                    title_elem = result.find('h3')
                    title = title_elem.get_text() if title_elem else ''
                    
                    # Extract URL
                    link_elem = result.find('a')
                    url = link_elem.get('href') if link_elem else ''
                    
                    # Extract snippet
                    snippet_elem = result.find('span', class_=['st', 'IsZvec'])
                    if not snippet_elem:
                        snippet_elem = result.find('div', class_=['s', 'IsZvec'])
                    snippet = snippet_elem.get_text() if snippet_elem else ''
                    
                    if title and url and url.startswith('http'):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            print(f"Google search failed: {e}")
            return []

class NewsCredibilityAnalyzer:
    def __init__(self):
        self.content_extractor = NewsContentExtractor()
        self.google_scraper = GoogleSearchScraper()
        
        # Reliable news sources (Brazilian focus)
        self.reliable_sources = [
            'g1.globo.com', 'folha.uol.com.br', 'estadao.com.br', 'bbc.com',
            'reuters.com', 'cnn.com.br', 'uol.com.br', 'veja.abril.com.br',
            'oglobo.globo.com', 'terra.com.br', 'r7.com', 'agenciabrasil.ebc.com.br'
        ]
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'URGENTE', r'BOMBA', r'ESCÂNDALO', r'CHOCANTE', r'INACREDITÁVEL',
            r'EXCLUSIVO', r'REVELAÇÃO', r'SEGREDO', r'CONSPIRAÇÃO'
        ]

    async def analyze_news_credibility(self, url_or_text: str) -> Dict:
        """Main analysis function"""
        suspicion_score = 0
        factors = []
        sources_checked = []
        analysis_details = {}
        
        # Determine if input is URL or text
        is_url = validators.url(url_or_text)
        
        if is_url:
            # Extract content from URL
            original_content = self.content_extractor.extract_from_url(url_or_text)
            content_summary = f"{original_content['title']}: {original_content['content'][:200]}..."
            
            # Check domain credibility
            domain = urlparse(url_or_text).netloc.lower()
            if any(reliable in domain for reliable in self.reliable_sources):
                factors.append("✅ Fonte conhecida e confiável")
                suspicion_score -= 20
            else:
                factors.append("⚠️ Fonte desconhecida ou não verificada")
                suspicion_score += 15
            
            analysis_details['original_domain'] = domain
            search_query = original_content['title']
            
        else:
            # Direct text analysis
            original_content = {'title': 'Texto direto', 'content': url_or_text}
            content_summary = url_or_text[:200] + "..."
            search_query = url_or_text[:100]
        
        # Check for suspicious patterns
        full_text = f"{original_content['title']} {original_content['content']}"
        suspicious_found = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                suspicious_found.append(pattern)
        
        if suspicious_found:
            factors.append(f"⚠️ Linguagem sensacionalista detectada: {', '.join(suspicious_found)}")
            suspicion_score += len(suspicious_found) * 10
        
        # Search Google for related information
        try:
            search_results = self.google_scraper.search_google(search_query, 8)
            sources_checked = [result['url'] for result in search_results]
            
            if not search_results:
                factors.append("❌ Nenhuma fonte adicional encontrada")
                suspicion_score += 25
            else:
                # Analyze search results
                reliable_confirmations = 0
                total_results = len(search_results)
                
                for result in search_results:
                    domain = urlparse(result['url']).netloc.lower()
                    if any(reliable in domain for reliable in self.reliable_sources):
                        reliable_confirmations += 1
                
                if reliable_confirmations >= 2:
                    factors.append(f"✅ {reliable_confirmations} fontes confiáveis confirmam informações similares")
                    suspicion_score -= 15
                elif reliable_confirmations == 1:
                    factors.append("⚠️ Apenas 1 fonte confiável encontrada")
                    suspicion_score += 10
                else:
                    factors.append("❌ Nenhuma fonte confiável confirma as informações")
                    suspicion_score += 30
                
                analysis_details['reliable_confirmations'] = reliable_confirmations
                analysis_details['total_results'] = total_results
                
        except Exception as e:
            factors.append("❌ Erro na verificação de fontes externas")
            suspicion_score += 20
        
        # Content analysis
        content_length = len(original_content['content'])
        if content_length < 200:
            factors.append("⚠️ Conteúdo muito curto para verificação completa")
            suspicion_score += 10
        
        # Check for author information
        if original_content.get('authors'):
            factors.append("✅ Autoria identificada")
            suspicion_score -= 5
        else:
            factors.append("⚠️ Autoria não identificada")
            suspicion_score += 10
        
        # Check for publication date
        if original_content.get('publish_date'):
            factors.append("✅ Data de publicação identificada")
            suspicion_score -= 5
        else:
            factors.append("⚠️ Data de publicação não identificada")
            suspicion_score += 5
        
        # Normalize score to 0-100 range
        suspicion_score = max(0, min(100, suspicion_score + 30))  # Base adjustment
        
        analysis_details.update({
            'content_length': content_length,
            'suspicious_patterns_found': len(suspicious_found),
            'extraction_method': original_content.get('method', 'unknown')
        })
        
        return {
            'suspicion_score': suspicion_score,
            'factors': factors,
            'sources_checked': sources_checked[:5],  # Limit displayed sources
            'content_summary': content_summary,
            'analysis_details': analysis_details
        }

# Initialize analyzer
analyzer = NewsCredibilityAnalyzer()

@app.get("/")
async def root():
    return {"message": "Fake News Sniff API - Combatendo a Desinformação"}

@app.post("/api/analyze", response_model=NewsAnalysisResponse)
async def analyze_news(request: NewsAnalysisRequest):
    """Analyze news for credibility"""
    try:
        if not request.url_or_text.strip():
            raise HTTPException(status_code=400, detail="URL ou texto não pode estar vazio")
        
        # Perform analysis
        result = await analyzer.analyze_news_credibility(request.url_or_text)
        
        # Store analysis in database
        try:
            analysis_record = {
                'input': request.url_or_text,
                'result': result,
                'timestamp': time.time()
            }
            await db.analyses.insert_one(analysis_record)
        except Exception as e:
            print(f"Database storage failed: {e}")
        
        return NewsAnalysisResponse(**result)
        
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Fake News Sniff"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)