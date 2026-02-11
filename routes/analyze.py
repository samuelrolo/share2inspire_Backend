"""
CV Analyze Routes
Handles free CV analysis for CV Analyser v2
"""

import logging
import base64
import io
from flask import Blueprint, request, jsonify
from utils.analysis import CVAnalyzer

logger = logging.getLogger(__name__)

analyze_bp = Blueprint('analyze', __name__)


def transform_to_frontend_format(analysis_data):
    """
    Transform CVAnalyzer output to frontend expected format
    Frontend expects: {atsRejectionRate, quadrants: [{title, score, benchmark, impactPhrase}]}
    """
    # Extract scores from analysis data
    scores = analysis_data.get('scores', {})
    
    # Calculate ATS rejection rate (inverse of ATS compatibility)
    ats_score = scores.get('ats_compatibility', 50)
    ats_rejection_rate = 100 - ats_score
    
    # Build quadrants from dimensional scores
    quadrants = [
        {
            'title': 'Estrutura',
            'score': scores.get('structure', 60),
            'benchmark': 74,
            'impactPhrase': 'A estrutura do CV afeta a primeira impressão'
        },
        {
            'title': 'Conteúdo',
            'score': scores.get('content', 65),
            'benchmark': 71,
            'impactPhrase': 'O conteúdo demonstra valor e competências'
        },
        {
            'title': 'Formação',
            'score': scores.get('education', 70),
            'benchmark': 68,
            'impactPhrase': 'A formação valida a preparação técnica'
        },
        {
            'title': 'Experiência',
            'score': scores.get('experience', 55),
            'benchmark': 69,
            'impactPhrase': 'A experiência comprova a capacidade de execução'
        }
    ]
    
    return {
        'atsRejectionRate': ats_rejection_rate,
        'quadrants': quadrants,
        'fullAnalysis': analysis_data  # Keep full data for paid report
    }


@analyze_bp.route('/free', methods=['POST', 'OPTIONS'])
def analyze_free():
    """
    Free CV analysis endpoint
    Expects: JSON with cv_data: {base64: string, filename: string}
    Returns: Analysis data with quadrants, ATS score, benchmarks, etc.
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200
    
    try:
        data = request.get_json()
        
        if not data or 'cv_data' not in data:
            return jsonify({'error': 'Missing cv_data'}), 400
        
        cv_data = data['cv_data']
        
        if 'base64' not in cv_data or 'filename' not in cv_data:
            return jsonify({'error': 'Missing base64 or filename in cv_data'}), 400
        
        # Decode base64 to file stream
        try:
            file_bytes = base64.b64decode(cv_data['base64'])
            file_stream = io.BytesIO(file_bytes)
        except Exception as e:
            logger.error(f'Base64 decode error: {str(e)}')
            return jsonify({'error': 'Invalid base64 data'}), 400
        
        # Analyze CV
        analyzer = CVAnalyzer()
        analysis_result = analyzer.analyze(file_stream, cv_data['filename'], role="", experience_level="")
        
        if not analysis_result:
            return jsonify({'error': 'Analysis failed'}), 500
        
        # Transform to frontend format
        frontend_data = transform_to_frontend_format(analysis_result)
        
        logger.info(f'Successfully analyzed CV: {cv_data["filename"]}')
        return jsonify(frontend_data), 200
        
    except Exception as e:
        logger.error(f'CV analysis error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@analyze_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for CV analyzer"""
    return jsonify({
        'service': 'cv-analyzer',
        'status': 'healthy'
    }), 200
