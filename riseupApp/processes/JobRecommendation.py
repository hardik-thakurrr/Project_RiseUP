import time
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
import ssl
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import urllib.parse

# SSL certificate verification bypass
ssl._create_default_https_context = ssl._create_unverified_context

class NaukriJobScraper:
    def __init__(self):
        self.chrome_options = Options()
        # Uncomment the line below if you want to run in headless mode
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
    
    def initialize_driver(self):
        """Initialize and return a Chrome driver with the appropriate options."""
        return uc.Chrome(options=self.chrome_options)
    
    def extract_job_details(self, job_card, job_id=None):
        """Extract job details from a Naukri job card"""
        job_info = {}
        
        # Get job ID
        if job_id is None:
            try:
                job_info['job_id'] = job_card.get_attribute('data-job-id')
            except:
                job_info['job_id'] = "Not found"
        else:
            job_info['job_id'] = job_id
        
        # Get job title
        try:
            title_element = job_card.find_element(By.CSS_SELECTOR, "a.title")
            job_info['job_title'] = title_element.text.strip()
            job_info['url'] = title_element.get_attribute('href')
        except:
            try:
                title_element = job_card.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a")
                job_info['job_title'] = title_element.text.strip()
                job_info['url'] = title_element.get_attribute('href')
            except:
                job_info['job_title'] = "Title not found"
                job_info['url'] = "URL not found"
        
        # Get company name
        try:
            company_element = job_card.find_element(By.CSS_SELECTOR, "a.comp-name")
            job_info['company_name'] = company_element.text.strip()
        except:
            try:
                company_element = job_card.find_element(By.CSS_SELECTOR, ".companyInfo a")
                job_info['company_name'] = company_element.text.strip()
            except:
                job_info['company_name'] = "Company not found"
        
        # Get company rating
        try:
            rating_element = job_card.find_element(By.CSS_SELECTOR, "a.rating span.main-2")
            job_info['company_rating'] = rating_element.text.strip()
        except:
            job_info['company_rating'] = None
        
        # Get experience
        try:
            exp_element = job_card.find_element(By.CSS_SELECTOR, "span.expwdth")
            job_info['experience'] = exp_element.text.strip()
        except:
            try:
                exp_element = job_card.find_element(By.CSS_SELECTOR, "span.exp")
                job_info['experience'] = exp_element.text.strip()
            except:
                job_info['experience'] = "Not specified"
        
        # Get salary
        try:
            salary_element = job_card.find_element(By.CSS_SELECTOR, "span.sal span")
            job_info['salary'] = salary_element.text.strip()
        except:
            job_info['salary'] = "Not disclosed"
        
        # Get location
        try:
            location_element = job_card.find_element(By.CSS_SELECTOR, "span.locWdth")
            job_info['location'] = location_element.text.strip()
        except:
            try:
                location_element = job_card.find_element(By.CSS_SELECTOR, "span.loc span")
                job_info['location'] = location_element.text.strip()
            except:
                job_info['location'] = "Not specified"
        
        # Get job description
        try:
            job_desc_element = job_card.find_element(By.CSS_SELECTOR, "span.job-desc")
            job_info['job_description'] = job_desc_element.text.strip()
        except:
            job_info['job_description'] = "Job description not available in job card"
        
        # Get skills
        try:
            skills_elements = job_card.find_elements(By.CSS_SELECTOR, "ul.tags-gt li.tag-li")
            job_info['skills'] = [skill.text.strip() for skill in skills_elements]
            job_info['skill_name'] = ", ".join(job_info['skills'])
        except:
            job_info['skills'] = []
            job_info['skill_name'] = "Skills not found"
        
        # Get posted date
        try:
            date_element = job_card.find_element(By.CSS_SELECTOR, "span.job-post-day")
            job_info['posted_date'] = date_element.text.strip()
        except:
            job_info['posted_date'] = "Not specified"
        
        # Set work type - Remote check
        job_info['work_type'] = "On-site"
        if (job_info.get('location', '').lower().find('remote') != -1 or 
            job_info.get('job_title', '').lower().find('remote') != -1 or
            job_info.get('job_description', '').lower().find('remote work') != -1):
            job_info['work_type'] = "Remote"
        
        return job_info
    
    def extract_details_from_job_page(self, driver, wait, job_info):
        """Extract additional details from the job details page based on its HTML structure"""
        try:
            # Wait for the job description to load
            try:
                detailed_job_desc = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".styles_JDC__dang-inner-html__h0K4t")))
                job_info['detailed_job_description'] = detailed_job_desc.text.strip()
            except TimeoutException:
                # Try alternate selector
                try:
                    detailed_job_desc = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dang-inner-html")))
                    job_info['detailed_job_description'] = detailed_job_desc.text.strip()
                except:
                    job_info['detailed_job_description'] = "Failed to load detailed description"
            
            # Extract skills from the key-skills section
            try:
                # First try to find the modern key skills section
                skills_section = driver.find_element(By.CSS_SELECTOR, ".styles_key-skill__GIPn_")
                skill_tags = skills_section.find_elements(By.CSS_SELECTOR, "a.styles_chip__7YCfG")
                additional_skills = [skill.text.strip() for skill in skill_tags]
                
                # Check for preferred skills (marked with save icon)
                preferred_skills = []
                for skill_tag in skill_tags:
                    try:
                        # If it has the save icon, it's a preferred skill
                        if skill_tag.find_element(By.CSS_SELECTOR, "i.ni-icon-jd-save"):
                            skill_text = skill_tag.text.strip()
                            preferred_skills.append(skill_text)
                    except:
                        pass
                
                if preferred_skills:
                    job_info['preferred_skills'] = preferred_skills
            except:
                # Try alternate selector
                try:
                    skills_section = driver.find_element(By.CSS_SELECTOR, ".key-skill")
                    skill_tags = skills_section.find_elements(By.TAG_NAME, "a")
                    additional_skills = [skill.text.strip() for skill in skill_tags]
                except:
                    additional_skills = []
            
            # Merge with existing skills
            if additional_skills:
                if 'skills' in job_info and job_info['skills']:
                    job_info['skills'].extend(additional_skills)
                    job_info['skills'] = list(set(job_info['skills']))  # Remove duplicates
                else:
                    job_info['skills'] = additional_skills
                
                job_info['skill_name'] = ", ".join(job_info['skills'])
            
            # Extract education requirements
            try:
                education_section = driver.find_element(By.CSS_SELECTOR, ".styles_education__KXFkO")
                education_details = education_section.find_elements(By.CSS_SELECTOR, ".styles_details__Y424J")
                
                education_info = {}
                for detail in education_details:
                    try:
                        label = detail.find_element(By.TAG_NAME, "label").text.strip().replace(":", "")
                        value = detail.find_element(By.TAG_NAME, "span").text.strip()
                        education_info[label] = value
                    except:
                        pass
                
                if education_info:
                    job_info['education_requirements'] = education_info
            except:
                pass
            
            # Extract other details (role, industry, department, etc.)
            try:
                other_details_section = driver.find_element(By.CSS_SELECTOR, ".styles_other-details__oEN4O")
                details = other_details_section.find_elements(By.CSS_SELECTOR, ".styles_details__Y424J")
                
                other_info = {}
                for detail in details:
                    try:
                        label = detail.find_element(By.TAG_NAME, "label").text.strip().replace(":", "")
                        value_span = detail.find_element(By.TAG_NAME, "span")
                        
                        # Check if there are links inside
                        links = value_span.find_elements(By.TAG_NAME, "a")
                        if links:
                            value = ", ".join([link.text.strip() for link in links])
                        else:
                            value = value_span.text.strip()
                        
                        other_info[label] = value
                    except:
                        pass
                
                if other_info:
                    job_info['other_details'] = other_info
            except:
                pass
            
            # Extract applicant count if available
            try:
                applicants_element = driver.find_element(By.CSS_SELECTOR, ".styles_jhc__stat__PgY67 span:last-child")
                job_info['applicants'] = applicants_element.text.strip()
            except:
                pass
            
            # If we still don't have a good job description, use the detailed one
            if job_info.get('job_description') == "Job description not available in job card":
                job_info['job_description'] = job_info.get('detailed_job_description', "No description available")
            
            return job_info
            
        except Exception as e:
            print(f"Error extracting details from job page: {str(e)}")
            return job_info
    
    def scrape_naukri_jobs(self, search_term, location, num_jobs=10):
        """Scrape job listings from Naukri.com"""
        driver = self.initialize_driver()
        wait = WebDriverWait(driver, 15)
        all_job_data = []
        
        try:
            # Format the job title and location for URL
            search_term_formatted = urllib.parse.quote(search_term)
            location_formatted = urllib.parse.quote(location)
            
            # Construct the URL for Naukri's search results
            url = f"https://www.naukri.com/{search_term_formatted}-jobs-in-{location_formatted}"
            print(f"Navigating to URL: {url}")
            
            driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Wait for job listings to load
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")))
                print("Job listings loaded successfully")
            except TimeoutException:
                print("Timeout waiting for job listings, trying alternate selector...")
                # Try an alternate selector
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobTupleHeader")))
                print("Job listings found with alternate selector")
            
            # Get job listings
            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")
            
            if not job_cards:
                # Try alternate selector
                job_cards = driver.find_elements(By.CSS_SELECTOR, "article.jobTuple")
                
            print(f"Found {len(job_cards)} job listings")
            
            # Limit to requested number of jobs
            jobs_to_process = min(num_jobs, len(job_cards))
            
            for i in range(jobs_to_process):
                print(f"Processing job {i+1}/{jobs_to_process}")
                
                try:
                    # Get fresh list of job cards (in case the DOM has been refreshed)
                    current_job_cards = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")
                    if not current_job_cards:
                        current_job_cards = driver.find_elements(By.CSS_SELECTOR, "article.jobTuple")
                    
                    if i >= len(current_job_cards):
                        print(f"Only {len(current_job_cards)} job cards found, stopping")
                        break
                    
                    # Extract basic job details from the card
                    job_card = current_job_cards[i]
                    job_info = self.extract_job_details(job_card)
                    
                    # Scroll to the job card
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_card)
                    time.sleep(0.5)
                    
                    # Get direct job URL if available
                    job_url = job_info.get('url')
                    
                    if job_url and job_url.startswith('http'):
                        # Navigate directly to the job page
                        print(f"Navigating to job details page: {job_url}")
                        driver.get(job_url)
                        time.sleep(2)  # Wait for page to load
                        
                        # Extract details from the job page
                        job_info = self.extract_details_from_job_page(driver, wait, job_info)
                        
                        # Go back to search results
                        driver.back()
                        time.sleep(3)  # Wait for search results to reload
                    else:
                        # Try to click on the job title to open detailed view
                        try:
                            title_link = job_card.find_element(By.CSS_SELECTOR, "a.title")
                            driver.execute_script("arguments[0].click();", title_link)
                            time.sleep(2)  # Wait for detail page to load
                            
                            # Extract additional details from the detailed view
                            job_info = self.extract_details_from_job_page(driver, wait, job_info)
                        except Exception as e:
                            print(f"Could not click on job title for job {i+1}: {str(e)}")
                    
                    all_job_data.append(job_info)
                    
                except Exception as e:
                    print(f"Error processing job {i+1}: {str(e)}")
                    continue
            
            # Create and save DataFrame
            df = pd.DataFrame(all_job_data)
            
            # Create output folder if it doesn't exist
            os.makedirs("output", exist_ok=True)
            
            # Save to CSV
            output_file = f"output/naukri_{search_term.replace(' ', '_')}_{location}_jobs.csv"
            df.to_csv(output_file, index=False)
            
            # Also save to JSON for easier inspection
            json_output_file = f"output/naukri_{search_term.replace(' ', '_')}_{location}_jobs.json"
            df.to_json(json_output_file, orient="records", indent=4)
            
            print(f"Scraped {len(df)} job listings and saved to CSV and JSON in the output folder")
            
            return df
            
        finally:
            driver.quit()


