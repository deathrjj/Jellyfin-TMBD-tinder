#!/usr/bin/env python3
import os
import csv
import requests
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Configuration
SUGGESTIONS_CSV = "suggestions.csv"
LIKES_CSV = "likes.csv"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
RATE_LIMIT = 0.25

def read_suggestions():
    """Read suggestions.csv and return list of dictionaries"""
    suggestions = []
    try:
        with open(SUGGESTIONS_CSV, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                suggestions.append({
                    'Name': row['Name'],
                    'Type': row['Type'],
                    'Count': int(row['Count']),
                    'Shown': int(row['Shown'])
                })
    except FileNotFoundError:
        return []
    return suggestions

def write_suggestions(suggestions):
    """Write suggestions list back to CSV"""
    with open(SUGGESTIONS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Type', 'Count', 'Shown'])
        for item in suggestions:
            writer.writerow([item['Name'], item['Type'], item['Count'], item['Shown']])

def get_next_suggestion():
    """Get the first entry where Shown = 0, sorted by Count descending"""
    suggestions = read_suggestions()
    unshown = [s for s in suggestions if s['Shown'] == 0]
    if not unshown:
        return None
    # Sort by count descending
    unshown.sort(key=lambda x: x['Count'], reverse=True)
    return unshown[0]

def tmdb_search(title, content_type):
    """Search TMDb for a movie or TV show by title"""
    if not TMDB_API_KEY:
        return None
        
    base_url = "https://api.themoviedb.org/3/search/"
    if content_type.lower() == "movie":
        url = base_url + "movie"
    elif content_type.lower() in ("show", "tv"):
        url = base_url + "tv"
    else:
        return None

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "page": 1,
        "include_adult": False,
    }

    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0]
    except:
        pass
    return None

def tmdb_get_similar(tmdb_id, content_type):
    """Get similar items from TMDb"""
    if not TMDB_API_KEY:
        return []
        
    if content_type.lower() == "movie":
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/similar"
    else:
        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/similar"

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "page": 1,
    }
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        return data.get("results", [])
    except:
        return []

def get_tmdb_details(title, content_type):
    """Get title, description, thumbnail, and year from TMDb"""
    result = tmdb_search(title, content_type)
    if not result:
        return {
            'title': title,
            'description': 'No description available',
            'thumbnail': None,
            'tmdb_id': None,
            'year': None
        }
    
    poster_path = result.get('poster_path')
    thumbnail = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    
    # Extract year from release_date (movies) or first_air_date (TV shows)
    year = None
    if content_type.lower() == "movie":
        release_date = result.get('release_date')
        if release_date:
            year = release_date.split('-')[0]  # Extract year from YYYY-MM-DD format
    else:  # TV show
        first_air_date = result.get('first_air_date')
        if first_air_date:
            year = first_air_date.split('-')[0]  # Extract year from YYYY-MM-DD format
    
    return {
        'title': result.get('title') or result.get('name', title),
        'description': result.get('overview', 'No description available'),
        'thumbnail': thumbnail,
        'tmdb_id': result.get('id'),
        'year': year
    }

def update_recommendations(title, content_type):
    """Update recommendations based on a liked item"""
    if not TMDB_API_KEY:
        return
        
    # Search for the item and get similar items
    tmdb_result = tmdb_search(title, content_type)
    if not tmdb_result:
        return
        
    tmdb_id = tmdb_result.get('id')
    if not tmdb_id:
        return
        
    time.sleep(RATE_LIMIT)
    similar_items = tmdb_get_similar(tmdb_id, content_type)
    time.sleep(RATE_LIMIT)
    
    # Read current suggestions
    suggestions = read_suggestions()
    suggestions_dict = {(s['Name'], s['Type']): s for s in suggestions}
    
    # Read downloaded items to skip them
    downloaded = set()
    try:
        with open("Jellyfin.csv", 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                downloaded.add(row['Name'].strip().lower())
    except FileNotFoundError:
        pass
    
    # Process similar items
    for sim in similar_items:
        sim_name = sim.get('title') or sim.get('name')
        if not sim_name:
            continue
            
        # Skip if already downloaded
        if sim_name.lower() in downloaded:
            continue
            
        sim_type = "Movie" if sim.get('media_type', content_type.lower()) == "movie" else "Show"
        key = (sim_name.strip(), sim_type)
        
        if key in suggestions_dict:
            # Increment count
            suggestions_dict[key]['Count'] += 1
        else:
            # Add new suggestion
            suggestions_dict[key] = {
                'Name': sim_name.strip(),
                'Type': sim_type,
                'Count': 1,
                'Shown': 0
            }
    
    # Convert back to list and sort by count
    suggestions = list(suggestions_dict.values())
    suggestions.sort(key=lambda x: x['Count'], reverse=True)
    
    # Write back to CSV
    write_suggestions(suggestions)

@app.route('/')
def index():
    """Main page showing current suggestion"""
    suggestion = get_next_suggestion()
    if not suggestion:
        return render_template('complete.html')
    
    # Get TMDb details
    details = get_tmdb_details(suggestion['Name'], suggestion['Type'])
    
    return render_template('index.html', 
                         suggestion=suggestion, 
                         details=details)

@app.route('/action', methods=['POST'])
def handle_action():
    """Handle Yes/No action"""
    action = request.form.get('action')
    title = request.form.get('title')
    content_type = request.form.get('type')
    
    suggestions = read_suggestions()
    
    if action == 'no':
        # Remove the entry
        suggestions = [s for s in suggestions if not (s['Name'] == title and s['Type'] == content_type)]
        # Write back to CSV
        write_suggestions(suggestions)
    elif action == 'yes':
        # Mark as shown and write to CSV first
        for s in suggestions:
            if s['Name'] == title and s['Type'] == content_type:
                s['Shown'] = 1
                break
        write_suggestions(suggestions)
        
        # Update recommendations (this will read, update, and write the CSV again)
        update_recommendations(title, content_type)
    
    return redirect(url_for('index'))

@app.route('/export')
def export_likes():
    """Export all liked items to likes.csv"""
    suggestions = read_suggestions()
    liked = [s for s in suggestions if s['Shown'] == 1]
    
    with open(LIKES_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Type', 'Count'])
        for item in liked:
            writer.writerow([item['Name'], item['Type'], item['Count']])
    
    return jsonify({'status': 'success', 'count': len(liked)})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 