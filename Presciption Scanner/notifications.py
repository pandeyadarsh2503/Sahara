# Optimized Medical Prescription Scanner
# app.py

import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
import time
from fuzzywuzzy import process, fuzz
import threading
import concurrent.futures
from functools import lru_cache
import schedule
from flask_socketio import SocketIO, join_room, leave_room
import hashlib
import pickle
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('prescription_scanner')

# Set Tesseract path for Windows - update this path to match your installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize Flask app with SocketIO for real-time notifications
app = Flask(__name__)
app.config['SECRET_KEY'] = 'prescription_scanner_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Create necessary directories
os.makedirs("temp", exist_ok=True)
os.makedirs("cache", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Configure APScheduler for handling reminders
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
scheduler.start()

# Global user reminders dictionary (in-memory cache)
user_reminders = {}

# LRU cache size
CACHE_SIZE = 1000

class MedicationDatabase:
    def __init__(self):
        self.local_db = self._initialize_local_db()
        self.api_cache = {}  # Cache API results to avoid repeated calls
        self.name_index = {}  # Index for faster name lookups
        self._build_index()
        
    def _initialize_local_db(self):
        """Initialize a basic local database with common medications"""
        # This is a fallback database that will be used if API calls fail
        medications = [
            {"name": "Amoxicillin", "common_dose": "500mg", "category": "antibiotic"},
            {"name": "Lisinopril", "common_dose": "10mg", "category": "antihypertensive"},
            {"name": "Metformin", "common_dose": "500mg", "category": "antidiabetic"},
            {"name": "Atorvastatin", "common_dose": "20mg", "category": "statin"},
            {"name": "Levothyroxine", "common_dose": "50mcg", "category": "thyroid hormone"},
            {"name": "Ibuprofen", "common_dose": "400mg", "category": "NSAID"},
            {"name": "Paracetamol", "common_dose": "500mg", "category": "analgesic"},
            {"name": "Aspirin", "common_dose": "75mg", "category": "antiplatelet"},
            {"name": "Omeprazole", "common_dose": "20mg", "category": "PPI"},
            {"name": "Amlodipine", "common_dose": "5mg", "category": "calcium channel blocker"}
        ]
        
        # Try to load from a local CSV if it exists (for expanded database)
        if os.path.exists("data/medications_db.csv"):
            try:
                df = pd.read_csv("data/medications_db.csv")
                logger.info(f"Loaded {len(df)} medications from local database")
                return df
            except Exception as e:
                logger.error(f"Error loading local database: {e}")
        
        return pd.DataFrame(medications)
    
    def _build_index(self):
        """Build index for faster medication name lookups"""
        for idx, row in self.local_db.iterrows():
            med_name = row['name'].lower()
            # Add full name
            self.name_index[med_name] = row['name']
            
            # Add word parts for partial matching
            words = med_name.split()
            for word in words:
                if len(word) > 3:  # Skip very short words
                    if word not in self.name_index:
                        self.name_index[word] = row['name']
        
        logger.info(f"Built index with {len(self.name_index)} entries")
    
    @lru_cache(maxsize=CACHE_SIZE)
    def search_medication(self, name, threshold=80):
        """Search for a medication using fuzzy matching with caching"""
        # Quick exact lookup in the index
        name_lower = name.lower()
        if name_lower in self.name_index:
            return self.name_index[name_lower]
        
        # Check API cache first
        if name_lower in self.api_cache:
            return self.api_cache[name_lower]
        
        # Fuzzy match in local database
        meds = self.local_db['name'].tolist()
        match = process.extractOne(name, meds, scorer=fuzz.token_sort_ratio)
        
        if match and match[1] >= threshold:
            return match[0]
        
        # If not found with high confidence, try API
        api_result = self._search_api(name)
        if api_result:
            return api_result
        
        # If no good match found and confidence is reasonable, return the best match
        if match and match[1] >= 65:  # Lower threshold for fallback
            return match[0]
        
        return None
    
    @lru_cache(maxsize=CACHE_SIZE)
    def _search_api(self, name):
        """Search for medication using RxNorm API with caching"""
        # Lower case for consistent caching
        name_lower = name.lower()
        
        # Check cache first
        if name_lower in self.api_cache:
            return self.api_cache[name_lower]
        
        try:
            # RxNorm API for drug name lookup
            url = f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={name_lower}&maxEntries=1"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if 'approximateGroup' in data and 'candidate' in data['approximateGroup']:
                    candidates = data['approximateGroup']['candidate']
                    if candidates and len(candidates) > 0:
                        # Get the RxCUI (RxNorm Concept Unique Identifier)
                        rxcui = candidates[0]['rxcui']
                        med_name = candidates[0]['name']
                        
                        # Add to local database and cache
                        new_row = pd.DataFrame([{'name': med_name, 'rxcui': rxcui, 'source': 'RxNorm API'}])
                        self.local_db = pd.concat([self.local_db, new_row], ignore_index=True)
                        self.api_cache[name_lower] = med_name
                        self.name_index[name_lower] = med_name
                        
                        return med_name
        except Exception as e:
            logger.error(f"API lookup error: {e}")
        
        return None
    
    def save_to_local_db(self):
        """Save the expanded database to CSV for future use"""
        self.local_db.to_csv("data/medications_db.csv", index=False)
        logger.info(f"Saved {len(self.local_db)} medications to local database")

        # Save the API cache and name index for faster loading next time
        try:
            with open('cache/med_api_cache.pkl', 'wb') as f:
                pickle.dump(self.api_cache, f)
            with open('cache/med_name_index.pkl', 'wb') as f:
                pickle.dump(self.name_index, f)
            logger.info("Saved medication cache and index")
        except Exception as e:
            logger.error(f"Error saving cache files: {e}")

# Initialize medication database
med_db = MedicationDatabase()

class PrescriptionScanner:
    def __init__(self):
        # Enhanced medication extraction patterns with more flexibility
        self.med_patterns = {
            'dose': r'(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|tablet|tab|capsule|cap|pill)s?)|(\d+/\d+\s*(?:Morning|Night|Evening))',
            'frequency': r'(\d+\s*times?\s*(?:a|per)\s*day|every\s*\d+\s*hours?|daily|twice\s*daily|once\s*daily|morning|evening|night|afternoon|tid|bid|qid|qd|q\d+h|\d+\s*(?:Morning|Night|Evening|Aft|Eve)|\d+\-\d+\-\d+|\d+\s*\+\s*\d+|\d+\s*when\s*required)',
            'duration': r'(?:for|x)?\s*(\d+\s*(?:days?|weeks?|months?|years?)|Tot[:\.]\s*\d+\s*(?:Tab|Cap))'
        }
        
        # Expanded abbreviations dictionary
        self.med_abbreviations = {
            'qd': 'once daily',
            'bid': 'twice daily', 
            'tid': 'three times daily',
            'qid': 'four times daily',
            'prn': 'as needed',
            'po': 'by mouth',
            'q4h': 'every 4 hours',
            'q6h': 'every 6 hours',
            'q8h': 'every 8 hours',
            'q12h': 'every 12 hours',
            'ac': 'before meals',
            'pc': 'after meals',
            'od': 'once daily',
            'bd': 'twice daily',
            'tds': 'three times daily',
            'qds': 'four times daily',
            'sos': 'as needed'
        }
        
        # Add meal-related patterns
        self.meal_patterns = {
            'before_food': r'(?:before\s*(?:food|meals?)|empty\s*stomach)',
            'after_food': r'(?:after\s*(?:food|meals?))',
            'with_food': r'(?:with\s*(?:food|meals?))'
        }
        
        # Initialize image cache
        self.image_cache = {}
        self._load_cached_data()
    
    def _load_cached_data(self):
        """Load cached data from disk if available"""
        try:
            # Load image processing cache
            if os.path.exists('cache/image_cache.pkl'):
                with open('cache/image_cache.pkl', 'rb') as f:
                    self.image_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.image_cache)} cached image results")
                
            # Load API cache and name index for medication database
            if os.path.exists('cache/med_api_cache.pkl'):
                with open('cache/med_api_cache.pkl', 'rb') as f:
                    med_db.api_cache = pickle.load(f)
            if os.path.exists('cache/med_name_index.pkl'):
                with open('cache/med_name_index.pkl', 'rb') as f:
                    med_db.name_index = pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading cached data: {e}")
    
    def _get_image_hash(self, image_path):
        """Generate a unique hash for an image to use as cache key"""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def preprocess_image(self, image_path):
        """Preprocess the prescription image for better OCR results"""
        # Check cache first
        image_hash = self._get_image_hash(image_path)
        if image_hash in self.image_cache and 'processed_path' in self.image_cache[image_hash]:
            cached_path = self.image_cache[image_hash]['processed_path']
            if os.path.exists(cached_path):
                logger.info(f"Using cached processed image: {cached_path}")
                return cached_path
        
        # Read the image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Save preprocessed image for OCR
        processed_path = f"cache/processed_{image_hash}.jpg"
        cv2.imwrite(processed_path, opening)
        
        # Update cache
        if image_hash not in self.image_cache:
            self.image_cache[image_hash] = {}
        self.image_cache[image_hash]['processed_path'] = processed_path
        
        return processed_path
    
    @lru_cache(maxsize=CACHE_SIZE)
    def extract_text(self, image_path):
        """Extract text from the prescription image using OCR with caching"""
        # Check cache first
        image_hash = self._get_image_hash(image_path)
        if image_hash in self.image_cache and 'extracted_text' in self.image_cache[image_hash]:
            logger.info("Using cached OCR result")
            return self.image_cache[image_hash]['extracted_text']
        
        # Process the image
        processed_path = self.preprocess_image(image_path)
        
        # Use Tesseract for OCR
        img = Image.open(processed_path)
        text = pytesseract.image_to_string(img, config='--psm 6')
        
        # Update cache
        if image_hash not in self.image_cache:
            self.image_cache[image_hash] = {}
        self.image_cache[image_hash]['extracted_text'] = text
        
        # Save cache periodically
        self._save_cache()
        
        return text
    
    def _save_cache(self):
        """Save the image cache to disk"""
        try:
            with open('cache/image_cache.pkl', 'wb') as f:
                pickle.dump(self.image_cache, f)
        except Exception as e:
            logger.error(f"Error saving image cache: {e}")
    
    def identify_medications(self, text):
        """Extract medication information from prescription text with enhanced detection"""
        medications = []
        
        # Split text into lines and paragraphs
        lines = text.split('\n')
        paragraphs = text.split('\n\n')
        
        # Look for Rx symbol or Medicine/Tab/Cap sections to find prescription section
        prescription_section = ""
        
        # Check for Rx marker or medicine sections
        rx_section_found = False
        for i, line in enumerate(lines):
            if re.search(r'(^|\s)R[xX](\s|$)|Medicine|Medication|TAB\.|CAP\.|Tablet|Dosage', line):
                rx_section_found = True
                prescription_section = '\n'.join(lines[i:])
                break
        
        if not rx_section_found:
            # If no clear marker, use the whole text
            prescription_section = text
        
        # Split prescription section into potential medication entries
        potential_entries = []
        
        # Try to identify numbered list items (common in prescriptions)
        numbered_items = re.findall(r'(?:\d+[\)\.]|\*|\-)\s*(.+?)(?=\n\d+[\)\.|\*|\-]|\n\n|$)', prescription_section, re.DOTALL)
        if numbered_items:
            potential_entries.extend(numbered_items)
        
        # If no numbered items found, try splitting by lines or other separators
        if not potential_entries:
            # Try to split based on medicine names or new lines
            potential_entries = [p for p in prescription_section.split('\n') if len(p.strip()) > 5]
        
        # Process each potential medication entry
        for entry in potential_entries:
            # Skip entries that are too short or appear to be headers
            if len(entry.strip()) < 5 or re.search(r'(^|\s)(Advice|Follow|Doctor|Instructions|Review)(:|\s*$)', entry):
                continue
                
            med_info = {}
            
            # Extract potential medication name (first capitalized word sequence)
            med_name_match = re.search(r'([A-Z][a-zA-Z0-9\s\-]+)(?:\(|\d|\s-|\s\d)', entry)
            if med_name_match:
                potential_name = med_name_match.group(1).strip()
                # Verify through med database
                verified_name = med_db.search_medication(potential_name)
                if verified_name:
                    med_info['name'] = verified_name
                else:
                    med_info['name'] = potential_name
            
            # If no name found yet, try alternate approach
            if 'name' not in med_info:
                # Look for TAB, CAP followed by name
                alt_name_match = re.search(r'(TAB\.|CAP\.|Tablet|Capsule)[:\s]+([A-Za-z0-9\s\-]+)', entry)
                if alt_name_match:
                    potential_name = alt_name_match.group(2).strip()
                    verified_name = med_db.search_medication(potential_name)
                    if verified_name:
                        med_info['name'] = verified_name
                    else:
                        med_info['name'] = potential_name
            
            # If still no name, use first few words
            if 'name' not in med_info and len(entry.split()) > 1:
                first_words = ' '.join(entry.split()[:3])
                verified_name = med_db.search_medication(first_words)
                if verified_name:
                    med_info['name'] = verified_name
            
            # If we found a medication name, extract other properties
            if 'name' in med_info:
                # Extract dosage, frequency and duration using regex patterns
                for pattern_name, pattern in self.med_patterns.items():
                    match = re.search(pattern, entry, re.IGNORECASE)
                    if match:
                        group = match.group(1) if match.group(1) else match.group(2) if len(match.groups()) > 1 else match.group(0)
                        med_info[pattern_name] = group
                
                # Check for meal-related instructions
                for meal_pattern_name, pattern in self.meal_patterns.items():
                    if re.search(pattern, entry, re.IGNORECASE):
                        med_info['meal_instruction'] = meal_pattern_name.replace('_', ' ')
                
                # Look for common medical abbreviations
                for abbr, expansion in self.med_abbreviations.items():
                    if re.search(r'\b' + abbr + r'\b', entry, re.IGNORECASE):
                        if 'frequency' not in med_info:
                            med_info['frequency'] = expansion
                
                # Add the medication only if we have sufficient information
                if len(med_info) > 1:
                    medications.append(med_info)
        
        # If no medications found, try a more aggressive approach
        if not medications:
            for line in lines:
                if len(line.strip()) > 5 and not re.search(r'(^|\s)(Advice|Follow|Doctor|Instructions|Review)(:|\s*$)', line):
                    # Look for potential medication names in the line
                    words = line.split()
                    for i in range(len(words)):
                        for j in range(i+1, min(i+5, len(words)+1)):
                            phrase = ' '.join(words[i:j])
                            if len(phrase) > 3:  # Skip very short phrases
                                result = med_db.search_medication(phrase)
                                if result:
                                    med_info = {'name': result}
                                    # Look for dosage pattern near the medication name
                                    for pattern_name, pattern in self.med_patterns.items():
                                        match = re.search(pattern, line, re.IGNORECASE)
                                        if match:
                                            group = match.group(1) if match.group(1) else match.group(0)
                                            med_info[pattern_name] = group
                                    
                                    # Only add if we have at least a name and one other piece of info
                                    if len(med_info) > 1:
                                        medications.append(med_info)
                                        break  # Found a medication in this line, move to next
        
        return medications
    
    def _process_text_block(self, block):
        """Process a single text block to find medications (for parallel processing)"""
        results = []
        words = block.split()
        
        # Check multi-word combinations for medication names
        potential_meds = []
        for i in range(len(words)):
            for j in range(i+1, min(i+5, len(words)+1)):  # Check phrases up to 4 words
                phrase = ' '.join(words[i:j])
                result = med_db.search_medication(phrase)
                if result:
                    potential_meds.append((result, block))
        
        # If no multi-word matches, try individual words
        if not potential_meds:
            for word in words:
                if len(word) > 3:  # Skip very short words
                    result = med_db.search_medication(word)
                    if result:
                        potential_meds.append((result, block))
        
        # Process found medications
        for med_name, context in potential_meds:
            med_info = {'name': med_name}
            
            # Extract dosage, frequency and duration using regex patterns
            for pattern_name, pattern in self.med_patterns.items():
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    med_info[pattern_name] = match.group(1)
            
            # Look for common medical abbreviations
            for abbr, expansion in self.med_abbreviations.items():
                if re.search(r'\b' + abbr + r'\b', context, re.IGNORECASE):
                    med_info['frequency'] = expansion
            
            # Only add if we have at least a name and one other piece of info
            if len(med_info) > 1:
                results.append(med_info)
        
        return results
    
    def parse_timings(self, medications):
            """Convert medication frequency to flexible time ranges based on common meal times and prescription formats"""
            for med in medications:
                time_ranges = []
                
                # Define standard time ranges
                morning_range = {'start': '07:00', 'end': '10:00', 'label': 'Morning'}
                lunch_range = {'start': '12:00', 'end': '14:00', 'label': 'Lunch'}
                evening_range = {'start': '16:00', 'end': '18:00', 'label': 'Evening'}
                night_range = {'start': '19:00', 'end': '22:00', 'label': 'Night'}
                
                # Check for frequency patterns and meal-related instructions
                if 'frequency' in med:
                    freq = med['frequency'].lower()
                    
                    # Check for specific timing patterns like "1 Morning, 1 Night"
                    morning_count = re.search(r'(\d+)\s*morning', freq, re.IGNORECASE)
                    afternoon_count = re.search(r'(\d+)\s*(?:afternoon|aft)', freq, re.IGNORECASE)
                    evening_count = re.search(r'(\d+)\s*(?:evening|eve)', freq, re.IGNORECASE)
                    night_count = re.search(r'(\d+)\s*night', freq, re.IGNORECASE)
                    
                    if morning_count or afternoon_count or evening_count or night_count:
                        if morning_count:
                            time_ranges.append(morning_range)
                        if afternoon_count:
                            time_ranges.append(lunch_range)
                        if evening_count:
                            time_ranges.append(evening_range) 
                        if night_count:
                            time_ranges.append(night_range)
                    # Numeric patterns like 1-0-1 (common in some countries)
                    elif re.search(r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)', freq):
                        match = re.search(r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)', freq)
                        morning_dose = int(match.group(1))
                        afternoon_dose = int(match.group(2))
                        night_dose = int(match.group(3))
                        
                        if morning_dose > 0:
                            time_ranges.append(morning_range)
                        if afternoon_dose > 0:
                            time_ranges.append(lunch_range)
                        if night_dose > 0:
                            time_ranges.append(night_range)
                    # Standard patterns
                    elif 'once daily' in freq or 'daily' in freq or 'qd' in freq or 'od' in freq:
                        if 'morning' in freq:
                            time_ranges = [morning_range]
                        elif 'evening' in freq:
                            time_ranges = [evening_range]
                        elif 'night' in freq:
                            time_ranges = [night_range]
                        else:
                            # Default to morning if not specified
                            time_ranges = [morning_range]
                            
                    elif 'twice daily' in freq or 'bid' in freq or 'bd' in freq:
                        time_ranges = [morning_range, night_range]
                        
                    elif 'three times' in freq or '3 times' in freq or 'tid' in freq or 'tds' in freq:
                        time_ranges = [morning_range, lunch_range, night_range]
                        
                    elif 'four times' in freq or '4 times' in freq or 'qid' in freq or 'qds' in freq:
                        time_ranges = [
                            morning_range,
                            {'start': '11:00', 'end': '12:00', 'label': 'Mid-Morning'},
                            lunch_range,
                            night_range
                        ]
                        
                    # When required / as needed / SOS
                    elif 'when required' in freq or 'as needed' in freq or 'prn' in freq or 'sos' in freq:
                        # For as-needed medications, we set a single reminder to ensure the patient has it available
                        time_ranges = [morning_range]
                        
                    # Meal-related timing
                    elif 'before meals' in freq or 'ac' in freq or ('meal_instruction' in med and med['meal_instruction'] == 'before food'):
                        time_ranges = [
                            {'start': '06:30', 'end': '07:30', 'label': 'Before breakfast'},
                            {'start': '11:30', 'end': '12:30', 'label': 'Before lunch'},
                            {'start': '18:30', 'end': '19:30', 'label': 'Before dinner'}
                        ]
                    elif 'after meals' in freq or 'pc' in freq or ('meal_instruction' in med and med['meal_instruction'] == 'after food'):
                        time_ranges = [
                            {'start': '08:30', 'end': '09:30', 'label': 'After breakfast'},
                            {'start': '13:30', 'end': '14:30', 'label': 'After lunch'},
                            {'start': '20:30', 'end': '21:30', 'label': 'After dinner'}
                        ]
                    elif 'with meals' in freq or ('meal_instruction' in med and med['meal_instruction'] == 'with food'):
                        time_ranges = [
                            {'start': '07:30', 'end': '08:30', 'label': 'With breakfast'},
                            {'start': '12:30', 'end': '13:30', 'label': 'With lunch'},
                            {'start': '19:30', 'end': '20:30', 'label': 'With dinner'}
                        ]
                        
                    # Hour-based patterns
                    elif ('every' in freq and 'hour' in freq) or any(x in freq for x in ['q4h', 'q6h', 'q8h', 'q12h']):
                        # Extract hour number
                        hours = re.search(r'every\s*(\d+)\s*hours?|q(\d+)h', freq)
                        if hours:
                            try:
                                interval = int(hours.group(1) if hours.group(1) else hours.group(2))
                                # Create time ranges every 'interval' hours
                                start_hour = 8  # Start at 8 AM
                                while start_hour < 24:
                                    end_hour = (start_hour + 1) % 24
                                    time_ranges.append({
                                        'start': f'{start_hour:02d}:00',
                                        'end': f'{end_hour:02d}:00',
                                        'label': f'{start_hour:02d}:00 window'
                                    })
                                    start_hour += interval
                            except:
                                # Default to three times daily if parsing fails
                                time_ranges = [morning_range, lunch_range, night_range]
                    
                    # If no specific pattern recognized, set a default time
                    if not time_ranges:
                        time_ranges = [morning_range]
                elif 'meal_instruction' in med:
                    # If we have meal instructions but no frequency info
                    if med['meal_instruction'] == 'before food':
                        time_ranges = [
                            {'start': '06:30', 'end': '07:30', 'label': 'Before breakfast'},
                            {'start': '11:30', 'end': '12:30', 'label': 'Before lunch'},
                            {'start': '18:30', 'end': '19:30', 'label': 'Before dinner'}
                        ]
                    elif med['meal_instruction'] == 'after food':
                        time_ranges = [
                            {'start': '08:30', 'end': '09:30', 'label': 'After breakfast'},
                            {'start': '13:30', 'end': '14:30', 'label': 'After lunch'},
                            {'start': '20:30', 'end': '21:30', 'label': 'After dinner'}
                        ]
                    elif med['meal_instruction'] == 'with food':
                        time_ranges = [
                            {'start': '07:30', 'end': '08:30', 'label': 'With breakfast'},
                            {'start': '12:30', 'end': '13:30', 'label': 'With lunch'},
                            {'start': '19:30', 'end': '20:30', 'label': 'With dinner'}
                        ]
                
                # If no timing information at all, set a default
                if not time_ranges:
                    time_ranges = [morning_range]
                
                med['time_ranges'] = time_ranges
            
            return medications
    
    def create_reminders(self, user_id, medications):
        """Create reminders based on medication schedule with flexible timing"""
        today = datetime.now().date()
        reminders = []
        
        for med in medications:
            if 'name' in med and 'time_ranges' in med:
                # Calculate end date if duration is specified
                end_date = None
                if 'duration' in med:
                    duration_match = re.search(r'(\d+)\s*(day|week|month|year)', med['duration'], re.IGNORECASE)
                    if duration_match:
                        amount = int(duration_match.group(1))
                        unit = duration_match.group(2).lower()
                        
                        if 'day' in unit:
                            end_date = today + timedelta(days=amount)
                        elif 'week' in unit:
                            end_date = today + timedelta(weeks=amount)
                        elif 'month' in unit:
                            end_date = today + timedelta(days=amount*30) # Approximation
                        elif 'year' in unit:
                            end_date = today + timedelta(days=amount*365) # Approximation
                
                # Create reminder for each time range
                for time_range in med['time_ranges']:
                    # Generate a random time within the range for a more natural reminder
                    start_hour, start_min = map(int, time_range['start'].split(':'))
                    end_hour, end_min = map(int, time_range['end'].split(':'))
                    
                    start_minutes = start_hour * 60 + start_min
                    end_minutes = end_hour * 60 + end_min
                    
                    # Pick a random time within the range
                    reminder_minutes = random.randint(start_minutes, end_minutes)
                    reminder_hour = reminder_minutes // 60
                    reminder_min = reminder_minutes % 60
                    
                    reminder_time = f"{reminder_hour:02d}:{reminder_min:02d}"
                    
                    reminder = {
                        'user_id': user_id,
                        'medication': med['name'],
                        'dosage': med.get('dose', 'as prescribed'),
                        'time': reminder_time,
                        'time_label': time_range['label'],
                        'time_range': f"{time_range['start']} - {time_range['end']}",
                        'start_date': today.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                        'status': 'active',
                        'reminder_id': f"{user_id}_{med['name']}_{reminder_time}".replace(' ', '_')
                    }
                    
                    reminders.append(reminder)
                    
                    # Schedule the reminder using APScheduler
                    self._schedule_reminder(reminder)
        
        return reminders
    
    def _schedule_reminder(self, reminder):
        """Schedule a reminder using APScheduler"""
        try:
            # Parse time
            hour, minute = map(int, reminder['time'].split(':'))
            
            # Schedule job
            job_id = f"reminder_{reminder['reminder_id']}"
            
            # Remove any existing job with the same ID
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
            
            # Schedule new job
            scheduler.add_job(
                send_notification,
                'cron', 
                hour=hour, 
                minute=minute, 
                id=job_id,
                replace_existing=True,
                args=[reminder]
            )
            
            logger.info(f"Scheduled reminder for {reminder['medication']} at {reminder['time']}")
        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")

    def scan_prescription(self, user_id, image_path):
        """Process a prescription image and set up reminders"""
        start_time = time.time()
        
        # Extract text from image
        text = self.extract_text(image_path)
        text_time = time.time()
        logger.info(f"Text extraction took {text_time - start_time:.2f} seconds")
        
        # Identify medications in text
        medications = self.identify_medications(text)
        med_time = time.time()
        logger.info(f"Medication identification took {med_time - text_time:.2f} seconds")
        
        # Parse timing information
        medications = self.parse_timings(medications)
        timing_time = time.time()
        logger.info(f"Timing parsing took {timing_time - med_time:.2f} seconds")
        
        # Create reminders
        reminders = self.create_reminders(user_id, medications)
        reminder_time = time.time()
        logger.info(f"Reminder creation took {reminder_time - timing_time:.2f} seconds")
        
        # Store reminders for this user
        user_reminders[user_id] = reminders
        
        # Save any new medications we've found to our local database
        med_db.save_to_local_db()
        
        # Total processing time
        end_time = time.time()
        logger.info(f"Total processing time: {end_time - start_time:.2f} seconds")
        
        return {
            'text': text,
            'medications': medications,
            'reminders': reminders,
            'processing_time': end_time - start_time
        }

