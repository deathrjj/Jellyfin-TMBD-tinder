# Jellyfin Suggestion System

A web-based recommendation system that helps you discover new movies and TV shows based on your existing Jellyfin library. The system uses The Movie Database (TMDb) API to find similar content and presents suggestions in an intuitive web interface.

## 🎬 Features

- **Smart Recommendations**: Analyzes your Jellyfin library to suggest similar movies and shows
- **Beautiful Web Interface**: Modern, responsive design for easy browsing
- **Interactive Rating**: Simple Yes/No interface to rate suggestions
- **Dynamic Learning**: Recommendations improve based on your preferences
- **Export Functionality**: Save your liked items to CSV
- **Real-time Updates**: New suggestions generated based on your choices

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- TMDb API key (free from [themoviedb.org](https://www.themoviedb.org/settings/api))
- Your Jellyfin library exported as `Jellyfin.csv`

### Installation

1. **Clone or download this project**
   ```bash
   git clone <repository-url>
   cd jellyfin-suggestion
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up TMDb API key**
   ```bash
   export TMDB_API_KEY="your_api_key_here"
   ```
   
   Or on Windows:
   ```cmd
   set TMDB_API_KEY=your_api_key_here
   ```

4. **Prepare your Jellyfin library data**
   
   Create a `Jellyfin.csv` file with your movies and shows:
   ```csv
   Name,Type
   The Matrix,Movie
   Breaking Bad,Show
   Inception,Movie
   ```

### Usage

#### Step 1: Generate Initial Suggestions

Run the suggestion generator to analyze your library and create recommendations:

```bash
python generate_suggestions.py
```

This will:
- Read your `Jellyfin.csv` library
- Search TMDb for each item
- Find similar movies and shows
- Generate a `suggestions.csv` file with recommendations sorted by popularity

#### Step 2: Start the Web Application

Launch the interactive web interface:

```bash
python app.py
```

Then open your browser to `http://localhost:5000`

#### Step 3: Rate Suggestions

The web interface will show you one suggestion at a time with:
- **Movie/Show poster** (when available)
- **Title and description** from TMDb
- **Recommendation count** (how many of your items suggested this)
- **Yes/No buttons** for rating

**When you click "Yes":**
- The item is marked as liked
- New similar suggestions are automatically generated
- The system learns from your preference

**When you click "No":**
- The item is removed from suggestions
- You proceed to the next highest-rated suggestion

#### Step 4: Export Your Likes

At any time, click the "Export Likes" button to save all your liked items to `likes.csv`.

## 📁 File Structure

```
jellyfin-suggestion/
├── app.py                 # Flask web application
├── generate_suggestions.py # Initial suggestion generator
├── requirements.txt       # Python dependencies
├── Jellyfin.csv          # Your library (you create this)
├── suggestions.csv       # Generated suggestions
├── likes.csv            # Your exported likes
├── templates/
│   ├── index.html       # Main suggestion interface
│   └── complete.html    # Completion page
└── README.md           # This file
```

## 🔧 Configuration

### Environment Variables

- `TMDB_API_KEY`: Your TMDb API key (required)

### CSV File Formats

**Jellyfin.csv** (input):
```csv
Name,Type
The Matrix,Movie
Breaking Bad,Show
```

**suggestions.csv** (generated):
```csv
Name,Type,Count,Shown
Blade Runner,Movie,5,0
Westworld,Show,3,1
```

**likes.csv** (exported):
```csv
Name,Type,Count
Blade Runner,Movie,5
```

## 🎯 How It Works

1. **Analysis**: The system analyzes your Jellyfin library using TMDb's similarity API
2. **Scoring**: Suggestions are ranked by how many items in your library recommend them
3. **Learning**: When you like a suggestion, it finds similar content and updates recommendations
4. **Filtering**: Already owned content and rejected suggestions are automatically filtered out

## 🛠️ Troubleshooting

### Common Issues

**"ERROR: Please set TMDB_API_KEY"**
- Make sure you've exported the TMDB_API_KEY environment variable
- Verify your API key is valid at [TMDb API documentation](https://developers.themoviedb.org/3)

**No suggestions appear**
- Check that `suggestions.csv` exists and has entries with `Shown = 0`
- Verify your `Jellyfin.csv` contains valid movie/show names
- Run `generate_suggestions.py` to create initial suggestions

**Thumbnails not loading**
- This is normal for some titles that don't have images on TMDb
- The system will show a placeholder instead

**Web interface not accessible**
- Ensure Flask is running on port 5000
- Check for firewall or port conflicts
- Try accessing `http://127.0.0.1:5000` instead

### Rate Limiting

The system includes built-in rate limiting (0.25 seconds between API calls) to respect TMDb's usage policies. Initial generation for large libraries may take some time.

## 🔄 Advanced Usage

### Regenerating Suggestions

To get fresh suggestions based on new additions to your library:

1. Update your `Jellyfin.csv` with new content
2. Run `python generate_suggestions.py` again
3. New suggestions will be added to existing ones

### Customizing the Interface

The web interface uses modern CSS with gradients and animations. You can customize the look by editing the `<style>` section in the HTML templates.

### Batch Operations

For power users who want to process many suggestions quickly, you can directly edit the `suggestions.csv` file:
- Set `Shown = 1` for items you like
- Delete rows for items you don't want to see
- Modify `Count` values to adjust ranking

## 📊 Statistics

The system tracks several metrics:
- **Count**: How many items in your library suggest this content
- **Shown**: Whether you've seen and rated this suggestion (0 = no, 1 = yes)
- **Type**: Movie or Show classification

Higher count values indicate content that's more aligned with your existing library's themes and genres.

## 🤝 Contributing

This project welcomes contributions! Some ideas for enhancements:
- Additional metadata sources beyond TMDb
- Machine learning-based preference modeling
- Integration with other media servers
- Recommendation explanations ("Because you liked X, Y, Z...")
- Social features for sharing recommendations

## 📄 License

This project is open source. Please ensure you comply with TMDb's API terms of service when using their data.

## 🙏 Acknowledgments

- [The Movie Database (TMDb)](https://www.themoviedb.org/) for providing the recommendation data
- [Flask](https://flask.palletsprojects.com/) for the web framework
- The Jellyfin community for inspiration 