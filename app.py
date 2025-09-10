# app.py - Updated with OpenAI API integration
from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

app.config['SECRET_KEY'] = "farmer-advisory-secret-key-2024"
app.config['DATABASE'] = 'farmers.db'

# Manual CORS handling
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response

# Initialize OpenAI
openai_available = False
client = None

try:
    from openai import OpenAI
    
    # Get API key from environment variable
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if openai_api_key:
        client = OpenAI(api_key=openai_api_key)
        openai_available = True
        logger.info("✅ OpenAI client initialized successfully")
        logger.info(f"✅ API Key found: {openai_api_key[:8]}...{openai_api_key[-4:]}")
    else:
        logger.warning("⚠️ OPENAI_API_KEY environment variable not found")
        logger.warning("⚠️ Running in demo mode")
        
except ImportError:
    logger.error("❌ OpenAI library not installed. Run: pip install openai")
except Exception as e:
    logger.error(f"❌ OpenAI initialization error: {e}")

# =====================================================
# Database Functions
# =====================================================
def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                category TEXT,
                language TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_openai BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

# =====================================================
# Category Detection
# =====================================================
def detect_query_category(query):
    """Detect query category with enhanced keywords"""
    query_lower = query.lower()
    
    # Crop/Farming keywords
    if any(word in query_lower for word in [
        'crop', 'crops', 'farming', 'farm', 'cultivation', 'grow', 'growing', 'plant', 'planting',
        'vegetable', 'vegetables', 'rice', 'wheat', 'tomato', 'potato', 'onion', 'cabbage',
        'കൃഷി', 'വിള', 'വിളകൾ', 'നട്ട്', 'വളർത്തുക'
    ]):
        return 'crop'
    
    # Pest/Disease keywords
    elif any(word in query_lower for word in [
        'pest', 'bug', 'disease', 'spots', 'yellow', 'brown', 'fungus', 'insect', 'infection',
        'കീട', 'രോഗം', 'പുഴു', 'പൊട്ട്', 'മഞ്ഞ', 'തവിട്ട്'
    ]):
        return 'pest'
    
    # Weather keywords  
    elif any(word in query_lower for word in [
        'weather', 'rain', 'drought', 'temperature', 'humidity', 'wind', 'season',
        'കാലാവസ്ഥ', 'മഴ', 'വരൾച്ച', 'താപനില'
    ]):
        return 'weather'
    
    # Fertilizer keywords
    elif any(word in query_lower for word in [
        'fertilizer', 'fertiliser', 'nutrient', 'npk', 'urea', 'compost', 'manure',
        'വള', 'പോഷകം', 'യൂറിയ'
    ]):
        return 'fertilizer'
    
    # Market keywords
    elif any(word in query_lower for word in [
        'price', 'market', 'sell', 'selling', 'rate', 'cost', 'profit',
        'വില', 'വിപണി', 'വിൽക്കുക', 'ലാഭം'
    ]):
        return 'market'
    
    # Government schemes
    elif any(word in query_lower for word in [
        'subsidy', 'scheme', 'government', 'loan', 'pm kisan', 'credit',
        'സബ്സിഡി', 'പദ്ധതി', 'സർക്കാർ', 'ലോൺ'
    ]):
        return 'subsidy'
    
    else:
        return 'general'

