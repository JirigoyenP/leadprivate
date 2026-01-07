"""
LinkedIn scraping service.

This service wraps the LinkedIn bot functionality and integrates it with
the LeadCleanse application for lead generation and enrichment.
"""

import os
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional
from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.linkedin import LinkedInKeyword, LinkedInPost, LinkedInScrapeJob


class LinkedInError(Exception):
    """Custom exception for LinkedIn scraping errors."""
    pass


class LinkedInService:
    """
    LinkedIn scraping service for lead generation.

    Scrapes LinkedIn posts based on keywords and extracts author information
    for lead enrichment via Apollo.io.
    """

    DEFAULT_KEYWORDS = [
        "integracion", "agencia", "dinamicas", "eventos", "presencial",
        "proveedor", "catering", "shows", "BTL", "lanzamiento",
        "activacion", "productoras"
    ]

    def __init__(self, db: Session, headless: bool = True):
        self.settings = get_settings()
        self.db = db
        self.headless = headless
        self.driver: Optional[webdriver.Firefox] = None
        self.date_today = datetime.now()
        self.max_age = self.date_today - relativedelta(months=3)

    def _init_driver(self):
        """Initialize the Firefox webdriver."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Use geckodriver from settings or default path
        geckodriver_path = self.settings.linkedin_geckodriver_path
        if geckodriver_path and os.path.exists(geckodriver_path):
            service = Service(executable_path=geckodriver_path)
            self.driver = webdriver.Firefox(service=service, options=options)
        else:
            self.driver = webdriver.Firefox(options=options)

        self.driver.set_page_load_timeout(30)

    def _close_driver(self):
        """Close the webdriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def login(self) -> bool:
        """
        Log into LinkedIn with configured credentials.

        Returns:
            True if login successful, False otherwise
        """
        if not self.driver:
            self._init_driver()

        username = self.settings.linkedin_username
        password = self.settings.linkedin_password

        if not username or not password:
            raise LinkedInError("LinkedIn credentials not configured")

        try:
            self.driver.get("https://www.linkedin.com")

            # Wait for and fill username
            username_box = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "session_key"))
            )
            username_box.send_keys(username)

            # Fill password and submit
            password_box = self.driver.find_element(By.ID, "session_password")
            password_box.send_keys(password)
            password_box.send_keys(Keys.ENTER)

            # Wait for feed to load (indicates successful login)
            time.sleep(5)

            # Check if we're on the feed
            if "feed" in self.driver.current_url or "checkpoint" not in self.driver.current_url:
                return True

            # May need security verification
            if "checkpoint" in self.driver.current_url:
                raise LinkedInError("LinkedIn requires security verification. Please login manually first.")

            return False

        except Exception as e:
            raise LinkedInError(f"Login failed: {str(e)}")

    def get_keywords(self) -> list[str]:
        """Get active keywords from database or defaults."""
        keywords = self.db.query(LinkedInKeyword).filter(
            LinkedInKeyword.is_active == True
        ).all()

        if keywords:
            return [k.keyword for k in keywords]
        return self.DEFAULT_KEYWORDS

    def _parse_date_text(self, date_text: str) -> Optional[datetime]:
        """Parse LinkedIn relative date text to datetime."""
        try:
            parts = date_text.strip().split(" ")
            if len(parts) < 2:
                return None

            amount = int(parts[0])
            unit = parts[1].lower()

            if "segundo" in unit or "second" in unit:
                return self.date_today - relativedelta(seconds=amount)
            elif "minuto" in unit or "minute" in unit:
                return self.date_today - relativedelta(minutes=amount)
            elif "hora" in unit or "hour" in unit:
                return self.date_today - relativedelta(hours=amount)
            elif "día" in unit or "dia" in unit or "day" in unit:
                return self.date_today - relativedelta(days=amount)
            elif "semana" in unit or "week" in unit:
                return self.date_today - relativedelta(weeks=amount)
            elif "mes" in unit or "month" in unit:
                return self.date_today - relativedelta(months=amount)
            elif "año" in unit or "year" in unit:
                return self.date_today - relativedelta(years=amount)

            return None
        except Exception:
            return None

    def _get_author_country(self, profile_url: str) -> Optional[str]:
        """Get the country from an author's profile."""
        try:
            self.driver.get(profile_url)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "profile-content"))
            )

            js_code = """
                var profileInfo = document.getElementById('profile-content');
                var insideProfile = profileInfo.getElementsByClassName('scaffold-layout__main')[0];
                var box = insideProfile.getElementsByClassName('ph5')[0];
                var countryText = box.getElementsByClassName('text-body-small inline t-black--light break-words')[0];
                return countryText ? countryText.textContent.trim() : null;
            """
            return self.driver.execute_script(js_code)
        except Exception:
            return None

    def _scroll_and_collect_posts(self, max_scrolls: int = 10) -> list:
        """Scroll the feed and collect post elements."""
        scroll_pause = 2
        posts_html = []

        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "scaffold-finite-scroll__content"))
            )
        except Exception:
            return []

        for _ in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)

        # Get all posts
        try:
            feed_element = self.driver.find_element(By.CLASS_NAME, "scaffold-finite-scroll__content")
            raw_html = feed_element.get_attribute("innerHTML")
            soup = bs(raw_html.encode("utf-8"), "html.parser")
            posts_html = soup.find_all("div", class_="artdeco-card")
        except Exception:
            pass

        return posts_html

    def _parse_post(self, post_html, keywords: list[str], register_time: datetime) -> Optional[dict]:
        """Parse a single post HTML into structured data."""
        try:
            # Check if it's a promoted post
            try:
                mini_info = post_html.find("div", class_="update-components-actor__meta relative")
                desc = mini_info.find("span", class_="update-components-actor__description")
                if desc and "Promocionado" in desc.get_text():
                    return None
                sub_desc = mini_info.find("div", class_="update-components-actor__sub-description")
                if sub_desc and "Promocionado" in sub_desc.get_text():
                    return None
            except Exception:
                pass

            # Get post text
            try:
                text_box = post_html.find("span", attrs={"class": "break-words"})
                post_text = text_box.find("span", attrs={"dir": "ltr"}).get_text() if text_box else None
            except Exception:
                post_text = None

            if not post_text:
                return None

            # Check if any keywords match
            matched_keywords = []
            text_lower = post_text.lower()
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched_keywords.append(kw)

            if not matched_keywords:
                return None

            # Get date
            post_date = None
            try:
                date_box = post_html.find("div", class_="update-components-actor__meta relative")
                date_span = date_box.find("span", class_="update-components-actor__sub-description")
                if date_span:
                    date_text = date_span.find("span", {"aria-hidden": "true"})
                    if date_text:
                        post_date = self._parse_date_text(date_text.get_text())
            except Exception:
                pass

            # Get author info
            author_name = None
            profile_url = None
            try:
                tag_a = post_html.find("a", {
                    "class": "app-aware-link update-components-actor__container-link"
                })
                if tag_a:
                    profile_url = tag_a.get("href")

                name_span = post_html.find("span", attrs={"dir": "ltr"})
                if name_span:
                    author_name = name_span.get_text().strip()
                    # Clean up the name
                    if "'" in author_name:
                        author_name = author_name.replace("'", "")
            except Exception:
                pass

            # Get comments count
            comments_count = 0
            try:
                info_comments = post_html.find("ul", {"class": "social-details-social-counts"})
                if info_comments:
                    comments_li = info_comments.find("li", class_="social-details-social-counts__comments")
                    if comments_li:
                        comments_text = comments_li.get_text()
                        comments_count = int(comments_text[:comments_text.find("c")])
            except Exception:
                pass

            return {
                "author_name": author_name,
                "author_profile_url": profile_url,
                "post_text": post_text[:5000] if post_text else None,  # Limit text length
                "post_date": post_date,
                "comments_count": comments_count,
                "keywords_matched": matched_keywords,
                "scraped_at": register_time,
            }

        except Exception:
            return None

    def scrape_feed(self, job_id: int, max_scrolls: int = 10) -> dict:
        """
        Scrape the LinkedIn feed for posts matching keywords.

        Args:
            job_id: The scrape job ID to track progress
            max_scrolls: Maximum number of scroll iterations

        Returns:
            Dict with scraping results
        """
        job = self.db.query(LinkedInScrapeJob).filter(LinkedInScrapeJob.id == job_id).first()
        if not job:
            raise LinkedInError("Scrape job not found")

        job.status = "running"
        job.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Initialize driver and login
            self._init_driver()
            self.login()

            # Get keywords
            keywords = self.get_keywords()
            job.keywords_used = keywords
            self.db.commit()

            # Navigate to feed
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)

            # Scroll and collect posts
            register_time = datetime.utcnow()
            posts_html = self._scroll_and_collect_posts(max_scrolls)
            job.posts_found = len(posts_html)
            self.db.commit()

            # Parse and save posts
            saved_count = 0
            for post_html in posts_html:
                parsed = self._parse_post(post_html, keywords, register_time)
                if parsed:
                    # Check if we already have this post (by author + approximate time)
                    existing = self.db.query(LinkedInPost).filter(
                        LinkedInPost.author_profile_url == parsed["author_profile_url"],
                        LinkedInPost.scraped_at >= register_time - timedelta(hours=1)
                    ).first()

                    if not existing:
                        post = LinkedInPost(
                            author_name=parsed["author_name"],
                            author_profile_url=parsed["author_profile_url"],
                            post_text=parsed["post_text"],
                            post_date=parsed["post_date"],
                            comments_count=parsed["comments_count"],
                            keywords_matched=parsed["keywords_matched"],
                            scrape_batch_id=job_id,
                            scraped_at=register_time,
                        )
                        self.db.add(post)
                        saved_count += 1

            self.db.commit()

            job.posts_saved = saved_count
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                "job_id": job_id,
                "status": "completed",
                "posts_found": job.posts_found,
                "posts_saved": saved_count,
                "keywords_used": keywords,
            }

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise LinkedInError(f"Scraping failed: {str(e)}")

        finally:
            self._close_driver()

    def search_posts(self, job_id: int, keywords: list[str] = None, max_scrolls: int = 5) -> dict:
        """
        Search LinkedIn for posts matching specific keywords.

        Args:
            job_id: The scrape job ID
            keywords: Keywords to search (uses defaults if not provided)
            max_scrolls: Scrolls per keyword search

        Returns:
            Dict with search results
        """
        job = self.db.query(LinkedInScrapeJob).filter(LinkedInScrapeJob.id == job_id).first()
        if not job:
            raise LinkedInError("Scrape job not found")

        job.status = "running"
        job.started_at = datetime.utcnow()
        self.db.commit()

        try:
            self._init_driver()
            self.login()

            keywords = keywords or self.get_keywords()
            job.keywords_used = keywords
            self.db.commit()

            register_time = datetime.utcnow()
            total_found = 0
            total_saved = 0

            for keyword in keywords:
                try:
                    # Navigate to search
                    search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}"
                    self.driver.get(search_url)
                    time.sleep(3)

                    # Scroll and collect
                    posts_html = self._scroll_and_collect_posts(max_scrolls)
                    total_found += len(posts_html)

                    # Parse and save
                    for post_html in posts_html:
                        parsed = self._parse_post(post_html, [keyword], register_time)
                        if parsed:
                            existing = self.db.query(LinkedInPost).filter(
                                LinkedInPost.author_profile_url == parsed["author_profile_url"],
                                LinkedInPost.scraped_at >= register_time - timedelta(hours=1)
                            ).first()

                            if not existing:
                                post = LinkedInPost(
                                    author_name=parsed["author_name"],
                                    author_profile_url=parsed["author_profile_url"],
                                    post_text=parsed["post_text"],
                                    post_date=parsed["post_date"],
                                    comments_count=parsed["comments_count"],
                                    keywords_matched=parsed["keywords_matched"],
                                    scrape_batch_id=job_id,
                                    scraped_at=register_time,
                                )
                                self.db.add(post)
                                total_saved += 1

                    self.db.commit()

                except Exception as e:
                    # Continue with next keyword
                    continue

            job.posts_found = total_found
            job.posts_saved = total_saved
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                "job_id": job_id,
                "status": "completed",
                "posts_found": total_found,
                "posts_saved": total_saved,
                "keywords_used": keywords,
            }

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise LinkedInError(f"Search failed: {str(e)}")

        finally:
            self._close_driver()


def get_linkedin_service(db: Session, headless: bool = True) -> LinkedInService:
    return LinkedInService(db, headless)
