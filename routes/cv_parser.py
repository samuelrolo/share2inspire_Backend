"""
CV Parser Routes
Handles CV upload and parsing for CV Builder
"""

import logging
from flask import Blueprint, request, jsonify
from utils.analysis import CVAnalyzer

logger = logging.getLogger(__name__)

cv_parser_bp = Blueprint('cv_parser', __name__)


@cv_parser_bp.route('/parse', methods=['POST', 'OPTIONS'])
def parse_cv():
    """
    Parse CV file and extract structured data for CV Builder
    Expects: multipart/form-data with 'file' field
    Returns: Structured CV data (personal info, experience, education, skills, etc.)
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }), 400
        
        # Parse CV using CVAnalyzer
        analyzer = CVAnalyzer()
        cv_data, status_code = analyzer.parse_for_cv_builder(file.stream, file.filename)
        
        if status_code != 200:
            return jsonify(cv_data), status_code
        
        logger.info(f'Successfully parsed CV: {file.filename}')
        return jsonify(cv_data), 200
        
    except Exception as e:
        logger.error(f'CV parsing error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@cv_parser_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for CV parser"""
    return jsonify({
        'service': 'cv-parser',
        'status': 'healthy'
    }), 200
