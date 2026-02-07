"""
LinkedIn Integration Routes
Handles LinkedIn OAuth and profile data import
"""

import logging
import requests
from flask import Blueprint, request, jsonify, make_response
from utils.secrets import get_secret

logger = logging.getLogger(__name__)

linkedin_bp = Blueprint('linkedin', __name__)

# LinkedIn API Configuration (OpenID Connect)
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_USERINFO_URL = 'https://api.linkedin.com/v2/userinfo'


@linkedin_bp.route('/import', methods=['POST', 'OPTIONS'])
def import_linkedin_data():
    """
    Import user data from LinkedIn profile
    Expects: { "code": "authorization_code" }
    Returns: CV data in standardized format
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'Authorization code is required'}), 400
        
        # Get credentials from Secret Manager
        client_id = get_secret('LINKEDIN_CLIENT_ID')
        client_secret = get_secret('LINKEDIN_CLIENT_SECRET_PRIMARY')
        redirect_uri = get_secret('LINKEDIN_REDIRECT_URI') or 'https://cv-builder.share2inspire.pt/auth/linkedin/callback'
        
        if not client_id or not client_secret:
            logger.error('LinkedIn credentials not configured')
            return jsonify({'error': 'LinkedIn integration not configured'}), 500
        
        # Step 1: Exchange code for access token
        token_response = requests.post(
            LINKEDIN_TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        if not token_response.ok:
            logger.error(f'LinkedIn token exchange failed: {token_response.text}')
            return jsonify({'error': 'Failed to authenticate with LinkedIn'}), 401
        
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            return jsonify({'error': 'No access token received'}), 401
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Fetch user info (OpenID Connect)
        userinfo_response = requests.get(LINKEDIN_USERINFO_URL, headers=headers, timeout=30)
        
        if not userinfo_response.ok:
            logger.error(f'LinkedIn userinfo fetch failed: {userinfo_response.text}')
            return jsonify({'error': 'Failed to fetch LinkedIn profile'}), 500
        
        userinfo = userinfo_response.json()
        logger.info(f'LinkedIn userinfo received: {userinfo}')
        
        # Step 3: Transform data to CV format
        cv_data = {
            'personalInfo': {
                'fullName': userinfo.get('name', ''),
                'email': userinfo.get('email', ''),
                'phone': '',
                'location': userinfo.get('locale', {}).get('country', '') if isinstance(userinfo.get('locale'), dict) else '',
                'linkedin': userinfo.get('sub', ''),  # LinkedIn profile ID
                'summary': '',
                'picture': userinfo.get('picture', ''),
            },
            'experience': [],  # OpenID Connect doesn't provide work experience
            'education': [],   # OpenID Connect doesn't provide education
            'skills': [],      # OpenID Connect doesn't provide skills
        }
        
        logger.info(f'Successfully imported LinkedIn data for user: {cv_data["personalInfo"]["fullName"]}')
        return jsonify(cv_data), 200
        
    except requests.exceptions.Timeout:
        logger.error('LinkedIn API request timed out')
        return jsonify({'error': 'Request timed out'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f'LinkedIn API request failed: {str(e)}')
        return jsonify({'error': 'Failed to connect to LinkedIn'}), 503
    except Exception as e:
        logger.error(f'LinkedIn import error: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


def format_linkedin_date(date_obj):
    """
    Format LinkedIn date object to YYYY-MM string
    LinkedIn dates come as: { "year": 2020, "month": 1 }
    """
    if not date_obj:
        return ''
    
    year = date_obj.get('year', '')
    month = date_obj.get('month', '')
    
    if year and month:
        return f"{year}-{str(month).zfill(2)}"
    elif year:
        return str(year)
    
    return ''


@linkedin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for LinkedIn integration"""
    return jsonify({
        'service': 'linkedin-integration',
        'status': 'healthy'
    }), 200
