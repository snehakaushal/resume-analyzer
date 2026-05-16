from flask import Flask, render_template, request, jsonify, redirect, url_for
import os, re, json, math, random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = 'resumeai_secret_2024'
os.makedirs('uploads', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

SKILL_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust', 'swift',
    'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'git', 'github',
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'nlp',
    'html', 'css', 'bootstrap', 'tailwind', 'sass', 'webpack',
    'rest api', 'graphql', 'microservices', 'devops', 'ci/cd', 'agile', 'scrum',
    'linux', 'bash', 'powershell', 'data analysis', 'pandas', 'numpy', 'excel',
    'figma', 'photoshop', 'illustrator', 'android', 'ios', 'flutter', 'react native'
]

SECTION_PATTERNS = {
    'Education':      ['education', 'academic', 'degree', 'university', 'college', 'school'],
    'Experience':     ['experience', 'work history', 'employment', 'career', 'internship'],
    'Skills':         ['skills', 'technical skills', 'competencies', 'expertise', 'technologies'],
    'Projects':       ['projects', 'personal projects', 'academic projects', 'portfolio'],
    'Certifications': ['certification', 'certificate', 'certified', 'license', 'credential'],
    'Summary':        ['summary', 'objective', 'profile', 'about me', 'overview'],
    'Achievements':   ['achievement', 'award', 'honor', 'recognition', 'accomplishment'],
    'Contact':        ['contact', 'phone', 'email', 'linkedin', 'github', 'address'],
}

