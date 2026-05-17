"""
Main application module with Flask backend and frontend serving
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path

from furever_match.db_ingestion import ingest_adoption_request, supabase
from furever_match.graphs import run_match_graph

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
        result = run_match_graph(request_id)
        return jsonify({
            'request_id': request_id,
            'matches': result.get('scored', []),
            'top3': result.get('top3', []),
            'filter_relaxed': result.get('filter_relaxed', False),
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
        if not response.data:
            return jsonify({'error': 'Dog not found'}), 404
        dog = response.data[0]
        imgs = supabase.table('dog_images').select('image_url').eq('dog_id', dog_id).execute()
        image_urls = [r['image_url'] for r in (imgs.data or [])]
        dog['image_url'] = image_urls[0] if image_urls else None
        dog['images'] = image_urls
        return jsonify(dog), 200
    except Exception as e:
        print(f"Error fetching dog: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# API Routes - Enhanced Matching v2
# ============================================================

@app.route('/api/v2/matches/<request_id>', methods=['GET'])
def get_matches_v2(request_id):
    """
    Get matching dogs using enhanced v2 system
    Query params:
    - use_llm: "true"/"false" (default: true)
    - llm_provider: "gemini"/"ollama" (default: gemini)
    """
    try:
        use_llm = request.args.get('use_llm', 'true').lower() == 'true'
        llm_provider = request.args.get('llm_provider', 'gemini')

        matches = get_matching_dogs_v2(
            request_id,
            use_llm=use_llm,
            llm_provider=llm_provider
        )

        return jsonify({
            'request_id': request_id,
            'total_matches': len(matches),
            'matches': matches,
            'system': 'enhanced_v2',
            'use_llm': use_llm,
        }), 200
    except Exception as e:
        print(f"Error fetching v2 matches: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/api/v2/matches/<request_id>/<dog_id>', methods=['GET'])
def get_match_details_v2(request_id, dog_id):
    """
    Get detailed match info using enhanced v2 system
    Query params:
    - use_llm: "true"/"false" (default: true)
    - llm_provider: "gemini"/"ollama" (default: gemini)
    """
    try:
        use_llm = request.args.get('use_llm', 'true').lower() == 'true'
        llm_provider = request.args.get('llm_provider', 'gemini')

        dog_response = supabase.table('dogs').select('*').eq('id', dog_id).execute()
        request_response = supabase.table('adoption_requests').select('*').eq('id', request_id).execute()

        if not dog_response.data or not request_response.data:
            return jsonify({'error': 'Dog or adoption request not found'}), 404

        dog = dog_response.data[0]
        adoption_request = request_response.data[0]

        match_result = calculate_match_score_v2(
            dog,
            adoption_request,
            use_llm=use_llm,
            llm_provider=llm_provider
        )

        imgs = supabase.table('dog_images').select('image_url').eq('dog_id', dog_id).execute()
        image_urls = [r['image_url'] for r in (imgs.data or [])]

        return jsonify({
            'dog_id': dog['id'],
            'dog_name': dog['name'],
            'breed': dog.get('breed'),
            'age': dog.get('age'),
            'size': dog.get('size'),
            'gender': dog.get('gender'),
            'image_urls': image_urls,
            'passes_filters': match_result['passes_filters'],
            'filter_rejection_reason': match_result['filter_rejection_reason'],
            'soft_score': match_result['soft_score'],
            'soft_scores_breakdown': match_result['soft_scores_breakdown'],
            'character_match': match_result['character_match'],
            'match_score': match_result['final_score'],
            'match_reasoning': match_result['final_reasoning'],
        }), 200
    except Exception as e:
        print(f"Error fetching v2 match details: {e}")
        import traceback
        traceback.print_exc()
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