class JobRecommender:
    def __init__(self, data):
        self.data = data
        self.vectorizer = None
        self.description_vectorizer = None
        self.description_embeddings = None
        
    def preprocess_text(self, text):
        if isinstance(text, str):
            text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
            return text
        return ''
    
    def fit(self):
        """Generate embeddings from the scraped data"""
        print("Generating embeddings from scraped data...")
        
        # Process job descriptions
        descriptions = [self.preprocess_text(desc) for desc in self.data['detailed_job_description'].fillna('')]
    
        
        self.description_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.description_embeddings = self.description_vectorizer.fit_transform(descriptions)
        
        # Process skills separately
        skills = [self.preprocess_text(skill) for skill in self.data['skill_name'].fillna('')]
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        self.skills_embeddings = self.vectorizer.fit_transform(skills)
        
        print("Embeddings generated successfully.")
        
    def calculate_skill_match_score(self, user_skills, idx):
        """Calculate skill match using TF-IDF embeddings"""
        if pd.isna(self.data.iloc[idx]['skill_name']):
            return 0
            
        try:
            user_skills_text = ' '.join(user_skills)
            user_skills_vector = self.vectorizer.transform([self.preprocess_text(user_skills_text)])
            similarity = cosine_similarity(user_skills_vector, 
                                           self.skills_embeddings[idx:idx+1])[0][0]
            return similarity
        except Exception as e:
            print(f"Error calculating skill match: {str(e)}")
            return 0

    def calculate_description_match_score(self, user_description, idx):
        """Calculate description match using TF-IDF embeddings"""
        if pd.isna(self.data.iloc[idx]['detailed_job_description']):
            return 0
            
        try:
            user_vector = self.description_vectorizer.transform([self.preprocess_text(user_description)])
            similarity = cosine_similarity(user_vector, 
                                          self.description_embeddings[idx:idx+1])[0][0]
            return similarity
        except Exception as e:
            print(f"Error calculating description match: {str(e)}")
            return 0

    def recommend_jobs(self, user_skills, user_description, top_n=10):
        """Recommend jobs based on user profile"""
        if self.vectorizer is None:
            self.fit()
        
        scores = []
        for idx, row in self.data.iterrows():
            try:
                skill_score = self.calculate_skill_match_score(user_skills, idx)
                
                description_score = self.calculate_description_match_score(user_description, idx)

                # Simplified scoring without experience and location
                total_score = (
                    skill_score * 0.6 +
                    description_score * 0.4
                )
                
                scores.append({
                    'jobTitle': row['job_title'],
                    'companyName': row['company_name'],
                    'location': row.get('location', 'Not specified'),
                    'url': row.get('url', ''),
                    'salary': row.get('salary', 'Not specified'),
                    'experience': row.get('experience', 'Not specified'),
                    'posted_date': row.get('posted_date', 'Not specified'),
                    'skillScore': round(skill_score, 2),
                    'descriptionScore': round(description_score, 2),
                    'totalScore': round(total_score, 3)
                })
            except Exception as e:
                print(f"Error processing job at index {idx}: {str(e)}")
                continue
            
        recommendations = pd.DataFrame(scores)
        if len(recommendations) == 0:
            print("Warning: No valid recommendations could be generated")
            return pd.DataFrame()
            
        return recommendations.sort_values('totalScore', ascending=False).head(top_n)