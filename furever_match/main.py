"""
Main application module with Flask backend and frontend serving
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path

from furever_match.db_ingestion import ingest_adoption_request, supabase
from furever_match.matching_integration import get_matching_dogs

# Get absolute path to frontend folder
FRONTEND_PATH = Path(__file__).parent.parent / 'frontend'

# Initialize Flask app
app = Flask(__name__, static_folder=str(FRONTEND_PATH), static_url_path='')
CORS(app)


class App:
    """Main application class"""

    def __init__(self):
        """Initialize the app"""
        self.config = {}

    def run(self):
        """Run the Flask application"""
        print("FureverMatch App is running on http://localhost:8000")
        app.run(debug=True, port=8000)

    def __call__(self):
        """Make the app callable"""
        self.run()


# ============================================================
# Frontend Routes
# ============================================================

@app.route('/')
def index():
    """Serve main HTML file"""
    return send_from_directory(str(FRONTEND_PATH), 'index.html')


@app.route('/<path:filename>')
def serve_frontend(filename):
    """Serve frontend static files"""
    return send_from_directory(str(FRONTEND_PATH), filename)


# ============================================================
# API Routes - Adoption Requests
# ============================================================

@app.route('/api/adoption-requests', methods=['POST'])
def create_adoption_request():
    """Create a new adoption request"""
    try:
        data = request.json
        request_id = ingest_adoption_request(data)
        return jsonify({
            'success': True,
            'request_id': request_id
        }), 201
    except Exception as e:
        print(f"Error creating adoption request: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/adoption-requests', methods=['GET'])
def get_adoption_requests():
    """Get all adoption requests"""
    try:
        response = supabase.table('adoption_requests').select('*').execute()
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching adoption requests: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/adoption-requests/<request_id>', methods=['GET'])
def get_adoption_request(request_id):
    """Get a specific adoption request"""
    try:
        response = supabase.table('adoption_requests').select('*').eq('id', request_id).execute()
        if response.data:
            return jsonify(response.data[0]), 200
        return jsonify({'error': 'Adoption request not found'}), 404
    except Exception as e:
        print(f"Error fetching adoption request: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# API Routes - Matching
# ============================================================

@app.route('/api/matches/<request_id>', methods=['GET'])
def get_matches(request_id):
    """Get matching dogs for an adoption request"""
    try:
        matches = get_matching_dogs(request_id)
        return jsonify({
            'request_id': request_id,
            'matches': matches
        }), 200
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/matches/<request_id>/<dog_id>', methods=['GET'])
def get_match_details(request_id, dog_id):
    """Get detailed match info for a specific dog"""
    try:
        # Fetch dog and adoption request
        dog_response = supabase.table('dogs').select('*').eq('id', dog_id).execute()
        request_response = supabase.table('adoption_requests').select('*').eq('id', request_id).execute()

        if not dog_response.data or not request_response.data:
            return jsonify({'error': 'Dog or adoption request not found'}), 404

        dog = dog_response.data[0]
        adoption_request = request_response.data[0]

        # Calculate match
        from furever_match.matching import calculate_match_score, get_match_explanation
        match_result = calculate_match_score(dog, adoption_request)

        return jsonify({
            'dog_id': dog['id'],
            'dog_name': dog['name'],
            'match_score': match_result['score'],
            'match_details': match_result['details'],
            'explanation': get_match_explanation(match_result)
        }), 200
    except Exception as e:
        print(f"Error fetching match details: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# API Routes - Dogs
# ============================================================

@app.route('/api/dogs', methods=['GET'])
def get_dogs():
    """Get all available dogs"""
    try:
        response = supabase.table('dogs').select('*').eq('status', 'available').execute()
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching dogs: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/dogs/<dog_id>', methods=['GET'])
def get_dog(dog_id):
    """Get a specific dog"""
    try:
        response = supabase.table('dogs').select('*').eq('id', dog_id).execute()
        if response.data:
            return jsonify(response.data[0]), 200
        return jsonify({'error': 'Dog not found'}), 404
    except Exception as e:
        print(f"Error fetching dog: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# Health Check
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'FureverMatch API is running'
    }), 200


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Entry point for the application"""
    app_instance = App()
    app_instance.run()


if __name__ == "__main__":
    main()