# Notification function that will be called by the scheduler
def send_notification(reminder):
    """Send a notification for a medication reminder"""
    try:
        user_id = reminder['user_id']
        message = f"Time to take your {reminder['medication']} ({reminder['dosage']})"
        
        # Send notification via SocketIO to the web client
        socketio.emit('medication_reminder', {
            'user_id': user_id,
            'medication': reminder['medication'],
            'dosage': reminder['dosage'],
            'time': reminder['time'],
            'message': message,
            'reminder_id': reminder['reminder_id']
        }, room=user_id)
        
        logger.info(f"Sent reminder notification to user {user_id} for {reminder['medication']}")
        
        # You could add other notification methods here (SMS, email, etc.)
    except Exception as e:
        logger.error(f"Error sending notification: {e}")

# Initialize the scanner
scanner = PrescriptionScanner()

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
        <head>
            <title>Global Prescription Scanner</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding-top: 20px; 
                }
                .card {
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .notification {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    max-width: 350px;
                    padding: 15px;
                    background-color: #3498db;
                    color: white;
                    border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    z-index: 1000;
                    display: none;
                    animation: slidein 0.5s ease-in-out;
                }
                @keyframes slidein {
                    from { transform: translateX(100%); }
                    to { transform: translateX(0); }
                }
                .loading {
                    display: none;
                    text-align: center;
                    padding: 20px;
                }
                .loading-spinner {
                    display: inline-block;
                    width: 2rem;
                    height: 2rem;
                    border: 3px solid rgba(0, 0, 0, 0.3);
                    border-radius: 50%;
                    border-top-color: #007bff;
                    animation: spin 1s ease-in-out infinite;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row">
                    <div class="col-md-8 mx-auto">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h2 class="mb-0">Prescription Scanner</h2>
                            </div>
                            <div class="card-body">
                                <p class="lead">This system can identify medications worldwide and create automatic reminders on your device.</p>
                                
                                <div class="card">
                                    <div class="card-header">
                                        <h4>Upload a Prescription Image</h4>
                                    </div>
                                    <div class="card-body">
                                        <form id="scanForm" action="/scan" method="post" enctype="multipart/form-data">
                                            <div class="mb-3">
                                                <label for="user_id" class="form-label">User ID</label>
                                                <input type="text" class="form-control" name="user_id" id="user_id" placeholder="Enter User ID" required>
                                            </div>
                                            <div class="mb-3">
                                                <label for="image" class="form-label">Prescription Image</label>
                                                <input type="file" class="form-control" name="image" id="image" accept="image/*" required>
                                            </div>
                                            <button type="submit" class="btn btn-primary">Scan Prescription</button>
                                        </form>
                                        <div class="loading mt-3" id="loading">
                                            <div class="loading-spinner"></div>
                                            <p class="mt-2">Processing prescription... This may take a moment.</p>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="card mt-4">
                                    <div class="card-header">
                                        <h4>Check Your Reminders</h4>
                                    </div>
                                    <div class="card-body">
                                        <form id="reminderForm">
                                            <div class="mb-3">
                                                <label for="reminder_user_id" class="form-label">User ID</label>
                                                <input type="text" class="form-control" id="reminder_user_id" placeholder="Enter User ID" required>
                                            </div>
                                            <button type="submit" class="btn btn-info">Check Reminders</button>
                                        </form>
                                    </div>
                                </div>
                                
                                <div id="results" class="mt-4"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="notification" id="notification">
                <h5 id="notif-title"></h5>
                <p id="notif-message"></p>
                <div class="d-flex justify-content-between mt-2">
                    <button class="btn btn-sm btn-light" onclick="dismissNotification()">Dismiss</button>
                    <button class="btn btn-sm btn-success" onclick="markTaken()">Mark as Taken</button>
                </div>
            </div>
            
            <script>
                // Connect to SocketIO
                const socket = io();
                let currentUserId = localStorage.getItem('current_user_id');
                let currentReminderId = null;

                // Listen for real-time reminders
                socket.on('medication_reminder', function(data) {
                    if (data.user_id === currentUserId) {
                        showNotification(data.medication, data.message, data.reminder_id);
                    }
                });

                // Join user's room for targeted notifications
                function joinUserRoom(userId) {
                    if (userId) {
                        currentUserId = userId;
                        localStorage.setItem('current_user_id', userId);
                        socket.emit('join', {user_id: userId});
                    }
                }
                
                // Show notification
                function showNotification(title, message, reminderId) {
                    currentReminderId = reminderId;
                    document.getElementById('notif-title').innerText = title;
                    document.getElementById('notif-message').innerText = message;
                    document.getElementById('notification').style.display = 'block';
                    
                    // Request permission for browser notifications
                    if (Notification.permission !== 'granted') {
                        Notification.requestPermission();
                    } else {
                        const notification = new Notification(title, {
                            body: message,
                            icon: '/static/pill_icon.png'
                        });
                        
                        notification.onclick = function() {
                            window.focus();
                            this.close();
                        };
                    }
                    
                    // Set notification to auto-dismiss after 30 seconds
                    setTimeout(dismissNotification, 30000);
                }
                
                // Dismiss notification
                function dismissNotification() {
                    document.getElementById('notification').style.display = 'none';
                    currentReminderId = null;
                }
                
                // Mark medication as taken
                function markTaken() {
                    if (currentReminderId) {
                        fetch('/mark_taken', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                user_id: currentUserId,
                                reminder_id: currentReminderId
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            dismissNotification();
                            // Refresh reminders display if it's open
                            if (document.getElementById('reminderResults')) {
                                checkReminders();
                            }
                        });
                    }
                }
                
                // Form submission handlers
                document.getElementById('scanForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const userId = document.getElementById('user_id').value;
                
                // Show loading indicator
                document.getElementById('loading').style.display = 'block';
                
                fetch('/scan', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    
                    // Join user's notification room
                    joinUserRoom(userId);
                    
                    // Display results
                    let resultsHtml = `
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h4>Prescription Analysis Results</h4>
                            </div>
                            <div class="card-body">
                                <p>Processing time: ${data.processing_time.toFixed(2)} seconds</p>
                                <h5>Identified Medications:</h5>
                                <div class="row">
                    `;
                    
                    data.medications.forEach(med => {
                        // Create a formatted display of time ranges
                        let timeRangeText = 'Not specified';
                        if (med.time_ranges && med.time_ranges.length > 0) {
                            timeRangeText = med.time_ranges.map(tr => tr.label).join(', ');
                        }
                        
                        resultsHtml += `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-header">
                                        <h5>${med.name}</h5>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Dosage:</strong> ${med.dose || 'Not specified'}</p>
                                        <p><strong>Frequency:</strong> ${med.frequency || 'Not specified'}</p>
                                        <p><strong>Duration:</strong> ${med.duration || 'Not specified'}</p>
                                        <p><strong>Reminder Times:</strong> ${timeRangeText}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    resultsHtml += `
                                </div>
                                <hr>
                                <p>Created ${data.reminders.length} reminders. These will appear on your device at the scheduled times.</p>
                                <button class="btn btn-info" onclick="checkReminders('${userId}')">View Reminders</button>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('results').innerHTML = resultsHtml;
                })
                .catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('results').innerHTML = `
                        <div class="alert alert-danger">
                            Error processing prescription: ${error}
                        </div>
                    `;
                });
            });
                
                document.getElementById('reminderForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    const userId = document.getElementById('reminder_user_id').value;
                    checkReminders(userId);
                });
                
                function checkReminders(userId = null) {
                    if (!userId) {
                        userId = document.getElementById('reminder_user_id').value;
                    }
                    
                    // Join user's notification room
                    joinUserRoom(userId);
                    
                    fetch('/reminders/' + userId)
                        .then(response => response.json())
                        .then(data => {
                            let resultsHtml = '';
                            
                            if (data.length === 0) {
                                resultsHtml = `
                                    <div class="alert alert-info">
                                        No reminders found for this user.
                                    </div>
                                `;
                            } else {
                                resultsHtml = `
                                    <div class="card" id="reminderResults">
                                        <div class="card-header bg-info text-white">
                                            <h4>Medication Reminders for ${userId}</h4>
                                        </div>
                                        <div class="card-body">
                                            <div class="table-responsive">
                                                <table class="table table-striped">
                                                    <thead>
                                                        <tr>
                                                            <th>Medication</th>
                                                            <th>Dosage</th>
                                                            <th>Time</th>
                                                            <th>End Date</th>
                                                            <th>Status</th>
                                                            <th>Actions</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                `;
                                
                                data.forEach(reminder => {
                                    resultsHtml += `
                                        <tr>
                                            <td>${reminder.medication}</td>
                                            <td>${reminder.dosage}</td>
                                            <td>${reminder.time}</td>
                                            <td>${reminder.end_date || 'Ongoing'}</td>
                                            <td>
                                                <span class="badge ${reminder.status === 'active' ? 'bg-success' : 'bg-secondary'}">
                                                    ${reminder.status}
                                                </span>
                                            </td>
                                            <td>
                                                <button class="btn btn-sm btn-danger" onclick="deleteReminder('${reminder.reminder_id}')">
                                                    Delete
                                                </button>
                                            </td>
                                        </tr>
                                    `;
                                });
                                
                                resultsHtml += `
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }
                            
                            document.getElementById('results').innerHTML = resultsHtml;
                        });
                }
                
                function deleteReminder(reminderId) {
                    if (confirm('Are you sure you want to delete this reminder?')) {
                        fetch('/delete_reminder', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                user_id: currentUserId,
                                reminder_id: reminderId
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                checkReminders(currentUserId);
                            }
                        });
                    }
                }
                
                // Request notification permission on page load
                document.addEventListener('DOMContentLoaded', function() {
                    if (Notification.permission !== 'granted') {
                        Notification.requestPermission();
                    }
                    
                    // Restore user ID from localStorage if available
                    const storedUserId = localStorage.getItem('current_user_id');
                    if (storedUserId) {
                        document.getElementById('user_id').value = storedUserId;
                        document.getElementById('reminder_user_id').value = storedUserId;
                        joinUserRoom(storedUserId);
                    }
                });
            </script>
        </body>
    </html>
    '''

@app.route('/scan', methods=['POST'])
def scan_prescription():
    """API endpoint to scan a prescription"""
    # Check if request contains file and user_id
    if 'image' not in request.files or 'user_id' not in request.form:
        return jsonify({'error': 'Missing image or user_id'}), 400
    
    user_id = request.form['user_id']
    image = request.files['image']
    
    # Save the image temporarily
    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/upload_{user_id}_{int(time.time())}.jpg"
    image.save(temp_path)
    
    # Process the prescription
    try:
        result = scanner.scan_prescription(user_id, temp_path)
        
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing prescription: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500

@app.route('/reminders/<user_id>', methods=['GET'])
def get_reminders(user_id):
    """Get all reminders for a user"""
    if user_id in user_reminders:
        return jsonify(user_reminders[user_id])
    return jsonify([])

@app.route('/mark_taken', methods=['POST'])
def mark_taken():
    """Mark a reminder as taken"""
    data = request.json
    user_id = data.get('user_id')
    reminder_id = data.get('reminder_id')
    
    if not user_id or not reminder_id:
        return jsonify({'error': 'Missing user_id or reminder_id'}), 400
    
    if user_id in user_reminders:
        for reminder in user_reminders[user_id]:
            if reminder['reminder_id'] == reminder_id:
                # Update reminder status
                reminder['status'] = 'taken'
                # Log the action
                logger.info(f"User {user_id} marked {reminder['medication']} as taken")
                return jsonify({'success': True})
    
    return jsonify({'error': 'Reminder not found'}), 404

@app.route('/delete_reminder', methods=['POST'])
def delete_reminder():
    """Delete a reminder"""
    data = request.json
    user_id = data.get('user_id')
    reminder_id = data.get('reminder_id')
    
    if not user_id or not reminder_id:
        return jsonify({'error': 'Missing user_id or reminder_id'}), 400
    
    if user_id in user_reminders:
        # Find the reminder
        for i, reminder in enumerate(user_reminders[user_id]):
            if reminder['reminder_id'] == reminder_id:
                # Remove from scheduler
                job_id = f"reminder_{reminder_id}"
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                
                # Remove from reminders list
                user_reminders[user_id].pop(i)
                logger.info(f"User {user_id} deleted reminder for {reminder['medication']}")
                return jsonify({'success': True})
    
    return jsonify({'error': 'Reminder not found'}), 404

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('join')
def on_join(data):
    """Join a user-specific room for targeted notifications"""
    user_id = data.get('user_id')
    if user_id:
        # Changed from socketio.join_room to the correct call
        join_room(user_id)  
        logger.info(f"User {user_id} joined notification room")

if __name__ == '__main__':
    print("\n==== Optimized Global Medical Prescription Scanner System ====")
    print("Server starting on http://localhost:8020")
    print("1. Open the URL in your browser")
    print("2. Upload a prescription image")
    print("3. The system will extract medications and create reminders")
    print("4. You'll receive notifications on your device at the scheduled times")
    print("===========================================\n")
    
    # Create icon for notifications
    try:
        os.makedirs("static", exist_ok=True)
        # Create a simple pill icon if it doesn't exist
        if not os.path.exists("static/pill_icon.png"):
            pill_icon = np.ones((64, 64, 3), dtype=np.uint8) * 255
            # Draw a simple pill shape
            cv2.ellipse(pill_icon, (32, 32), (25, 15), 45, 0, 360, (52, 152, 219), -1)
            cv2.ellipse(pill_icon, (32, 32), (25, 15), 45, 0, 360, (41, 128, 185), 2)
            # Save the icon
            cv2.imwrite("static/pill_icon.png", pill_icon)
    except Exception as e:
        logger.error(f"Error creating pill icon: {e}")
    
    # Start the server with socketio instead of app.run()
    socketio.run(app, debug=True, host='0.0.0.0', port=8020)