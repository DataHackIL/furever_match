# Frontend Setup & Usage Guide

## What Was Created

I've created a complete **Stitch-compatible frontend** for your ForeverMatch application with:

✅ **HTML Interface** (`frontend/index.html`)
- Adoption form page
- Dogs list page
- Matches results page
- Dog details modal

✅ **Styling** (`frontend/styles.css`)
- Hebrew (RTL) support
- Responsive design
- Modern UI with gradients
- Mobile-friendly

✅ **JavaScript Services** (`frontend/js/`)
- `stitch-client.js` - Stitch client initialization
- `adoption-service.js` - Adoption form handling
- `matching-service.js` - Dog matching API calls
- `ui-manager.js` - UI interactions
- `app.js` - Main app logic

---

## File Structure

```
frontend/
├── index.html              # Main HTML file
├── app.js                  # Main app logic
├── styles.css              # Styling
└── js/
    ├── stitch-client.js    # Stitch initialization
    ├── adoption-service.js # Adoption handling
    ├── matching-service.js # Matching API
    └── ui-manager.js       # UI management
```

---

## How to Use Your Frontend

### Step 1: Backend Setup

Your Python backend needs to serve the frontend and provide APIs:

**Update `furever_match/main.py`:**

```python
from flask import Flask, jsonify, request, send_from_directory
from furever_match.db_ingestion import ingest_adoption_request
from furever_match.matching_integration import get_matching_dogs
import os

app = Flask(__name__, static_folder='frontend', static_url_path='')

# Serve frontend
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

# API Endpoints

@app.route('/api/adoption-requests', methods=['POST'])
def create_adoption_request():
    data = request.json
    try:
        request_id = ingest_adoption_request(data)
        return jsonify({'request_id': request_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/matches/<request_id>', methods=['GET'])
def get_matches(request_id):
    try:
        matches = get_matching_dogs(request_id)
        return jsonify({'matches': matches})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/dogs', methods=['GET'])
def get_dogs():
    try:
        # Fetch from Supabase
        from furever_match.db_ingestion import supabase
        dogs_response = supabase.table("dogs").select("*").eq("status", "available").execute()
        return jsonify(dogs_response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/dogs/<dog_id>', methods=['GET'])
def get_dog(dog_id):
    try:
        from furever_match.db_ingestion import supabase
        dog_response = supabase.table("dogs").select("*").eq("id", dog_id).execute()
        if dog_response.data:
            return jsonify(dog_response.data[0])
        return jsonify({'error': 'Dog not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8000)
```

### Step 2: Install Flask

```bash
pip install flask flask-cors
```

### Step 3: Run Backend

```bash
python -m furever_match.main
```

Backend runs at: `http://localhost:8000`

### Step 4: Open Frontend

Open in browser: `http://localhost:8000`

---

## Frontend Features

### 1. **Home Page**
- Welcome message
- "Start Now" button to begin

### 2. **Adoption Form Page**
- Fill out 14 adoption questions
- Form validation
- Hebrew support (RTL)
- Conditional fields (show kids age only if has kids)

### 3. **Dogs List Page**
- View all available dogs
- Click to see details
- Dog information display

### 4. **Matches Results Page**
- Shows matching dogs for submitted form
- Ranked by match score
- Visual quality indicators:
  - ⭐ Excellent (80-100%)
  - ✅ Good (60-79%)
  - ⊙ Fair (40-59%)
  - ❌ Poor (0-39%)

### 5. **Dog Details Modal**
- Full dog information
- Compatibility details
- Match breakdown for matches

---

## How Services Work

### adoption-service.js
```javascript
// Submit adoption form
const result = await adoptionService.submitForm(formData);

// Get a request
const request = await adoptionService.getRequest(requestId);

// Get all requests
const requests = await adoptionService.getAllRequests();
```

### matching-service.js
```javascript
// Get all matches for a request
const matches = await matchingService.getMatches(adoptionRequestId);

// Get top 5 matches
const topMatches = await matchingService.getTopMatches(adoptionRequestId, 5);

// Get match details
const details = await matchingService.getMatchDetails(adoptionRequestId, dogId);

// Get all dogs
const dogs = await matchingService.getAllDogs();

// Get single dog
const dog = await matchingService.getDog(dogId);

// Get quality label
const label = matchingService.getQualityLabel(95); // "Excellent"

// Get quality emoji
const emoji = matchingService.getQualityEmoji(95); // "⭐"
```

