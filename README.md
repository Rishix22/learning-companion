# learning-companion
PERSONALIZED LEARNING COMPANION
[License: MIT]

An adaptive learning system that uses spaced repetition and Wikipedia integration to personalize study schedules.

FEATURES

Learning Style Adaptation: Visual/Auditory/Kinesthetic content delivery

Spaced Repetition: SM-2 algorithm for optimal review scheduling

Wikipedia Integration: Auto-fetch structured educational content

Progress Tracking: Review history and performance analytics

SETUP INSTRUCTIONS

PREREQUISITES

Python 3.8+

Git

Modern web browser

INSTALLATION

Clone the repository:
git clone https://github.com/your-username/personalized-learning-companion.git
cd personalized-learning-companion

Install dependencies:
pip install -r requirements.txt

Initialize database:
python system.py --init-db

CONFIGURATION
Create .env file with these contents:
FLASK_SECRET_KEY=your_secret_key_here
WIKIPEDIA_API_ENDPOINT=https://en.wikipedia.org/api/rest_v1/page/summary/

RUN THE APPLICATION
python system.py
Access at: http://localhost:5000

GIT REPOSITORY SETUP

Initialize local repository:
git init
git branch -M main

Stage and commit files:
git add .
git commit -m "Initial commit: Personalized Learning Companion"

Connect to remote repository:
git remote add origin https://github.com/your-username/your-repo.git

Push changes:
git push -u origin main

PROJECT STRUCTURE
.
├── system.py # Flask backend
├── requirements.txt # Python dependencies
├── .env # Environment config
├── static/
│ ├── style.css # Styling
│ └── script.js # Frontend logic
├── templates/
│ └── index.html # Main interface
└── learning.db # SQLite database (auto-created)

API ENDPOINTS
Endpoint Method Description
/api/learn POST Fetch learning content
/api/review POST Submit review results
/api/profile POST Update user preferences

TROUBLESHOOTING

Issue: Port 5000 in use
Fix:
python system.py --port 5001

Issue: Missing dependencies
Fix:
pip install --upgrade -r requirements.txt

Issue: CORS errors
Fix: Ensure flask-cors is installed and configured

LICENSE
MIT License - See LICENSE file

ACKNOWLEDGMENTS

Wikipedia API for content

SuperMemo SM-2 algorithm

Flask developer community