# =====================================================
# OpenAI Response Function
# =====================================================
def get_openai_response(query, category, language):
    """Get response from OpenAI API"""
    
    if not openai_available or not client:
        logger.warning("OpenAI not available, falling back to demo")
        return get_demo_response(query, category, language)
    
    try:
        # Language-specific instructions
        language_instructions = {
            'en': "Respond in clear, simple English that Indian farmers can understand.",
            'ml': "മലയാളത്തിൽ ഉത്തരം നൽകുക. കേരളത്തിലെ കർഷകർക്ക് മനസ്സിലാകുന്ന ലളിതമായ ഭാഷ ഉപയോഗിക്കുക.",
            'hi': "हिंदी में उत्तर दें। भारतीय किसानों को समझ आने वाली सरल भाषा का उपयोग करें।",
            'ta': "தமிழில் பதிலளிக்கவும். இந்திய விவசாயிகளுக்கு புரியும் எளிய மொழியைப் பயன்படுத்தவும்.",
            'te': "తెలుగులో సమాధానం ఇవ్వండి। భారతీయ రైతులకు అర్థమయ్యే సరళమైన భాషను ఉపయోగించండి।"
        }
        
        lang_instruction = language_instructions.get(language, language_instructions['en'])
        
        # Create system prompt based on category
        system_prompts = {
            'crop': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
Category: Crop cultivation and farming practices
{lang_instruction}

Provide practical, actionable advice for:
- Suitable crops for Indian climate
- Planting techniques and timing
- Care and maintenance
- Harvesting tips

Keep response under 200 words. Focus on solutions available in India.""",

            'pest': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
Category: Pest and disease management
{lang_instruction}

Provide practical solutions for:
- Pest identification
- Organic and chemical control methods
- Prevention strategies
- When to seek professional help

Include specific product names and dosages available in India. Keep under 200 words.""",

            'weather': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
Category: Weather and climate management
{lang_instruction}

Provide advice on:
- Weather preparation for crops
- Seasonal farming practices
- Climate-smart agriculture
- Weather monitoring tools

Focus on Indian climate conditions. Keep under 200 words.""",

            'fertilizer': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
Category: Fertilizer and soil management
{lang_instruction}

Provide guidance on:
- Soil testing and analysis
- Fertilizer recommendations
- Organic alternatives
- Application methods and timing

Include products available in Indian markets. Keep under 200 words.""",

            'market': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
Category: Market prices and selling
{lang_instruction}

Provide information about:
- Market price sources (e-NAM, local mandis)
- Better selling strategies
- Value addition techniques
- Market timing

Focus on Indian agricultural markets. Keep under 200 words.""",

            'subsidy': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
Category: Government schemes and subsidies
{lang_instruction}

Provide information about:
- Available government schemes (PM-KISAN, etc.)
- Eligibility criteria
- Application process
- Required documents

Focus on current Indian government schemes. Keep under 200 words.""",

            'general': f"""You are KisanMitra, an expert agricultural advisor for Indian farmers.
            
{lang_instruction}

Provide helpful agricultural guidance relevant to Indian farming conditions.
If the question is unclear, ask for clarification.
Always end with contact information for local agricultural offices.

Keep under 200 words."""
        }
        
        system_prompt = system_prompts.get(category, system_prompts['general'])
        
        logger.info(f"🤖 Calling OpenAI API for category: {category}, language: {language}")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=400,
            temperature=0.7,
            top_p=1.0
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"✅ OpenAI response received: {len(ai_response)} characters")
        
        return ai_response
        
    except Exception as e:
        logger.error(f"❌ OpenAI API error: {e}")
        logger.error(traceback.format_exc())
        return get_demo_response(query, category, language)

# =====================================================
# Demo Response (Fallback)
# =====================================================
def get_demo_response(query, category, language):
    """Fallback demo responses"""
    responses = {
        'en': {
            'crop': '🌱 For vegetable farming: 1) Test soil pH, 2) Use quality seeds, 3) Apply balanced NPK fertilizer, 4) Ensure proper drainage. Contact KVK for detailed guidance.',
            'pest': '🐛 For pest control: Use neem oil (5ml/L water) spray in early morning. For severe cases, consult agricultural extension officer.',
            'weather': '🌤️ Use IMD weather apps for forecasts. Ensure proper drainage during monsoon. Plan planting according to seasonal calendar.',
            'fertilizer': '🌱 Get soil tested first. Apply NPK 16:16:16 as base dose. Add organic compost for better soil health.',
            'market': '💰 Check prices on e-NAM portal. Visit local mandis. Join FPO for better rates.',
            'subsidy': '🏛️ Apply for PM-KISAN scheme. Visit bank with Aadhaar and land documents.',
            'general': '💬 Contact Krishi Vigyan Kendra for agricultural guidance. Kisan Call Center: 1800-180-1551.'
        },
        'ml': {
            'crop': '🌱 പച്ചക്കറി കൃഷിക്ക്: 1) മണ്ണ് പരിശോധന, 2) നല്ല വിത്ത്, 3) സമതുലിത വള, 4) നല്ല നീർവാത്. കൃഷി വിജ്ഞാന കേന്ദ്രത്തിൽ നിന്ന് വിശദമായ വിവരങ്ങൾ.',
            'pest': '🐛 കീടനിയന്ത്രണത്തിന്: നീം എണ്ണ (5ml/ലിറ്റർ) രാവിലെ തളിക്കുക. ഗുരുതരമായ കേസുകളിൽ കൃഷി ഓഫീസറെ സമീപിക്കുക.',
            'weather': '🌤️ കാലാവസ്ഥയ്ക്ക് IMD ആപ്പ് ഉപയോഗിക്കുക. മഴക്കാലത്ത് നീർവാത്ത് ഉറപ്പാക്കുക.',
            'fertilizer': '🌱 മണ്ണ് പരിശോധനയ്ക്ക് ശേഷം NPK 16:16:16 വള ഇടുക. ജൈവവള കൂടി ചേർക്കുക.',
            'market': '💰 e-NAM പോർട്ടലിൽ വില നോക്കുക. പ്രാദേശിക മാർക്കറ്റിൽ അന്വേഷിക്കുക.',
            'subsidy': '🏛️ PM-KISAN പദ്ധതിക്ക് അപേക്ഷിക്കുക. ആധാർ, ഭൂമി രേഖകളുമായി ബാങ്കിൽ പോകുക.',
            'general': '💬 കൃഷി സംശയങ്ങൾക്ക് കൃഷി വിജ്ഞാന കേന്ദ്രത്തെ സമീപിക്കുക. കിസാൻ കോൾ സെന്റർ: 1800-180-1551.'
        }
    }
    
    lang_resp = responses.get(language, responses['en'])
    return lang_resp.get(category, lang_resp['general'])

