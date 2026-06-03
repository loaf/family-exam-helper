"""
家庭考试助手 - Family Exam Helper
单机运行的考试/练习系统，支持富文本题目、数学公式、代码高亮
"""
import os
import re
import sqlite3
import uuid
import json
import time
from datetime import datetime
from functools import wraps

from flask import (Flask, g, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_from_directory,
                   send_file, make_response)
from werkzeug.utils import secure_filename
import openpyxl

app = Flask(__name__)
app.secret_key = 'family-exam-helper-2026-sisyphus'

# ── Directories ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANKS_DIR = os.path.join(BASE_DIR, 'banks')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
IMPORTS_DIR = os.path.join(BASE_DIR, 'imports')

for d in [BANKS_DIR, UPLOADS_DIR, IMPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Allowed extensions ───────────────────────────────────────────────
ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'}
MAX_IMG_SIZE = 16 * 1024 * 1024  # 16 MB


# ══════════════════════════════════════════════════════════════════════
#  Database helpers
# ══════════════════════════════════════════════════════════════════════

def _bank_path(filename):
    """Resolve bank path with traversal protection."""
    path = os.path.realpath(os.path.join(BANKS_DIR, filename))
    if not path.startswith(os.path.realpath(BANKS_DIR)):
        return None
    return path


def init_bank_db(db_path, display_name=''):
    """Create tables for a new question bank."""
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bank_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER DEFAULT NULL,
            tag TEXT DEFAULT '',
            type TEXT NOT NULL CHECK(type IN ('single_choice','multi_choice','true_false','fill_blank')),
            difficulty INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 3),
            content TEXT NOT NULL DEFAULT '',
            options TEXT DEFAULT '[]',
            answer TEXT NOT NULL DEFAULT '',
            explanation TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS exam_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL,
            subject_id INTEGER DEFAULT NULL,
            tag TEXT DEFAULT '',
            total_questions INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            score REAL DEFAULT 0,
            total_score REAL DEFAULT 0,
            duration_seconds INTEGER DEFAULT 0,
            answers TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject_id);
        CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(type);
        CREATE INDEX IF NOT EXISTS idx_questions_tag ON questions(tag);
    """)
    if display_name:
        conn.execute("INSERT INTO bank_meta (key, value) VALUES ('display_name', ?)", (display_name,))
    conn.commit()
    conn.close()


def get_bank_list():
    """List all .db banks with display name and question count."""
    banks = []
    for f in sorted(os.listdir(BANKS_DIR)):
        if not f.endswith('.db'):
            continue
        db_path = os.path.join(BANKS_DIR, f)
        name = f[:-3]  # fallback
        count = 0
        try:
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT value FROM bank_meta WHERE key='display_name'").fetchone()
            if row and row[0]:
                name = row[0]
            row = conn.execute('SELECT COUNT(*) FROM questions').fetchone()
            count = row[0] if row else 0
            conn.close()
        except Exception:
            pass
        banks.append({'filename': f, 'name': name, 'count': count})
    return banks


def get_db():
    """Return a per-request sqlite3 connection for the current bank."""
    if 'db' not in g:
        db_name = session.get('current_bank')
        if not db_name:
            return None
        db_path = _bank_path(db_name)
        if not db_path or not os.path.exists(db_path):
            return None
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def require_bank(f):
    """Decorator: redirect to home if no bank selected."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('current_bank') or get_db() is None:
            flash('请先选择题库', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper


# ══════════════════════════════════════════════════════════════════════
#  Image upload (TinyMCE)
# ══════════════════════════════════════════════════════════════════════

def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXT


@app.route('/upload_image', methods=['POST'])
@require_bank
def upload_image():
    """TinyMCE image upload endpoint. Returns {location: url}."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f = request.files['file']
    if f.filename == '' or not _allowed_image(f.filename):
        return jsonify({'error': 'Invalid file'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOADS_DIR, fname))
    return jsonify({'location': url_for('uploaded_file', filename=fname)})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOADS_DIR, filename)


# ══════════════════════════════════════════════════════════════════════
#  Routes – Bank management
# ══════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    banks = get_bank_list()
    current = session.get('current_bank')
    return render_template('index.html', banks=banks, current_bank=current)


@app.route('/bank/create', methods=['POST'])
def create_bank():
    name = request.form.get('name', '').strip()
    if not name:
        flash('请输入题库名称', 'error')
        return redirect(url_for('index'))
    # Use UUID for filename (avoids encoding issues with Chinese)
    filename = f"{uuid.uuid4().hex}.db"
    while os.path.exists(os.path.join(BANKS_DIR, filename)):
        filename = f"{uuid.uuid4().hex}.db"
    init_bank_db(os.path.join(BANKS_DIR, filename), display_name=name)
    session['current_bank'] = filename
    flash(f'题库「{name}」创建成功', 'success')
    return redirect(url_for('bank_home'))


@app.route('/bank/select/<filename>')
def select_bank(filename):
    if not filename.endswith('.db'):
        flash('无效的题库', 'error')
        return redirect(url_for('index'))
    path = _bank_path(filename)
    if not path or not os.path.exists(path):
        flash('题库不存在', 'error')
        return redirect(url_for('index'))
    session['current_bank'] = filename
    return redirect(url_for('bank_home'))


@app.route('/bank/delete/<filename>', methods=['POST'])
def delete_bank(filename):
    path = _bank_path(filename)
    if not path or not os.path.exists(path):
        flash('题库不存在', 'error')
        return redirect(url_for('index'))

    # Close current connection if it's to this bank
    if session.get('current_bank') == filename:
        db = g.pop('db', None)
        if db is not None:
            db.close()
        session.pop('current_bank', None)

    # Checkpoint WAL and close any lingering connections
    try:
        conn = sqlite3.connect(path)
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        conn.close()
    except Exception:
        pass

    # Remove the .db file and any WAL/SHM sidecar files
    base = path[:-3] if path.endswith('.db') else path
    for suffix in ['', '-shm', '-wal']:
        f = base + suffix
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    flash('题库已删除', 'success')
    return redirect(url_for('index'))


@app.route('/bank/back')
def back_to_banks():
    session.pop('current_bank', None)
    return redirect(url_for('index'))


# ══════════════════════════════════════════════════════════════════════
#  Routes – Bank home (select mode)
# ══════════════════════════════════════════════════════════════════════

@app.route('/bank/home')
@require_bank
def bank_home():
    db = get_db()
    subjects = db.execute('SELECT * FROM subjects ORDER BY name').fetchall()
    tags_rows = db.execute(
        "SELECT DISTINCT tag FROM questions WHERE tag != '' ORDER BY tag"
    ).fetchall()
    tags = [r['tag'] for r in tags_rows]
    total = db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]

    # Stats per type
    type_stats = {}
    for t in ['single_choice', 'multi_choice', 'true_false', 'fill_blank']:
        row = db.execute('SELECT COUNT(*) FROM questions WHERE type=?', (t,)).fetchone()
        type_stats[t] = row[0]

    bank_display = ''
    try:
        row = db.execute("SELECT value FROM bank_meta WHERE key='display_name'").fetchone()
        if row and row[0]:
            bank_display = row[0]
    except Exception:
        bank_display = session.get('current_bank', '')[:-3]
    return render_template('bank_home.html',
                           subjects=subjects, tags=tags, total=total,
                           type_stats=type_stats, bank_display=bank_display)


# ══════════════════════════════════════════════════════════════════════
#  Routes – Subject management
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/subjects/add', methods=['POST'])
@require_bank
def api_add_subject():
    """AJAX endpoint to add a subject. Returns JSON."""
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'error': '请输入科目名称'}), 400
    db = get_db()
    try:
        cursor = db.execute('INSERT INTO subjects (name) VALUES (?)', (name,))
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'name': name})
    except sqlite3.IntegrityError:
        return jsonify({'error': '科目已存在'}), 409


@app.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@require_bank
def delete_subject(subject_id):
    db = get_db()
    db.execute('DELETE FROM subjects WHERE id=?', (subject_id,))
    db.commit()
    return redirect(url_for('bank_home'))


# ══════════════════════════════════════════════════════════════════════
#  Routes – Question CRUD
# ══════════════════════════════════════════════════════════════════════

@app.route('/questions')
@require_bank
def list_questions():
    db = get_db()
    sf = request.args.get('subject', '')
    tf = request.args.get('tag', '')
    typef = request.args.get('type', '')

    q = ("SELECT q.*, s.name AS subject_name "
         "FROM questions q LEFT JOIN subjects s ON q.subject_id=s.id WHERE 1=1")
    params = []
    if sf:
        q += " AND q.subject_id=?"
        params.append(sf)
    if tf:
        q += " AND q.tag=?"
        params.append(tf)
    if typef:
        q += " AND q.type=?"
        params.append(typef)
    q += " ORDER BY q.id DESC"

    questions = db.execute(q, params).fetchall()
    subjects = db.execute('SELECT * FROM subjects ORDER BY name').fetchall()
    tags_rows = db.execute(
        "SELECT DISTINCT tag FROM questions WHERE tag != '' ORDER BY tag"
    ).fetchall()
    tags = [r['tag'] for r in tags_rows]
    return render_template('questions.html',
                           questions=questions, subjects=subjects, tags=tags,
                           sf=sf, tf=tf, typef=typef)


@app.route('/questions/add', methods=['GET', 'POST'])
@require_bank
def add_question():
    db = get_db()
    if request.method == 'POST':
        data = _parse_question_form(request.form)
        db.execute(
            "INSERT INTO questions (subject_id,tag,type,difficulty,content,options,answer,explanation) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (data['subject_id'], data['tag'], data['type'], data['difficulty'],
             data['content'], data['options'], data['answer'], data['explanation'])
        )
        db.commit()
        flash('题目已添加', 'success')
        return redirect(url_for('list_questions'))

    subjects = db.execute('SELECT * FROM subjects ORDER BY name').fetchall()
    return render_template('question_form.html', subjects=subjects, question=None)


@app.route('/questions/edit/<int:qid>', methods=['GET', 'POST'])
@require_bank
def edit_question(qid):
    db = get_db()
    if request.method == 'POST':
        data = _parse_question_form(request.form)
        db.execute(
            "UPDATE questions SET subject_id=?,tag=?,type=?,difficulty=?,"
            "content=?,options=?,answer=?,explanation=? WHERE id=?",
            (data['subject_id'], data['tag'], data['type'], data['difficulty'],
             data['content'], data['options'], data['answer'], data['explanation'], qid)
        )
        db.commit()
        flash('题目已更新', 'success')
        return redirect(url_for('list_questions'))

    question = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
    if not question:
        flash('题目不存在', 'error')
        return redirect(url_for('list_questions'))
    subjects = db.execute('SELECT * FROM subjects ORDER BY name').fetchall()
    return render_template('question_form.html', subjects=subjects, question=question)


@app.route('/questions/delete/<int:qid>', methods=['POST'])
@require_bank
def delete_question(qid):
    db = get_db()
    db.execute('DELETE FROM questions WHERE id=?', (qid,))
    db.commit()
    flash('题目已删除', 'success')
    return redirect(url_for('list_questions'))


@app.route('/questions/view/<int:qid>')
@require_bank
def view_question(qid):
    db = get_db()
    q = db.execute(
        "SELECT q.*, s.name AS subject_name "
        "FROM questions q LEFT JOIN subjects s ON q.subject_id=s.id WHERE q.id=?",
        (qid,)
    ).fetchone()
    if not q:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': q['id'],
        'type': q['type'],
        'content': q['content'],
        'options': json.loads(q['options']),
        'answer': q['answer'],
        'explanation': q['explanation'],
        'subject_name': q['subject_name'],
        'tag': q['tag'],
        'difficulty': q['difficulty'],
    })


def _parse_question_form(form):
    """Extract question fields from form data."""
    subject_id = form.get('subject_id') or None
    if subject_id:
        subject_id = int(subject_id)
    tag = form.get('tag', '').strip()
    qtype = form.get('type', 'single_choice')
    difficulty = int(form.get('difficulty', 1))
    content = form.get('content', '')
    explanation = form.get('explanation', '')

    # Build options JSON
    options = []
    if qtype in ('single_choice', 'multi_choice'):
        for key in sorted(form):
            if key.startswith('option_'):
                val = form.get(key, '').strip()
                if val:
                    label = key.replace('option_', '').upper()
                    options.append({'label': label, 'content': val})
    elif qtype == 'true_false':
        options = [
            {'label': 'A', 'content': '正确'},
            {'label': 'B', 'content': '错误'},
        ]

    answer = form.get('answer', '').strip()
    # For fill_blank, support multiple answers separated by |
    if qtype == 'fill_blank':
        answer = '|'.join(a.strip() for a in answer.split('|') if a.strip())

    return {
        'subject_id': subject_id,
        'tag': tag,
        'type': qtype,
        'difficulty': difficulty,
        'content': content,
        'options': json.dumps(options, ensure_ascii=False),
        'answer': answer,
        'explanation': explanation,
    }


# ══════════════════════════════════════════════════════════════════════
#  Routes – Excel import
# ══════════════════════════════════════════════════════════════════════

@app.route('/import', methods=['GET', 'POST'])
@require_bank
def import_questions():
    db = get_db()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('请选择文件', 'error')
            return redirect(url_for('import_questions'))
        f = request.files['file']
        if not f.filename.endswith(('.xlsx', '.xls')):
            flash('请上传 Excel 文件（.xlsx）', 'error')
            return redirect(url_for('import_questions'))

        # Auto-create subjects if needed
        existing = {r['name']: r['id'] for r in db.execute('SELECT * FROM subjects').fetchall()}

        try:
            wb = openpyxl.load_workbook(f)
            ws = wb.active
            count = 0
            errors = []

            for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    if not row or len(row) < 10 or not row[4]:
                        continue
                    subject_name = str(row[0] or '').strip()
                    tag = str(row[1] or '').strip()
                    qtype = str(row[2] or '').strip()
                    difficulty = int(row[3] or 1)
                    content = str(row[4] or '').strip()
                    opt_a = str(row[5] or '').strip()
                    opt_b = str(row[6] or '').strip()
                    opt_c = str(row[7] or '').strip()
                    opt_d = str(row[8] or '').strip()
                    answer = str(row[9] or '').strip()
                    explanation = str(row[10] or '').strip()

                    # Validate type
                    type_map = {
                        'single_choice': 'single_choice',
                        'multi_choice': 'multi_choice',
                        'true_false': 'true_false',
                        'fill_blank': 'fill_blank',
                    }
                    qtype = type_map.get(qtype, 'single_choice')

                    # Ensure subject exists
                    subject_id = None
                    if subject_name:
                        if subject_name not in existing:
                            cursor = db.execute('INSERT INTO subjects (name) VALUES (?)', (subject_name,))
                            existing[subject_name] = cursor.lastrowid
                        subject_id = existing[subject_name]

                    # Build options
                    options = []
                    if qtype in ('single_choice', 'multi_choice'):
                        for label, val in [('A', opt_a), ('B', opt_b), ('C', opt_c), ('D', opt_d)]:
                            if val:
                                options.append({'label': label, 'content': val})
                    elif qtype == 'true_false':
                        options = [
                            {'label': 'A', 'content': '正确'},
                            {'label': 'B', 'content': '错误'},
                        ]

                    db.execute(
                        "INSERT INTO questions (subject_id,tag,type,difficulty,content,options,answer,explanation) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (subject_id, tag, qtype, difficulty, content,
                         json.dumps(options, ensure_ascii=False), answer, explanation)
                    )
                    count += 1
                except Exception as e:
                    errors.append(f'第{i}行：{e}')

            db.commit()
            msg = f'成功导入 {count} 道题目'
            if errors:
                msg += f'，{len(errors)} 行出错'
            flash(msg, 'success' if not errors else 'warning')
            if errors:
                for e in errors[:5]:
                    flash(e, 'error')
        except Exception as e:
            flash(f'导入失败：{e}', 'error')

        return redirect(url_for('list_questions'))

    return render_template('import.html')


# ══════════════════════════════════════════════════════════════════════
#  Routes – Export & JSON import
# ══════════════════════════════════════════════════════════════════════

@app.route('/export')
@require_bank
def export_bank():
    """Export current bank as a JSON file (with subjects + questions)."""
    db = get_db()
    bank_name = ''
    try:
        row = db.execute("SELECT value FROM bank_meta WHERE key='display_name'").fetchone()
        if row and row[0]:
            bank_name = row[0]
    except Exception:
        pass

    subjects = [{'id': r['id'], 'name': r['name']}
                for r in db.execute('SELECT * FROM subjects ORDER BY id').fetchall()]

    questions = []
    for q in db.execute(
            "SELECT q.*, s.name AS subject_name "
            "FROM questions q LEFT JOIN subjects s ON q.subject_id=s.id ORDER BY q.id"
    ).fetchall():
        questions.append({
            'subject': q['subject_name'] or '',
            'tag': q['tag'],
            'type': q['type'],
            'difficulty': q['difficulty'],
            'content': q['content'],
            'options': json.loads(q['options']),
            'answer': q['answer'],
            'explanation': q['explanation'],
        })

    data = {
        'format': 'family-exam-helper',
        'version': 1,
        'bank_name': bank_name,
        'subjects': subjects,
        'questions': questions,
        'exported_at': datetime.now().isoformat(),
    }

    safe_name = bank_name if bank_name else 'bank'
    # Remove characters unsafe for filenames
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', safe_name)

    resp = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    resp.headers['Content-Type'] = 'application/json; charset=utf-8'
    resp.headers['Content-Disposition'] = \
        f'attachment; filename="{safe_name}.json"'
    return resp


@app.route('/import/json', methods=['GET', 'POST'])
@require_bank
def import_json():
    """Import questions from a previously exported JSON file."""
    if request.method == 'GET':
        return render_template('import_json.html')

    if 'file' not in request.files:
        flash('请选择文件', 'error')
        return redirect(url_for('import_json'))

    f = request.files['file']
    if not f.filename.endswith('.json'):
        flash('请上传 JSON 文件（.json）', 'error')
        return redirect(url_for('import_json'))

    try:
        raw = f.read().decode('utf-8')
        data = json.loads(raw)
    except Exception as e:
        flash(f'文件读取失败：{e}', 'error')
        return redirect(url_for('import_json'))

    if data.get('format') != 'family-exam-helper':
        flash('不是有效的题库导出文件', 'error')
        return redirect(url_for('import_json'))

    db = get_db()

    # Build existing subject map (name -> id)
    existing = {r['name']: r['id'] for r in db.execute('SELECT * FROM subjects').fetchall()}

    # Import subjects (merge – skip existing)
    for s in data.get('subjects', []):
        name = s.get('name', '').strip()
        if name and name not in existing:
            cursor = db.execute('INSERT INTO subjects (name) VALUES (?)', (name,))
            existing[name] = cursor.lastrowid

    # Import questions
    count = 0
    errors = []
    for i, q in enumerate(data.get('questions', []), start=1):
        try:
            subject_name = q.get('subject', '').strip()
            subject_id = existing.get(subject_name) if subject_name else None
            tag = q.get('tag', '')
            qtype = q.get('type', 'single_choice')
            difficulty = q.get('difficulty', 1)
            content = q.get('content', '')
            options = q.get('options', [])
            answer = q.get('answer', '')
            explanation = q.get('explanation', '')

            db.execute(
                "INSERT INTO questions (subject_id,tag,type,difficulty,content,options,answer,explanation) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (subject_id, tag, qtype, difficulty, content,
                 json.dumps(options, ensure_ascii=False), answer, explanation)
            )
            count += 1
        except Exception as e:
            errors.append(f'第{i}题：{e}')

    db.commit()

    msg = f'成功导入 {count} 道题目'
    if errors:
        msg += f'，{len(errors)} 题出错'
    flash(msg, 'success' if not errors else 'warning')
    if errors:
        for e in errors[:5]:
            flash(e, 'error')
    return redirect(url_for('list_questions'))


# ══════════════════════════════════════════════════════════════════════
#  Routes – Practice mode
# ══════════════════════════════════════════════════════════════════════

@app.route('/practice/start', methods=['POST'])
@require_bank
def practice_start():
    db = get_db()
    qids = _select_question_ids(db, request.form)
    if not qids:
        flash('没有符合条件的题目', 'error')
        return redirect(url_for('bank_home'))
    session['practice_qids'] = qids
    session['practice_index'] = 0
    session['practice_answers'] = {}
    session['practice_start'] = time.time()
    return redirect(url_for('practice_question'))


@app.route('/practice')
@require_bank
def practice_question():
    qids = session.get('practice_qids', [])
    idx = session.get('practice_index', 0)
    if not qids or idx >= len(qids):
        return redirect(url_for('practice_result'))

    db = get_db()
    q = db.execute(
        "SELECT q.*, s.name AS subject_name "
        "FROM questions q LEFT JOIN subjects s ON q.subject_id=s.id WHERE q.id=?",
        (qids[idx],)
    ).fetchone()
    if not q:
        return redirect(url_for('practice_result'))

    total = len(qids)
    return render_template('practice.html',
                           question=q, index=idx, total=total,
                           options=json.loads(q['options']),
                           saved_answer=session.get('practice_answers', {}).get(str(q['id']), ''))


@app.route('/practice/next', methods=['POST'])
@require_bank
def practice_next():
    qid = request.form.get('qid')
    answer = request.form.get('answer', '').strip()
    action = request.form.get('action', 'next')

    if qid:
        answers = session.get('practice_answers', {})
        answers[str(qid)] = answer
        session['practice_answers'] = answers

    if action == 'prev':
        session['practice_index'] = max(0, session.get('practice_index', 0) - 1)
    elif action == 'finish':
        return redirect(url_for('practice_result'))
    else:
        idx = session.get('practice_index', 0) + 1
        session['practice_index'] = idx

    return redirect(url_for('practice_question'))


@app.route('/practice/result')
@require_bank
def practice_result():
    qids = session.get('practice_qids', [])
    answers = session.get('practice_answers', {})
    if not qids:
        return redirect(url_for('bank_home'))

    db = get_db()
    questions = []
    correct = 0
    for qid in qids:
        q = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
        if q:
            user_ans = answers.get(str(qid), '')
            is_correct = _check_answer(q['type'], q['answer'], user_ans)
            if is_correct:
                correct += 1
            questions.append({
                'id': q['id'],
                'type': q['type'],
                'content': q['content'],
                'options': json.loads(q['options']),
                'answer': q['answer'],
                'explanation': q['explanation'],
                'user_answer': user_ans,
                'is_correct': is_correct,
                'difficulty': q['difficulty'],
            })

    duration = int(time.time() - session.get('practice_start', time.time()))
    # Clear session
    for key in ['practice_qids', 'practice_index', 'practice_answers', 'practice_start']:
        session.pop(key, None)

    return render_template('result.html',
                           mode='practice', questions=questions,
                           correct=correct, total=len(questions),
                           duration=duration)


# ══════════════════════════════════════════════════════════════════════
#  Routes – Exam mode
# ══════════════════════════════════════════════════════════════════════

@app.route('/exam/start', methods=['POST'])
@require_bank
def exam_start():
    db = get_db()
    qids = _select_question_ids(db, request.form)
    if not qids:
        flash('没有符合条件的题目', 'error')
        return redirect(url_for('bank_home'))
    session['exam_qids'] = qids
    session['exam_index'] = 0
    session['exam_answers'] = {}
    session['exam_start'] = time.time()
    return redirect(url_for('exam_question'))


@app.route('/exam')
@require_bank
def exam_question():
    qids = session.get('exam_qids', [])
    idx = session.get('exam_index', 0)
    if not qids or idx >= len(qids):
        return redirect(url_for('exam_submit'))

    db = get_db()
    q = db.execute('SELECT * FROM questions WHERE id=?', (qids[idx],)).fetchone()
    if not q:
        return redirect(url_for('exam_submit'))

    total = len(qids)
    return render_template('exam.html',
                           question=q, index=idx, total=total,
                           options=json.loads(q['options']),
                           saved_answer=session.get('exam_answers', {}).get(str(q['id']), ''))


@app.route('/exam/next', methods=['POST'])
@require_bank
def exam_next():
    qid = request.form.get('qid')
    answer = request.form.get('answer', '').strip()
    action = request.form.get('action', 'next')

    if qid:
        answers = session.get('exam_answers', {})
        answers[str(qid)] = answer
        session['exam_answers'] = answers

    if action == 'prev':
        session['exam_index'] = max(0, session.get('exam_index', 0) - 1)
    elif action == 'finish':
        return redirect(url_for('exam_submit'))
    else:
        idx = session.get('exam_index', 0) + 1
        session['exam_index'] = idx

    return redirect(url_for('exam_question'))


@app.route('/exam/submit')
@require_bank
def exam_submit():
    qids = session.get('exam_qids', [])
    answers = session.get('exam_answers', {})
    if not qids:
        return redirect(url_for('bank_home'))

    db = get_db()
    questions = []
    correct = 0
    score_per_q = 100.0 / len(qids) if qids else 0

    for qid in qids:
        q = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
        if q:
            user_ans = answers.get(str(qid), '')
            is_correct = _check_answer(q['type'], q['answer'], user_ans)
            if is_correct:
                correct += 1
            questions.append({
                'id': q['id'],
                'type': q['type'],
                'content': q['content'],
                'options': json.loads(q['options']),
                'answer': q['answer'],
                'explanation': q['explanation'],
                'user_answer': user_ans,
                'is_correct': is_correct,
                'difficulty': q['difficulty'],
                'score': score_per_q if is_correct else 0,
            })

    total_score = correct * score_per_q
    duration = int(time.time() - session.get('exam_start', time.time()))

    # Save exam record
    try:
        db.execute(
            "INSERT INTO exam_records (mode,total_questions,correct_count,score,total_score,duration_seconds,answers) "
            "VALUES (?,?,?,?,?,?,?)",
            ('exam', len(qids), correct, total_score, 100,
             duration, json.dumps(answers, ensure_ascii=False))
        )
        db.commit()
    except Exception:
        pass

    # Clear session
    for key in ['exam_qids', 'exam_index', 'exam_answers', 'exam_start']:
        session.pop(key, None)

    return render_template('result.html',
                           mode='exam', questions=questions,
                           correct=correct, total=len(questions),
                           score=total_score, total_score=100,
                           duration=duration)


# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════

def _select_question_ids(db, form):
    """Build question ID list from form filters."""
    subject_id = form.get('subject_id', '')
    tag = form.get('tag', '')
    count = int(form.get('count', 0) or 0)

    q = "SELECT id FROM questions WHERE 1=1"
    params = []
    if subject_id:
        q += " AND subject_id=?"
        params.append(int(subject_id))
    if tag:
        q += " AND tag=?"
        params.append(tag)
    q += " ORDER BY RANDOM()"
    if count > 0:
        q += " LIMIT ?"
        params.append(count)

    rows = db.execute(q, params).fetchall()
    return [r['id'] for r in rows]


def _check_answer(qtype, correct_answer, user_answer):
    """Check if user answer matches correct answer."""
    if not user_answer:
        return False
    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()

    if qtype == 'fill_blank':
        # Multiple acceptable answers separated by |
        acceptable = [a.strip().lower() for a in correct_answer.split('|')]
        return user_answer.lower() in acceptable
    elif qtype == 'multi_choice':
        # All correct options must be selected, no extras
        correct_set = set(correct_answer.upper().replace(',', '').split())
        user_set = set(user_answer.upper().replace(',', '').split())
        return correct_set == user_set
    else:
        # single_choice, true_false
        return user_answer.upper() == correct_answer.upper()


# ══════════════════════════════════════════════════════════════════════
#  Run
# ══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