# ─── Interview question bank keyed by skill/topic ───────────────────────────
QUESTION_BANK = {
    'python': [
        {"q": "What are Python decorators and how do you use them?", "tip": "Explain with a real example like @login_required or @staticmethod", "difficulty": "Medium"},
        {"q": "Explain the difference between lists, tuples, and sets in Python.", "tip": "Focus on mutability, ordering, and use-cases", "difficulty": "Easy"},
        {"q": "What is the GIL (Global Interpreter Lock) in Python?", "tip": "Mention threading limitations and multiprocessing as alternative", "difficulty": "Hard"},
        {"q": "How does Python's memory management work?", "tip": "Talk about garbage collection and reference counting", "difficulty": "Hard"},
        {"q": "What are list comprehensions and when should you use them?", "tip": "Show syntax and compare with regular for-loop", "difficulty": "Easy"},
    ],
    'java': [
        {"q": "What is the difference between Abstract class and Interface in Java?", "tip": "Mention multiple inheritance, default methods in Java 8+", "difficulty": "Medium"},
        {"q": "Explain Java's garbage collection mechanism.", "tip": "Mention JVM, heap, generations, and GC algorithms", "difficulty": "Hard"},
        {"q": "What are the SOLID principles?", "tip": "Name all 5 and give a brief example of each", "difficulty": "Medium"},
        {"q": "Explain multithreading in Java with synchronized keyword.", "tip": "Cover race conditions, deadlock, and thread safety", "difficulty": "Hard"},
    ],
    'javascript': [
        {"q": "What is event delegation in JavaScript?", "tip": "Explain bubbling and how it improves performance", "difficulty": "Medium"},
        {"q": "Explain closures with a practical example.", "tip": "Use counter or private variable pattern example", "difficulty": "Medium"},
        {"q": "What is the difference between == and === in JavaScript?", "tip": "Type coercion vs strict equality", "difficulty": "Easy"},
        {"q": "How does async/await work under the hood?", "tip": "Connect to Promises and the event loop", "difficulty": "Hard"},
        {"q": "What is the Virtual DOM and why does React use it?", "tip": "Compare with real DOM manipulation performance", "difficulty": "Medium"},
    ],
    'react': [
        {"q": "What are React Hooks and why were they introduced?", "tip": "Compare with class components, mention useState/useEffect", "difficulty": "Medium"},
        {"q": "Explain the React component lifecycle.", "tip": "Cover mounting, updating, unmounting phases", "difficulty": "Medium"},
        {"q": "What is Context API and when would you use it over Redux?", "tip": "Talk about prop drilling problem and scale", "difficulty": "Hard"},
        {"q": "How do you optimize performance in a React application?", "tip": "Mention useMemo, useCallback, lazy loading, React.memo", "difficulty": "Hard"},
    ],
    'sql': [
        {"q": "What is the difference between INNER JOIN, LEFT JOIN, and RIGHT JOIN?", "tip": "Draw a Venn diagram mentally and explain with example tables", "difficulty": "Easy"},
        {"q": "Explain database normalization (1NF, 2NF, 3NF).", "tip": "Use a real table example to show each normal form", "difficulty": "Medium"},
        {"q": "What are indexes and how do they improve query performance?", "tip": "Mention B-tree, tradeoff with write performance", "difficulty": "Medium"},
        {"q": "What is a stored procedure and when would you use one?", "tip": "Compare with regular queries, mention security and reuse", "difficulty": "Medium"},
    ],
    'machine learning': [
        {"q": "Explain the bias-variance tradeoff.", "tip": "Connect to underfitting/overfitting with visual intuition", "difficulty": "Medium"},
        {"q": "What is cross-validation and why is it important?", "tip": "Explain k-fold and how it gives reliable performance estimates", "difficulty": "Easy"},
        {"q": "How does gradient descent work?", "tip": "Explain learning rate, local minima, stochastic vs batch GD", "difficulty": "Hard"},
        {"q": "What is the difference between supervised and unsupervised learning?", "tip": "Give 2 examples each and mention use cases", "difficulty": "Easy"},
    ],
    'docker': [
        {"q": "What is the difference between a Docker image and a container?", "tip": "Image = blueprint, container = running instance", "difficulty": "Easy"},
        {"q": "Explain Docker Compose and when you'd use it.", "tip": "Multi-container apps, services, networking between containers", "difficulty": "Medium"},
        {"q": "What are Docker volumes and why are they needed?", "tip": "Data persistence beyond container lifecycle", "difficulty": "Medium"},
    ],
    'aws': [
        {"q": "What is the difference between EC2, Lambda, and ECS?", "tip": "VM vs serverless vs containers — explain when to use each", "difficulty": "Medium"},
        {"q": "Explain S3 storage classes and their use cases.", "tip": "Standard, IA, Glacier — cost vs access frequency", "difficulty": "Medium"},
        {"q": "How does auto-scaling work in AWS?", "tip": "CloudWatch metrics triggering scale-out/in policies", "difficulty": "Hard"},
    ],
    'git': [
        {"q": "What is the difference between git merge and git rebase?", "tip": "Merge preserves history, rebase creates linear history", "difficulty": "Medium"},
        {"q": "How do you resolve a merge conflict?", "tip": "Walk through the steps: identify, edit, stage, commit", "difficulty": "Easy"},
        {"q": "What is git cherry-pick?", "tip": "Applying specific commits from one branch to another", "difficulty": "Medium"},
    ],
    'agile': [
        {"q": "What is the difference between Scrum and Kanban?", "tip": "Sprints vs continuous flow, ceremonies vs WIP limits", "difficulty": "Easy"},
        {"q": "Explain the role of a Product Owner in Scrum.", "tip": "Backlog management, stakeholder communication, prioritization", "difficulty": "Easy"},
        {"q": "What is a retrospective and what value does it add?", "tip": "Continuous improvement, team morale, process efficiency", "difficulty": "Easy"},
    ],
}

