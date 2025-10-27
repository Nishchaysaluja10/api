from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from lxml import html
import re

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_wikipedia_page(country: str):
    """Fetch Wikipedia page HTML for a given country"""
    url = f"https://en.wikipedia.org/wiki/{country.replace(' ', '_')}"
    try:
        response = httpx.get(url, follow_redirects=True, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return None

def extract_headings(html_content: str):
    """Extract all headings (H1-H6) from Wikipedia page"""
    tree = html.fromstring(html_content)
    
    # Get all headings with their hierarchy
    headings = []
    
    # Wikipedia uses specific classes for content headings
    for i in range(1, 7):  # H1 to H6
        elements = tree.xpath(f'//h{i}')
        for element in elements:
            # Get the text content, removing edit links
            text = element.text_content().strip()
            # Remove [edit] and other Wikipedia-specific text
            text = re.sub(r'\[edit\]', '', text).strip()
            
            if text and len(text) > 0:
                headings.append({
                    'level': i,
                    'text': text
                })
    
    return headings

def generate_markdown_outline(headings: list):
    """Convert headings to Markdown outline"""
    markdown = "## Contents\n\n"
    
    for heading in headings:
        level = heading['level']
        text = heading['text']
        
        # Create appropriate markdown heading
        if level == 1:
            markdown += f"# {text}\n\n"
        elif level == 2:
            markdown += f"## {text}\n\n"
        elif level == 3:
            markdown += f"### {text}\n\n"
        elif level == 4:
            markdown += f"#### {text}\n\n"
        elif level == 5:
            markdown += f"##### {text}\n\n"
        elif level == 6:
            markdown += f"###### {text}\n\n"
    
    return markdown

@app.get("/api/outline")
async def get_country_outline(country: str = Query(..., description="Country name")):
    """
    API endpoint to get Wikipedia outline for a country
    
    Example: /api/outline?country=Japan
    """
    # Fetch Wikipedia page
    html_content = fetch_wikipedia_page(country)
    
    if not html_content:
        return {
            "error": f"Could not fetch Wikipedia page for '{country}'",
            "status": "failed"
        }
    
    # Extract headings
    headings = extract_headings(html_content)
    
    if not headings:
        return {
            "error": f"No headings found for '{country}'",
            "status": "failed"
        }
    
    # Generate Markdown outline
    markdown_outline = generate_markdown_outline(headings)
    
    return {
        "country": country,
        "outline": markdown_outline,
        "heading_count": len(headings),
        "status": "success"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Country Information API for GlobalEdu",
        "usage": "GET /api/outline?country=<country_name>",
        "example": "/api/outline?country=Vanuatu"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
