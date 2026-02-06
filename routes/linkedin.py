"""
LinkedIn Integration Routes
Handles LinkedIn OAuth and profile data import
"""

import logging
import requests
from flask import Blueprint, request, jsonify
from utils.secrets import get_secret

logger = logging.getLogger(__name__)

linkedin_bp = Blueprint('linkedin', __name__)

# LinkedIn API Configuration
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_PROFILE_URL = 'https://api.linkedin.com/v2/me'
LINKEDIN_EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'
LINKEDIN_POSITIONS_URL = 'https://api.linkedin.com/v2/positions?q=members&projection=(elements*(company,title,timePeriod,description))'
LINKEDIN_EDUCATION_URL = 'https://api.linkedin.com/v2/educations?q=members&projection=(elements*(schoolName,degreeName,fieldOfStudy,timePeriod))'
LINKEDIN_SKILLS_URL = 'https://api.linkedin.com/v2/skills?q=members&projection=(elements*(name))'


@linkedin_bp.route('/import', methods=['POST'])
def import_linkedin_data():
    """
    Import user data from LinkedIn profile
    Expects: { "code": "authorization_code" }
    Returns: CV data in standardized format
    """
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
        
        # Step 2: Fetch profile data
        profile_response = requests.get(LINKEDIN_PROFILE_URL, headers=headers, timeout=30)
        email_response = requests.get(LINKEDIN_EMAIL_URL, headers=headers, timeout=30)
        
        if not profile_response.ok:
            logger.error(f'LinkedIn profile fetch failed: {profile_response.text}')
            return jsonify({'error': 'Failed to fetch LinkedIn profile'}), 500
        
        profile = profile_response.json()
        email_data = email_response.json() if email_response.ok else {}
        email = email_data.get('elements', [{}])[0].get('handle~', {}).get('emailAddress', '')
        
        # Step 3: Fetch additional data (optional, may fail due to permissions)
        positions_response = requests.get(LINKEDIN_POSITIONS_URL, headers=headers, timeout=30)
        education_response = requests.get(LINKEDIN_EDUCATION_URL, headers=headers, timeout=30)
        skills_response = requests.get(LINKEDIN_SKILLS_URL, headers=headers, timeout=30)
        
        positions = positions_response.json().get('elements', []) if positions_response.ok else []
        education = education_response.json().get('elements', []) if education_response.ok else []
        skills = skills_response.json().get('elements', []) if skills_response.ok else []
        
        # Step 4: Transform data to CV format
        cv_data = {
            'personalInfo': {
                'fullName': f"{profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}".strip(),
                'email': email,
                'phone': '',
                'location': '',
                'linkedin': f"https://www.linkedin.com/in/{profile.get('vanityName', '')}",
                'summary': profile.get('headline', ''),
            },
            'experience': [
                {
                    'company': pos.get('company', {}).get('name', ''),
                    'position': pos.get('title', ''),
                    'startDate': format_linkedin_date(pos.get('timePeriod', {}).get('startDate')),
                    'endDate': format_linkedin_date(pos.get('timePeriod', {}).get('endDate')),
                    'current': not pos.get('timePeriod', {}).get('endDate'),
                    'description': pos.get('description', ''),
                }
                for pos in positions
            ],
            'education': [
                {
                    'institution': edu.get('schoolName', ''),
                    'degree': edu.get('degreeName', ''),
                    'field': edu.get('fieldOfStudy', ''),
                    'startDate': format_linkedin_date(edu.get('timePeriod', {}).get('startDate')),
                    'endDate': format_linkedin_date(edu.get('timePeriod', {}).get('endDate')),
                    'current': not edu.get('timePeriod', {}).get('endDate'),
                }
                for edu in education
            ],
            'skills': [
                {
                    'name': skill.get('name', ''),
                    'level': 3,  # Default to intermediate level
                }
                for skill in skills
            ],
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