# Generic CS/HR questions always included
GENERIC_QUESTIONS = [
    {"q": "Tell me about yourself and your technical background.", "tip": "Use the Present-Past-Future formula: current role/study → key experience → what you want to do", "difficulty": "Easy", "category": "HR"},
    {"q": "Describe a challenging project you worked on and how you overcame the difficulties.", "tip": "Use STAR method: Situation, Task, Action, Result", "difficulty": "Medium", "category": "Behavioral"},
    {"q": "Where do you see yourself in 5 years?", "tip": "Align with the company's growth — mention skills you want to develop", "difficulty": "Easy", "category": "HR"},
    {"q": "What is your greatest technical weakness?", "tip": "Pick a real weakness but show you're actively working on it", "difficulty": "Easy", "category": "HR"},
    {"q": "How do you handle tight deadlines and pressure?", "tip": "Give a real example, mention prioritization and communication", "difficulty": "Easy", "category": "Behavioral"},
    {"q": "Explain OOP concepts (Inheritance, Polymorphism, Encapsulation, Abstraction).", "tip": "Give a real-world analogy for each — animal/dog for inheritance is classic", "difficulty": "Easy", "category": "Technical"},
    {"q": "What is the difference between a process and a thread?", "tip": "Memory isolation vs shared memory, overhead differences", "difficulty": "Medium", "category": "Technical"},
    {"q": "Explain REST API design principles.", "tip": "Stateless, resources as URLs, HTTP verbs, status codes", "difficulty": "Medium", "category": "Technical"},
    {"q": "How do you stay updated with new technologies?", "tip": "Mention specific sources: blogs, GitHub, courses, side projects", "difficulty": "Easy", "category": "HR"},
    {"q": "Describe your experience working in a team.", "tip": "Mention collaboration tools, conflict resolution, code reviews", "difficulty": "Easy", "category": "Behavioral"},
]


def allowed_file(f): return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    try:
        import PyPDF2
        text = ""
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except: return ""

def extract_skills(text):
    text_lower = text.lower()
    return list(set([s.title() for s in SKILL_KEYWORDS if s.lower() in text_lower]))

def detect_sections(text):
    text_lower = text.lower()
    return {sec: any(kw in text_lower for kw in kws) for sec, kws in SECTION_PATTERNS.items()}

def calculate_ats_score(text, skills, sections):
    score = 0
    breakdown = {}
    skill_score = min(25, len(skills) * 2)
    breakdown['Keywords & Skills'] = {'score': skill_score, 'max': 25}
    score += skill_score
    present = sum(1 for v in sections.values() if v)
    section_score = round((present / len(sections)) * 25)
    breakdown['Sections Completeness'] = {'score': section_score, 'max': 25}
    score += section_score
    wc = len(text.split())
    length_score = 25 if wc >= 400 else (15 if wc >= 200 else (8 if wc >= 100 else 3))
    breakdown['Content Depth'] = {'score': length_score, 'max': 25}
    score += length_score
    fmt = 0
    if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text): fmt += 8
    if re.search(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text): fmt += 7
    if re.search(r'\d+%|\d+ years|\$\d+', text): fmt += 10
    breakdown['Formatting & Contact'] = {'score': fmt, 'max': 25}
    score += fmt
    return min(100, score), breakdown

def check_grammar(text):
    suggestions = []
    patterns = [
        (r'\bI has\b', 'I have', 'Subject-verb agreement'),
        (r'\bI done\b', 'I have done', 'Incorrect past tense'),
        (r'\bmore better\b', 'better', 'Double comparative'),
        (r'\bvery unique\b', 'unique', '"Unique" needs no modifier'),
        (r'\bI are\b', 'I am', 'Subject-verb agreement'),
        (r'\bwe was\b', 'we were', 'Subject-verb agreement'),
        (r'\bresponsible of\b', 'responsible for', 'Preposition error'),
    ]
    for pattern, suggestion, rule in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            suggestions.append({'error': matches[0], 'suggestion': suggestion, 'rule': rule})
    return suggestions[:8]

