# Stitch App Integration Guide

## Project Structure with Stitch

Your project should now have this structure:

```
furever_match/
├── furever_match/                 # Python backend
│   ├── __init__.py
│   ├── main.py                    # Backend entry point
│   ├── config.py
│   ├── db_ingestion.py
│   ├── matching.py
│   ├── matching_integration.py
│   └── utils.py
│
├── frontend/                      # 🆕 Stitch frontend (NEW)
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── pages/
│   │   ├── adoption-form.html
│   │   ├── dog-list.html
│   │   ├── match-results.html
│   │   └── dog-details.html
│   └── js/
│       ├── stitch-client.js       # Stitch initialization
│       ├── adoption-service.js    # Adoption requests
│       ├── matching-service.js    # Matching logic
│       └── ui-manager.js          # UI updates
│
├── tests/
│   ├── test_db_ingestion.py
│   ├── test_main.py
│   └── test_matching.py
│
├── docs/                          # Documentation
│   ├── STITCH_SETUP.md
│   ├── STITCH_INTEGRATION.md
│   └── (other docs)
│
└── package.json                   # 🆕 For Node.js dependencies (if needed)
```

---

## Where to Put Your Stitch Code

### Option 1: Local Stitch App (Recommended)

Create a `frontend/` directory in your project root:

```bash
mkdir -p frontend/js
mkdir -p frontend/pages
mkdir -p frontend/assets
```

### Option 2: Structure for Your Stitch Files

**If you have HTML/JS files from Stitch:**

```
frontend/
├── index.html                 # Main page
├── app.js                     # Main app logic
├── styles.css                 # Styling
├── js/
│   ├── stitch-client.js       # Stitch client setup
│   ├── adoption-service.js    # Adoption form handler
│   ├── matching-service.js    # Matching logic
│   └── ui-manager.js          # UI interactions
└── pages/
    ├── adoption-form.html
    ├── dog-list.html
    ├── match-results.html
    └── dog-details.html
```

---

## How to Set Up Your Stitch App

### Step 1: Create Frontend Directory
```bash
cd C:\Users\hadas\PycharmProjects\furever_match
mkdir frontend
```

### Step 2: Create Main Stitch File
Place your main Stitch app file at: `frontend/index.html`

### Step 3: Create Stitch Client File
Place Stitch configuration at: `frontend/js/stitch-client.js`

```javascript
// frontend/js/stitch-client.js
import * as Stitch from 'mongodb-stitch-browser-sdk';

const client = Stitch.initializeAppClient('YOUR_APP_ID_HERE');

export { client };
```

### Step 4: Create Service Files
For your adoption matching features:

- `frontend/js/adoption-service.js` - Handle adoption form submissions
- `frontend/js/matching-service.js` - Call your Python matching API
- `frontend/js/ui-manager.js` - Update UI with results

---

## Integration Steps

### 1. Frontend → Backend Communication

Your Stitch app will communicate with Python backend via:

**Option A: HTTP Webhooks (Recommended)**
```javascript
// frontend/js/adoption-service.js
async function submitAdoptionForm(formData) {
  const response = await fetch('http://localhost:8000/api/adoption-requests', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  return response.json();
}
```

**Option B: Stitch HTTP Service**
```javascript
// Using Stitch HTTP Service to call Python API
const response = await client.callFunction('submitAdoptionRequest', [formData]);
```

**Option C: MongoDB Atlas (Shared Database)**
```javascript
// Write directly to MongoDB via Stitch
const db = client.getServiceClient(
  Stitch.RemoteMongoClient.factory,
  'mongodb-atlas'
).db('furever_match');

await db.collection('adoption_requests').insertOne(formData);
```

### 2. Call Matching API

```javascript
// frontend/js/matching-service.js
async function getMatchingDogs(adoptionRequestId) {
  const response = await fetch(
    `http://localhost:8000/api/matches/${adoptionRequestId}`,
    { method: 'GET' }
  );
  return response.json();
}
```

### 3: Update UI with Results

```javascript
// frontend/js/ui-manager.js
function displayMatches(matches) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = matches.map(match => `
    <div class="match-card">
      <h3>${match.dog_name}</h3>
      <p>Breed: ${match.breed}</p>
      <p>Match Score: ${match.match_score}%</p>
      <button onclick="showDetails('${match.dog_id}')">
        See Details
      </button>
    </div>
  `).join('');
}
```

---

## File Placement Summary

### Your Stitch HTML/JS Files Should Go Here:

| What | Where |
|------|-------|
| Main HTML | `frontend/index.html` |
| Main JS | `frontend/app.js` |
| CSS | `frontend/styles.css` |
| Stitch client setup | `frontend/js/stitch-client.js` |
| Services | `frontend/js/adoption-service.js` |
| | `frontend/js/matching-service.js` |
| | `frontend/js/ui-manager.js` |
| Pages | `frontend/pages/*.html` |

---

## If You're Using Stitch with These Features:

### Adoption Form Page
Place at: `frontend/pages/adoption-form.html`

### Dog Matching Results Page
Place at: `frontend/pages/match-results.html`

### Dog Details Page
Place at: `frontend/pages/dog-details.html`

### Dog List Page
Place at: `frontend/pages/dog-list.html`

---

## Next Steps

1. **Create frontend directory structure:**
   ```bash
   mkdir -p frontend/js
   mkdir -p frontend/pages
   ```

2. **Paste your Stitch files:**
   - Main HTML → `frontend/index.html`
   - Main JS → `frontend/app.js` or `frontend/js/app.js`
   - Stitch config → `frontend/js/stitch-client.js`

3. **Create integration files** (shown in sections above)

4. **Update Python backend** to serve frontend (see next section)

---

## Backend Integration (Python)

Update your `main.py` to serve the frontend:

```python
from flask import Flask, jsonify, request
from furever_match.db_ingestion import ingest_adoption_request
from furever_match.matching_integration import get_matching_dogs

app = Flask(__name__, static_folder='frontend', static_url_path='')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/adoption-requests', methods=['POST'])
def create_adoption_request():
    data = request.json
    request_id = ingest_adoption_request(data)
    return jsonify({'request_id': request_id})

@app.route('/api/matches/<request_id>', methods=['GET'])
def get_matches(request_id):
    matches = get_matching_dogs(request_id)
    return jsonify({'matches': matches})

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Summary

**Paste your Stitch code here:**
- Main files → `frontend/` directory
- Supporting files → `frontend/js/` directory
- Pages → `frontend/pages/` directory

**Your frontend and backend work together:**
1. User fills form in Stitch (frontend)
2. Sends to Python API (backend)
3. Backend processes and matches
4. Results sent back to frontend
5. Stitch displays results

---

## Questions to Answer

To give you more specific guidance, please share:

1. **What type of Stitch project did you create?**
   - Stitch Web Application?
   - Stitch CLI Project?
   - Something else?

2. **What files did you generate?**
   - Just index.html?
   - index.html + app.js?
   - Multiple components?

3. **Do you want to:**
   - Serve Stitch from Python backend?
   - Keep frontend and backend separate?
   - Use Stitch directly with MongoDB Atlas?

Once you share these details, I can give you exact file locations and code integration!