# =====================================================
# Routes
# =====================================================
@app.route('/')
def index():
    """Serve main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"""
        <h1>🌾 KisanMitra - AI Krishi Officer</h1>
        <p>OpenAI Status: {'✅ Connected' if openai_available else '❌ Demo Mode'}</p>
        <p>API endpoint: /api/query</p>
        """, 200

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process farmer queries with OpenAI"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False, 
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'error': 'No JSON data provided'
            }), 400
        
        user_query = data.get('query', '').strip()
        language = data.get('language', 'en')
        
        if not user_query:
            return jsonify({
                'success': False, 
                'error': 'Query cannot be empty'
            }), 400
        
        logger.info(f"📥 Processing query: '{user_query[:50]}...' (Language: {language})")
        
        # Detect category
        category = detect_query_category(user_query)
        logger.info(f"📊 Detected category: {category}")
        
        # Get AI response
        ai_response = get_openai_response(user_query, category, language)
        
        # Save to database
        try:
            conn = sqlite3.connect(app.config['DATABASE'])
            c = conn.cursor()
            c.execute('''
                INSERT INTO queries (user_query, ai_response, category, language, is_openai)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_query, ai_response, category, language, openai_available))
            conn.commit()
            conn.close()
            logger.info(f"💾 Query saved to database")
        except Exception as db_error:
            logger.error(f"DB save error: {db_error}")
        
        # Return response
        return jsonify({
            'success': True,
            'response': ai_response,
            'category': category,
            'language': language,
            'is_demo': not openai_available,
            'source': 'openai' if openai_available else 'demo'
        })
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred'
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get application statistics"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM queries')
        total = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM queries WHERE is_openai = 1')
        openai_queries = c.fetchone()[0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('SELECT COUNT(*) FROM queries WHERE DATE(timestamp) = ?', (today,))
        today_count = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_queries': total,
            'openai_queries': openai_queries,
            'demo_queries': total - openai_queries,
            'today_queries': today_count,
            'api_status': 'openai' if openai_available else 'demo'
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'openai_available': openai_available,
        'api_key_configured': bool(os.getenv("OPENAI_API_KEY")),
        'timestamp': datetime.now().isoformat()
    })

# =====================================================
# Main
# =====================================================
if __name__ == '__main__':
    print("🌾 KisanMitra - AI Krishi Officer")
    print("=" * 50)
    
    # Check OpenAI setup
    if openai_available:
        print("✅ OpenAI API: Connected")
        print("🤖 Mode: Real AI responses")
    else:
        print("⚠️ OpenAI API: Not configured")
        print("🤖 Mode: Demo responses")
        print("💡 To enable OpenAI: Set OPENAI_API_KEY environment variable")
    
    # Check file structure
    if os.path.exists('templates'):
        print("✅ Templates folder: Found")
    else:
        print("⚠️ Templates folder: Missing")
    
    if os.path.exists('static'):
        print("✅ Static folder: Found")
    else:
        print("⚠️ Static folder: Missing") 
    
    # Initialize database
    if init_db():
        print("✅ Database: Ready")
    
    print(f"\n🚀 Server starting on http://127.0.0.1:5000")
    print("=" * 50)
    
    app.run(debug=True, host='127.0.0.1', port=5000)