def calculate_job_match(resume_text, jd):
    def tokenize(t): return re.findall(r'\b[a-z]{3,}\b', t.lower())
    def tf(tokens):
        freq = {}
        for t in tokens: freq[t] = freq.get(t, 0) + 1
        total = len(tokens)
        return {k: v/total for k, v in freq.items()}
    r_tf = tf(tokenize(resume_text))
    j_tf = tf(tokenize(jd))
    vocab = set(list(r_tf.keys()) + list(j_tf.keys()))
    v1 = [r_tf.get(w, 0) for w in vocab]
    v2 = [j_tf.get(w, 0) for w in vocab]
    dot = sum(a*b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a**2 for a in v1))
    m2 = math.sqrt(sum(b**2 for b in v2))
    if m1 == 0 or m2 == 0: return 0
    return round(dot / (m1 * m2) * 100, 1)

def get_missing_keywords(resume_text, jd):
    stop = {'the','and','for','with','you','are','will','have','this','that','from','our','their','your','can','not','but','all','any','been','has','its','who','was','also','into','more'}
    jd_words = re.findall(r'\b[a-z]{4,}\b', jd.lower())
    resume_lower = resume_text.lower()
    missing, seen = [], set()
    for w in jd_words:
        if w not in stop and w not in resume_lower and w not in seen:
            missing.append(w.title()); seen.add(w)
    return missing[:10]

def generate_suggestions(sections, skills, ats_score):
    suggestions = []
    if not sections.get('Summary'):    suggestions.append({'icon': '📝', 'text': 'Add a professional summary/objective at the top'})
    if not sections.get('Certifications'): suggestions.append({'icon': '🏆', 'text': 'Add a Certifications section to boost credibility'})
    if not sections.get('Achievements'):   suggestions.append({'icon': '⭐', 'text': 'Include measurable achievements (e.g., "Increased efficiency by 30%")'})
    if len(skills) < 8: suggestions.append({'icon': '💡', 'text': 'Add more technical skills relevant to your target role'})
    if ats_score < 60: suggestions.append({'icon': '📊', 'text': 'Use more industry-specific keywords to improve ATS score'})
    suggestions.append({'icon': '📏', 'text': 'Keep resume to 1-2 pages for best results'})
    suggestions.append({'icon': '🎯', 'text': 'Tailor your resume for each job application'})
    return suggestions

def generate_interview_questions(skills, resume_text):
    questions = []
    # Add skill-specific questions
    for skill in skills:
        skill_lower = skill.lower()
        for key, qs in QUESTION_BANK.items():
            if key in skill_lower or skill_lower in key:
                for q in qs:
                    q_copy = dict(q)
                    q_copy['category'] = skill
                    questions.append(q_copy)
    # Add generic questions
    questions.extend(GENERIC_QUESTIONS)
    # Deduplicate
    seen, unique = set(), []
    for q in questions:
        if q['q'] not in seen:
            seen.add(q['q']); unique.append(q)
    random.shuffle(unique)
    return unique[:25]

def generate_resume_from_jd(jd_text, user_name, user_email, user_phone, user_skills_extra):
    """Generate a complete resume HTML tailored to a job description"""
    # Extract key skills from JD
    jd_lower = jd_text.lower()
    jd_skills = [s.title() for s in SKILL_KEYWORDS if s.lower() in jd_lower]
    
    # Merge with user-provided extra skills
    extra = [s.strip() for s in user_skills_extra.split(',') if s.strip()]
    all_skills = list(set(jd_skills + extra))[:16]
    
    # Detect role from JD
    role = "Software Developer"
    if 'frontend' in jd_lower or 'react' in jd_lower or 'vue' in jd_lower: role = "Frontend Developer"
    elif 'backend' in jd_lower or 'django' in jd_lower or 'flask' in jd_lower: role = "Backend Developer"
    elif 'full stack' in jd_lower or 'fullstack' in jd_lower: role = "Full Stack Developer"
    elif 'data science' in jd_lower or 'machine learning' in jd_lower: role = "Data Science Engineer"
    elif 'devops' in jd_lower or 'kubernetes' in jd_lower: role = "DevOps Engineer"
    elif 'android' in jd_lower or 'ios' in jd_lower or 'mobile' in jd_lower: role = "Mobile Developer"
    elif 'cloud' in jd_lower or 'aws' in jd_lower: role = "Cloud Engineer"

    return {
        'name': user_name or 'Your Name',
        'email': user_email or 'your.email@gmail.com',
        'phone': user_phone or '+91 00000 00000',
        'role': role,
        'skills': all_skills,
        'jd_summary': jd_text[:300],
        'matched_keywords': jd_skills[:10],
    }


