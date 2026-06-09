"""Create a sample question bank demonstrating all features."""
import sqlite3, json, os, struct, zlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Create sample images ──────────────────────────────────────────────
def create_png(filepath, width, height, r, g, b):
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            if x < 3 or x >= width - 3 or y < 3 or y >= height - 3:
                raw += bytes([50, 50, 50, 255])
            else:
                raw += bytes([r, g, b, 255])

    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw)
    with open(filepath, 'wb') as f:
        f.write(sig)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))


uploads_dir = os.path.join(BASE_DIR, 'uploads')
os.makedirs(uploads_dir, exist_ok=True)
create_png(os.path.join(uploads_dir, 'triangle.png'), 200, 160, 230, 240, 255)
create_png(os.path.join(uploads_dir, 'graph.png'), 300, 200, 255, 245, 230)
create_png(os.path.join(uploads_dir, 'circuit.png'), 250, 180, 240, 255, 240)
print('Sample images created.')

# ── Create sample bank ────────────────────────────────────────────────
db_path = os.path.join(BASE_DIR, 'banks', 'sample.db')
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
conn.executescript("""
    CREATE TABLE bank_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL);
    CREATE TABLE questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER DEFAULT NULL,
        tag TEXT DEFAULT '',
        type TEXT NOT NULL CHECK(type IN ('single_choice','multi_choice','true_false','fill_blank')),
        difficulty INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 3),
        content TEXT NOT NULL DEFAULT '',
        options TEXT DEFAULT '[]',
        answer TEXT NOT NULL DEFAULT '',
        explanation TEXT DEFAULT '',
        score REAL DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    );
    CREATE TABLE exam_records (
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

conn.execute("INSERT INTO bank_meta (key, value) VALUES ('display_name', '示例题库-功能演示')")

for name in ['数学', '计算机', '物理', '化学']:
    conn.execute('INSERT INTO subjects (name) VALUES (?)', (name,))

questions = [
    # 1. Math - LaTeX formula
    (
        1, '微积分', 'single_choice', 2,
        '<p>已知函数 \\(f(x) = x^3 - 3x^2 + 2x\\)，求 \\(f\'\'(x) = 0\\) 时 \\(x\\) 的值为：</p>',
        json.dumps([
            {'label': 'A', 'content': '\\(x = 1\\)'},
            {'label': 'B', 'content': '\\(x = \\frac{1}{3}\\)'},
            {'label': 'C', 'content': '\\(x = 1 \\text{ 或 } x = \\frac{1}{3}\\)'},
            {'label': 'D', 'content': '\\(x = 0\\)'}
        ], ensure_ascii=False),
        'C',
        '<p>对 \\(f(x) = x^3 - 3x^2 + 2x\\) 求导：</p>'
        '<p>\\(f\'\'(x) = 6x - 6 = 0\\)，解得 \\(x = 1\\)。</p>'
        '<p>再由 \\(f\'(x) = 3x^2 - 6x + 2 = 0\\)，解得 \\(x = 1 \\pm \\frac{\\sqrt{3}}{3}\\)。</p>'
    ),
    # 2. Computer - Python code
    (
        2, 'Python基础', 'single_choice', 1,
        '<p>以下 Python 代码的输出结果是什么？</p>'
        '<pre><code class="language-python">def fibonacci(n):\n    if n &lt;= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nresult = fibonacci(5)\nprint(result)</code></pre>',
        json.dumps([
            {'label': 'A', 'content': '3'},
            {'label': 'B', 'content': '5'},
            {'label': 'C', 'content': '8'},
            {'label': 'D', 'content': '13'}
        ], ensure_ascii=False),
        'B',
        '<p>斐波那契数列：\\(F(0)=0, F(1)=1, F(2)=1, F(3)=2, F(4)=3, F(5)=5\\)</p>'
        '<pre><code class="language-python">fibonacci(5)\n= fibonacci(4) + fibonacci(3)\n= 3 + 2\n= 5</code></pre>'
    ),
    # 3. Math - image + formula
    (
        1, '几何', 'single_choice', 2,
        '<p>如下图所示的三角形 ABC 中，已知 \\(\\angle B = 90°\\)，'
        '\\(AB = 3\\)，\\(BC = 4\\)，求斜边 \\(AC\\) 的长度：</p>'
        '<p><img src="/uploads/triangle.png" alt="直角三角形" width="200" /></p>',
        json.dumps([
            {'label': 'A', 'content': '\\(AC = 5\\)'},
            {'label': 'B', 'content': '\\(AC = 6\\)'},
            {'label': 'C', 'content': '\\(AC = 7\\)'},
            {'label': 'D', 'content': '\\(AC = \\sqrt{7}\\)'}
        ], ensure_ascii=False),
        'A',
        '<p>根据勾股定理：\\(AC^2 = AB^2 + BC^2 = 9 + 16 = 25\\)</p>'
        '<p>所以 \\(AC = \\sqrt{25} = 5\\)。</p>'
    ),
    # 4. Computer - multi_choice with code
    (
        2, '数据结构', 'multi_choice', 3,
        '<p>以下哪些是 Python 中合法的列表操作？</p>'
        '<pre><code class="language-python">my_list = [1, 2, 3, 4, 5]</code></pre>',
        json.dumps([
            {'label': 'A', 'content': '<code>my_list.append(6)</code>'},
            {'label': 'B', 'content': '<code>my_list[1:3]</code>'},
            {'label': 'C', 'content': '<code>my_list[-1]</code>'},
            {'label': 'D', 'content': '<code>my_list[5] = 10</code>（直接赋值到索引5）'}
        ], ensure_ascii=False),
        'A,B,C',
        '<p><strong>A</strong>: <code>append()</code> 在末尾添加元素 ✅</p>'
        '<p><strong>B</strong>: 切片 <code>[1:3]</code> 返回 <code>[2, 3]</code> ✅</p>'
        '<p><strong>C</strong>: 负索引 <code>[-1]</code> 返回 <code>5</code> ✅</p>'
        '<p><strong>D</strong>: 索引 5 超出范围（最大索引4），抛出 <code>IndexError</code> ❌</p>'
    ),
    # 5. Physics - true/false with formula
    (
        3, '力学', 'true_false', 1,
        '<p>根据牛顿第二定律 \\(\\vec{F} = m\\vec{a}\\)，当物体质量 \\(m\\) 不变时，'
        '加速度 \\(\\vec{a}\\) 与合外力 \\(\\vec{F}\\) 成正比。</p>',
        json.dumps([
            {'label': 'A', 'content': '正确'},
            {'label': 'B', 'content': '错误'}
        ], ensure_ascii=False),
        'A',
        '<p>由 \\(\\vec{F} = m\\vec{a}\\) 得 \\(\\vec{a} = \\frac{\\vec{F}}{m}\\)，'
        '当 \\(m\\) 为常数时，\\(\\vec{a}\\) 与 \\(\\vec{F}\\) 成正比。</p>'
    ),
    # 6. Chemistry - fill_blank with LaTeX
    (
        4, '化学方程式', 'fill_blank', 1,
        '<p>完成以下化学方程式配平：</p>'
        '<p>\\(\\text{H}_2\\text{SO}_4 + \\text{NaOH} \\rightarrow \\text{Na}_2\\text{SO}_4 + \\)'
        ' ___ \\(\\text{H}_2\\text{O}\\)</p>'
        '<p>请填写生成的水的系数（数字）：</p>',
        json.dumps([], ensure_ascii=False),
        '2',
        '<p>配平后：</p>'
        '<p>\\(\\text{H}_2\\text{SO}_4 + 2\\text{NaOH} \\rightarrow \\text{Na}_2\\text{SO}_4 + 2\\text{H}_2\\text{O}\\)</p>'
        '<p>左侧 H: \\(2+2=4\\)，右侧 H: \\(2 \\times 2 = 4\\) ✅</p>'
    ),
    # 7. Computer - fill_blank with code
    (
        2, 'Python基础', 'fill_blank', 2,
        '<p>以下代码的输出是什么？</p>'
        '<pre><code class="language-python">my_dict = {"name": "Alice", "age": 18, "score": 95}\nkeys = list(my_dict.keys())\nprint(keys[1])</code></pre>',
        json.dumps([], ensure_ascii=False),
        'age',
        '<p><code>my_dict.keys()</code> 返回 <code>dict_keys([\'name\', \'age\', \'score\'])</code></p>'
        '<p>转为列表后 <code>keys = [\'name\', \'age\', \'score\']</code></p>'
        '<p><code>keys[1]</code> 即第二个元素 <code>\'age\'</code>。</p>'
    ),
    # 8. Physics - image + formula
    (
        3, '运动学', 'single_choice', 3,
        '<p>物体从高度 \\(h = 20\\text{m}\\) 自由落下'
        '（忽略空气阻力，\\(g = 10\\text{m/s}^2\\)），求落地速度：</p>'
        '<p><img src="/uploads/graph.png" alt="自由落体示意图" width="300" /></p>',
        json.dumps([
            {'label': 'A', 'content': '\\(v = 10\\text{ m/s}\\)'},
            {'label': 'B', 'content': '\\(v = 20\\text{ m/s}\\)'},
            {'label': 'C', 'content': '\\(v = 15\\text{ m/s}\\)'},
            {'label': 'D', 'content': '\\(v = 25\\text{ m/s}\\)'}
        ], ensure_ascii=False),
        'B',
        '<p>由自由落体公式：\\(v^2 = 2gh = 2 \\times 10 \\times 20 = 400\\)</p>'
        '<p>所以 \\(v = \\sqrt{400} = 20\\text{ m/s}\\)</p>'
    ),
    # 9. Computer - Java code
    (
        2, 'Java基础', 'single_choice', 2,
        '<p>以下 Java 代码的输出是什么？</p>'
        '<pre><code class="language-java">public class Test {\n'
        '    public static void main(String[] args) {\n'
        '        int[] arr = {5, 3, 8, 1, 9};\n'
        '        Arrays.sort(arr);\n'
        '        System.out.println(arr[2]);\n'
        '    }\n'
        '}</code></pre>',
        json.dumps([
            {'label': 'A', 'content': '1'},
            {'label': 'B', 'content': '3'},
            {'label': 'C', 'content': '5'},
            {'label': 'D', 'content': '8'}
        ], ensure_ascii=False),
        'C',
        '<p><code>Arrays.sort(arr)</code> 排序后为 <code>[1, 3, 5, 8, 9]</code></p>'
        '<p><code>arr[2]</code> 即第三个元素 <code>5</code>。</p>'
    ),
    # 10. Chemistry - image + multi_choice
    (
        4, '原子结构', 'multi_choice', 2,
        '<p>关于原子结构，以下说法正确的是（多选）：</p>'
        '<p><img src="/uploads/circuit.png" alt="原子结构示意图" width="250" /></p>',
        json.dumps([
            {'label': 'A', 'content': '原子核由质子和中子组成'},
            {'label': 'B', 'content': '电子在核外分层排布'},
            {'label': 'C', 'content': '原子的质量主要集中在电子上'},
            {'label': 'D', 'content': '质子带正电，电子带负电'}
        ], ensure_ascii=False),
        'A,B,D',
        '<p><strong>A</strong> ✅ 原子核由质子和中子构成</p>'
        '<p><strong>B</strong> ✅ 电子按能量高低分层排布</p>'
        '<p><strong>C</strong> ❌ 质量主要集中在原子核（质子/中子质量远大于电子）</p>'
        '<p><strong>D</strong> ✅ 质子带正电，电子带负电</p>'
    ),
]

for q in questions:
    conn.execute(
        'INSERT INTO questions (subject_id,tag,type,difficulty,content,options,answer,explanation) '
        'VALUES (?,?,?,?,?,?,?,?)',
        q
    )

conn.commit()

count = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
print(f'Created sample bank: {count} questions')
for t in ['single_choice', 'multi_choice', 'true_false', 'fill_blank']:
    c = conn.execute('SELECT COUNT(*) FROM questions WHERE type=?', (t,)).fetchone()[0]
    if c:
        print(f'  {t}: {c}')
conn.close()
print('Done!')