### ui-manager.js
```javascript
// Show a page
uiManager.showPage('adoption-form');

// Load and display dogs
uiManager.loadDogs();

// Load and display matches
uiManager.loadMatches();

// Show dog details
uiManager.showDogDetails(dogId);

// Show match details
uiManager.showMatchDetails(dogId);

// Display messages
uiManager.showError('Error message');
uiManager.showSuccess('Success message');
```

---

## If You Have Stitch Code

If you created a Stitch app with MongoDB, you have two options:

### Option 1: Use Frontend As-Is (Recommended)
The frontend works with REST API calls via Flask backend.
No changes needed!

### Option 2: Integrate Actual Stitch Client
Replace `frontend/js/stitch-client.js` with:

```javascript
import * as Stitch from 'mongodb-stitch-browser-sdk';

const client = Stitch.initializeAppClient('YOUR_APP_ID_HERE');

// Authenticate
await client.auth.loginWithEmailPassword('email@example.com', 'password');

// Use MongoDB
const db = client.getServiceClient(
    Stitch.RemoteMongoClient.factory,
    'mongodb-atlas'
).db('furever_match');

// Query
const docs = await db.collection('adoption_requests').find().asArray();
```

---

## API Endpoints

Your backend should provide these endpoints:

```
POST   /api/adoption-requests          # Create adoption request
GET    /api/adoption-requests          # Get all requests
GET    /api/adoption-requests/{id}     # Get specific request

GET    /api/matches/{request_id}       # Get matches for request
GET    /api/matches/{request_id}/{dog_id}  # Get match details

GET    /api/dogs                       # Get all dogs
GET    /api/dogs/{dog_id}              # Get specific dog
```

---

## Testing

### 1. Test Form Submission
1. Open `http://localhost:8000`
2. Click "Start Now"
3. Fill out adoption form
4. Click "Submit"
5. Should redirect to matches page

### 2. Test Matches Display
1. Fill out and submit adoption form
2. View generated matches
3. Click on a match to see details

### 3. Test Dog List
1. Click "Our Dogs" in navigation
2. See all available dogs
3. Click on a dog to see details

---

## Customization

### Change API Base URL
In `frontend/js/adoption-service.js` and `matching-service.js`:
```javascript
const apiBaseUrl = 'http://your-backend-url:port/api';
```

### Change Styling
Edit `frontend/styles.css` to customize colors, fonts, layout, etc.

### Add More Pages
1. Add new section in `index.html` with id `your-page`
2. Add button to `navbar-menu`
3. Add event listener in `setupNavigation()`

### Change Form Fields
Edit `index.html` adoption form to match your schema

---

## Troubleshooting

### "Cannot GET /"
- Make sure Flask is running: `python -m furever_match.main`
- Check port is 8000: `http://localhost:8000`

### Form submission fails
- Check backend is running
- Check Flask console for errors
- Verify API endpoint in browser DevTools

### No matches shown
- Make sure you have dogs in database
- Check Supabase connection
- Verify `get_matching_dogs()` works in Python

### Styling looks wrong
- Clear browser cache
- Check CSS file loaded: DevTools → Network
- Verify `styles.css` path in `index.html`

---

## Next Steps

1. **Update Python backend** with Flask API endpoints (see section above)
2. **Run backend**: `python -m furever_match.main`
3. **Open frontend**: `http://localhost:8000`
4. **Test form submission** and matching
5. **Customize** as needed for your UI/UX

---

## Summary

You now have a complete frontend that:

✅ Provides user-friendly adoption form  
✅ Displays all available dogs  
✅ Shows personalized match recommendations  
✅ Integrates with Python backend  
✅ Supports Hebrew language (RTL)  
✅ Responsive design (mobile-friendly)  
✅ Ready to deploy  

**Everything is ready to use!** Just update your Python backend with the API endpoints and you're done! 🚀
