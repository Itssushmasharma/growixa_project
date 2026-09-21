import re
from urllib.parse import urlparse
import httpx

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore


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

        score = 100
        warnings = []
        recommendations = []

        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.title
            title_str = title_tag.string.strip() if title_tag and title_tag.string else None
            meta_desc = soup.find("meta", attrs={"name": "description"})
            desc_str = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None
            h1_tags = soup.find_all("h1")
            h1_count = len(h1_tags)
            images = soup.find_all("img")
            missing_alt_count = len([img for img in images if not img.get("alt")])
            image_count = len(images)
        else:
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title_str = title_match.group(1).strip() if title_match else None
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
            desc_str = desc_match.group(1).strip() if desc_match else None
            h1_count = len(re.findall(r"<h1[^>]*>", html, re.IGNORECASE))
            images = re.findall(r"<img[^>]*>", html, re.IGNORECASE)
            image_count = len(images)
            missing_alt_count = len([img for img in images if "alt=" not in img.lower()])

        # 1. Title Tag
        if not title_str:
            score -= 15
            warnings.append("Missing <title> tag.")
            recommendations.append("Add a descriptive <title> tag to your HTML <head>.")
        else:
            title_length = len(title_str)
            if title_length < 10 or title_length > 60:
                score -= 5
                warnings.append(f"Title length is {title_length} characters. Optimal is 10-60.")
                recommendations.append("Keep your title between 10 and 60 characters.")

        # 2. Meta Description
        if not desc_str:
            score -= 15
            warnings.append("Missing meta description.")
            recommendations.append('Add a <meta name="description" content="..."> tag.')
        else:
            desc_length = len(desc_str)
            if desc_length < 50 or desc_length > 160:
                score -= 5
                warnings.append(f"Meta description length is {desc_length} characters. Optimal is 50-160.")
                recommendations.append("Keep your meta description between 50 and 160 characters.")

        # 3. H1 Tag
        if h1_count == 0:
            score -= 10
            warnings.append("No <h1> tag found.")
            recommendations.append("Add exactly one <h1> tag representing the main topic.")
        elif h1_count > 1:
            score -= 5
            warnings.append("Multiple <h1> tags found.")
            recommendations.append("Use only one <h1> tag per page.")

        # 4. Images Alt Text
        if image_count > 0 and missing_alt_count > 0:
            score -= 10
            warnings.append(f"{missing_alt_count} out of {image_count} images are missing alt text.")
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
            "title": title_str,
            "description": desc_str,
            "h1_count": h1_count,
            "image_count": image_count,
            "images_missing_alt": missing_alt_count,
            "is_https": parsed_url.scheme == "https",
            "warnings": warnings,
            "recommendations": recommendations,
        }


seo_analyzer = SEOAnalyzer()