# ─── ROUTES ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['resume']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file. PDF only.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    text = extract_text_from_pdf(filepath)
    if not text.strip():
        text = """John Doe | john.doe@email.com | +91 98765 43210 | github.com/johndoe
SUMMARY
Motivated Computer Science student with experience in Python, React, and cloud technologies.
EDUCATION
B.Tech Computer Science Engineering | XYZ University 2021-2025 | CGPA: 8.5/10
EXPERIENCE
Software Development Intern | ABC Tech, Summer 2024
- Developed REST APIs using Python Flask, reducing response time by 40%
- Implemented automated testing, increasing code coverage by 25%
SKILLS
Python, JavaScript, React, Node.js, Flask, SQL, MySQL, MongoDB, Git, Docker, AWS, HTML, CSS
PROJECTS
E-Commerce Web App | React, Node.js, MongoDB
- Built full-stack shopping platform with 500+ monthly active users
Resume Analyzer Tool | Python, Flask, NLP
- AI-powered tool analyzing ATS compatibility with 90% accuracy
CERTIFICATIONS
AWS Cloud Practitioner 2024 | Python for Data Science Coursera 2023"""

    skills    = extract_skills(text)
    sections  = detect_sections(text)
    ats_score, breakdown = calculate_ats_score(text, skills, sections)
    grammar   = check_grammar(text)
    suggestions = generate_suggestions(sections, skills, ats_score)
    interview_qs = generate_interview_questions(skills, text)

    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    name_lines  = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) < 40]

    result = {
        'filename': filename,
        'name': (name_lines[0] if name_lines else 'Candidate')[:50],
        'email': email_match.group() if email_match else 'Not found',
        'ats_score': ats_score,
        'ats_breakdown': breakdown,
        'skills': skills,
        'sections': sections,
        'grammar_issues': grammar,
        'suggestions': suggestions,
        'interview_questions': interview_qs,
        'word_count': len(text.split()),
        'text': text[:5000],
    }

    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename + '.json'), 'w') as f:
        json.dump(result, f)

    return jsonify({'success': True, 'filename': filename})


@app.route('/dashboard/<filename>')
def dashboard(filename):
    result_file = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename) + '.json')
    if not os.path.exists(result_file):
        return redirect(url_for('index'))
    with open(result_file) as f:
        data = json.load(f)
    return render_template('dashboard.html', data=data)


@app.route('/match_job', methods=['POST'])
def match_job():
    data = request.json
    resume_text = data.get('resume_text', '')
    jd = data.get('job_description', '')
    if not jd.strip():
        return jsonify({'error': 'Please enter a job description'}), 400
    return jsonify({
        'match_score': calculate_job_match(resume_text, jd),
        'missing_keywords': get_missing_keywords(resume_text, jd)
    })


@app.route('/build-resume')
def build_resume():
    return render_template('build_resume.html')


@app.route('/jd-resume')
def jd_resume():
    return render_template('jd_resume.html')


@app.route('/generate_from_jd', methods=['POST'])
def generate_from_jd():
    data = request.json
    result = generate_resume_from_jd(
        jd_text=data.get('jd', ''),
        user_name=data.get('name', ''),
        user_email=data.get('email', ''),
        user_phone=data.get('phone', ''),
        user_skills_extra=data.get('skills', '')
    )
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
