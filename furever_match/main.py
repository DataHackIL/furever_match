"""
Main application module with Flask backend and frontend serving.
Internal data is stored in English; all API responses are translated to
Hebrew (or the language requested via ?lang=he|en, default: he).
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path

from furever_match.db_ingestion import ingest_adoption_request, supabase
from furever_match.graphs import run_match_graph
from furever_match.matching_v2 import calculate_match_score_v2
from furever_match.matching_integration_v2 import get_matching_dogs_v2
from furever_match.matching_v2 import load_matching_config
from furever_match.translations import translate_dog, translate_adoption_request

FRONTEND_PATH = Path(__file__).parent.parent / 'frontend'

app = Flask(__name__, static_folder=str(FRONTEND_PATH), static_url_path='')
CORS(app)


def _lang() -> str:
    """Return the requested language from the query string (default: he)."""
    return request.args.get('lang', 'he').lower()


def _tr_dog(dog: dict) -> dict:
    return translate_dog(dog) if _lang() == 'he' else dog


def _tr_req(req: dict) -> dict:
    return translate_adoption_request(req) if _lang() == 'he' else req


# ============================================================
# Frontend
# ============================================================

@app.route('/')
def index():
    return send_from_directory(str(FRONTEND_PATH), 'welcome.html')


@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(str(FRONTEND_PATH), filename)


# ============================================================
# Adoption Requests
# ============================================================

@app.route('/api/adoption-requests', methods=['POST'])
def create_adoption_request():
    try:
        request_id = ingest_adoption_request(request.json)
        return jsonify({'success': True, 'request_id': request_id}), 201
    except Exception as e:
        print(f"Error creating adoption request: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/adoption-requests', methods=['GET'])
def get_adoption_requests():
    try:
        rows = supabase.table('adoption_requests').select('*').execute().data or []
        return jsonify([_tr_req(r) for r in rows]), 200
    except Exception as e:
        print(f"Error fetching adoption requests: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/adoption-requests/<request_id>', methods=['GET'])
def get_adoption_request(request_id):
    try:
        rows = supabase.table('adoption_requests').select('*').eq('id', request_id).execute().data
        if not rows:
            return jsonify({'error': 'Adoption request not found'}), 404
        return jsonify(_tr_req(rows[0])), 200
    except Exception as e:
        print(f"Error fetching adoption request: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# Dogs
# ============================================================

@app.route('/api/dogs', methods=['GET'])
def get_dogs():
    try:
        rows = supabase.table('dogs').select('*').eq('status', 'available').execute().data or []
        return jsonify([_tr_dog(d) for d in rows]), 200
    except Exception as e:
        print(f"Error fetching dogs: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/dogs/<dog_id>', methods=['GET'])
def get_dog(dog_id):
    try:
        rows = supabase.table('dogs').select('*').eq('id', dog_id).execute().data
        if not rows:
            return jsonify({'error': 'Dog not found'}), 404
        dog = rows[0]
        imgs = supabase.table('dog_images').select('image_url').eq('dog_id', dog_id).execute()
        image_urls = [r['image_url'] for r in (imgs.data or [])]
        dog['image_url'] = image_urls[0] if image_urls else None
        dog['images'] = image_urls
        return jsonify(_tr_dog(dog)), 200
    except Exception as e:
        print(f"Error fetching dog: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# Matching (hypergraph pipeline)
# ============================================================

@app.route('/api/matches/<request_id>', methods=['GET'])
def get_matches(request_id):
    try:
        result = run_match_graph(request_id)
        scored = [_tr_dog(d) for d in (result.get('scored') or [])]
        top3   = [_tr_dog(d) for d in (result.get('top3')   or [])]
        return jsonify({
            'request_id': request_id,
            'matches': scored,
            'top3': top3,
        }), 200
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/matches/<request_id>/<dog_id>', methods=['GET'])
def get_match_details(request_id, dog_id):
    try:
        dog_rows = supabase.table('dogs').select('*').eq('id', dog_id).execute().data
        req_rows = supabase.table('adoption_requests').select('*').eq('id', request_id).execute().data
        if not dog_rows or not req_rows:
            return jsonify({'error': 'Dog or adoption request not found'}), 404

        dog = dog_rows[0]
        match_result = calculate_match_score_v2(dog, req_rows[0], use_llm=False)

        return jsonify({
            'dog_id': dog['id'],
            'dog_name': dog['name'],
            'passes_filters': match_result['passes_filters'],
            'filter_rejection_reason': match_result['filter_rejection_reason'],
            'match_score': match_result['final_score'],
            'soft_scores_breakdown': match_result['soft_scores_breakdown'],
            **_tr_dog({'size': dog.get('size'), 'gender': dog.get('gender'),
                       'level_of_training': dog.get('level_of_training')}),
        }), 200
    except Exception as e:
        print(f"Error fetching match details: {e}")
        return jsonify({'error': str(e)}), 400


# ============================================================
# Enhanced Matching v2
# ============================================================

@app.route('/api/v2/matches/<request_id>', methods=['GET'])
def get_matches_v2(request_id):
    try:
        use_llm      = request.args.get('use_llm', 'true').lower() == 'true'
        cfg_provider = load_matching_config()["llm_analysis"].get("default_provider", "ollama")
        llm_provider = request.args.get('llm_provider', cfg_provider)

        result = get_matching_dogs_v2(request_id, use_llm=use_llm, llm_provider=llm_provider)
        matches = result["matches"]
        warnings = result["filter_warnings"]

        translated = []
        for m in matches:
            m = dict(m)
            dog_display = _tr_dog({
                'size':              m.get('size'),
                'gender':            m.get('gender'),
                'level_of_training': m.get('level_of_training'),
            })
            m.update(dog_display)
            translated.append(m)

        return jsonify({
            'request_id':      request_id,
            'total_matches':   len(translated),
            'matches':         translated,
            'filter_warnings': warnings,
            'system':          'enhanced_v2',
            'use_llm':         use_llm,
        }), 200
    except Exception as e:
        print(f"Error fetching v2 matches: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/api/v2/matches/<request_id>/<dog_id>', methods=['GET'])
def get_match_details_v2(request_id, dog_id):
    try:
        use_llm      = request.args.get('use_llm', 'true').lower() == 'true'
        cfg_provider = load_matching_config()["llm_analysis"].get("default_provider", "ollama")
        llm_provider = request.args.get('llm_provider', cfg_provider)

        dog_rows = supabase.table('dogs').select('*').eq('id', dog_id).execute().data
        req_rows = supabase.table('adoption_requests').select('*').eq('id', request_id).execute().data
        if not dog_rows or not req_rows:
            return jsonify({'error': 'Dog or adoption request not found'}), 404

        dog = dog_rows[0]
        match_result = calculate_match_score_v2(dog, req_rows[0], use_llm=use_llm, llm_provider=llm_provider)

        imgs = supabase.table('dog_images').select('image_url').eq('dog_id', dog_id).execute()
        image_urls = [r['image_url'] for r in (imgs.data or [])]

        translated_dog = _tr_dog(dog)

        return jsonify({
            'dog_id':                  dog['id'],
            'dog_name':                dog['name'],
            'breed':                   dog.get('breed'),
            'age':                     dog.get('age'),
            'size':                    translated_dog.get('size'),
            'gender':                  translated_dog.get('gender'),
            'level_of_training':       translated_dog.get('level_of_training'),
            'image_urls':              image_urls,
            'passes_filters':          match_result['passes_filters'],
            'filter_rejection_reason': match_result['filter_rejection_reason'],
            'soft_score':              match_result['soft_score'],
            'soft_scores_breakdown':   match_result['soft_scores_breakdown'],
            'character_match':         match_result['character_match'],
            'match_score':             match_result['final_score'],
            'match_reasoning':         match_result['final_reasoning'],
        }), 200
    except Exception as e:
        print(f"Error fetching v2 match details: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 400


# ============================================================
# Health Check
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'FureverMatch API is running'}), 200


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


def main():
    app.run(debug=True, port=8000)


if __name__ == "__main__":
    main()
