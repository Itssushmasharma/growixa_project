import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class SEOAnalyzer:
    async def analyze(self, url: str) -> dict:
        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
        except Exception as e:
            return {
                "url": url,
                "score": 0,
                "error": f"Failed to fetch URL: {str(e)}",
                "warnings": ["Could not reach the website."],
                "recommendations": ["Check if the URL is correct and the site is online."],
            }

        soup = BeautifulSoup(html, "html.parser")
        
        score = 100
        warnings = []
        recommendations = []

        # 1. Title Tag
        title_tag = soup.title
        if not title_tag or not title_tag.string:
            score -= 15
            warnings.append("Missing <title> tag.")
            recommendations.append("Add a descriptive <title> tag to your HTML <head>.")
        else:
            title_length = len(title_tag.string.strip())
            if title_length < 10 or title_length > 60:
                score -= 5
                warnings.append(f"Title length is {title_length} characters. Optimal is 10-60.")
                recommendations.append("Keep your title between 10 and 60 characters.")

        # 2. Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if not meta_desc or not meta_desc.get("content"):
            score -= 15
            warnings.append("Missing meta description.")
            recommendations.append("Add a <meta name=\"description\" content=\"...\"> tag.")
        else:
            desc_length = len(meta_desc["content"].strip())
            if desc_length < 50 or desc_length > 160:
                score -= 5
                warnings.append(f"Meta description length is {desc_length} characters. Optimal is 50-160.")
                recommendations.append("Keep your meta description between 50 and 160 characters.")

        # 3. H1 Tag
        h1_tags = soup.find_all("h1")
        if len(h1_tags) == 0:
            score -= 10
            warnings.append("No <h1> tag found.")
            recommendations.append("Add exactly one <h1> tag representing the main topic.")
        elif len(h1_tags) > 1:
            score -= 5
            warnings.append("Multiple <h1> tags found.")
            recommendations.append("Use only one <h1> tag per page.")

        # 4. Images Alt Text
        images = soup.find_all("img")
        missing_alt = [img for img in images if not img.get("alt")]
        if images and missing_alt:
            score -= 10
            warnings.append(f"{len(missing_alt)} out of {len(images)} images are missing alt text.")
            recommendations.append("Add descriptive alt attributes to all <img> tags for accessibility and SEO.")

        # 5. HTTPS Check
        parsed_url = urlparse(str(response.url))
        if parsed_url.scheme != "https":
            score -= 20
            warnings.append("Website is not using HTTPS.")
            recommendations.append("Secure your website with an SSL certificate.")

        # Prevent negative score
        score = max(0, score)

        return {
            "url": str(response.url),
            "score": score,
            "title": title_tag.string.strip() if title_tag and title_tag.string else None,
            "description": meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None,
            "h1_count": len(h1_tags),
            "image_count": len(images),
            "images_missing_alt": len(missing_alt),
            "is_https": parsed_url.scheme == "https",
            "warnings": warnings,
            "recommendations": recommendations,
        }

seo_analyzer = SEOAnalyzer()
