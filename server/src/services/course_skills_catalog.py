"""Keyword-to-skills mapping for academic course titles (case-insensitive substring match)."""

from __future__ import annotations

DEFAULT_COURSE_SKILLS = "Computer Science, Software Engineering"

# Each entry: (keywords, skills). First matching rule wins — list more specific phrases first.
COURSE_SKILL_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    # 1. Core CS & Foundations
    (("מבוא למדעי המחשב",), "Python, Algorithmic Thinking, Loops, Functions, Recursion"),
    (
        ("מבוא לתכנות מערכות",),
        "C Language, Manual Memory Management, Pointers, Linux Terminal, GCC, Valgrind",
    ),
    (
        ("תכנות מונחה עצמים",),
        "Java, C#, OOP Principles, Inheritance, Polymorphism, Design Patterns",
    ),
    (
        ("מבני נתונים",),
        "Linked Lists, Binary Search Trees, AVL Trees, Hash Tables, Computational Complexity, Interview Prep",
    ),
    (
        ("תכנון וניתוח אלגוריתמים",),
        "Greedy Algorithms, Dynamic Programming, Graph Algorithms",
    ),
    (
        ("אלגוריתם מתקדם וסיבוכיות",),
        "P vs NP, Computational Complexity, Optimization Problems, Heuristics",
    ),
    (
        ("מודלים חישוביים",),
        "Automata Theory, Formal Languages, Turing Machines, Abstract Thinking",
    ),
    (
        ("עקרונות שפות תכנות",),
        "Programming Paradigms, Functional Programming, Logical Programming, Type Systems",
    ),
    # 2. Software Engineering & Methodologies
    (
        ("מבוא להנדסת תכנה", "מבוא להנדסת תוכנה"),
        "Software Development Life Cycle, SDLC, MVC Architecture, Code QA, Testing",
    ),
    (
        ("כלי פיתוח",),
        "Git, GitHub, Docker, Linux, Bash, Maven, npm, Automation",
    ),
    (
        ("Agile", "אג'ייל", "מתודולוגיות תכנות"),
        "Agile Methodologies, Scrum, Kanban, Jira, Teamwork",
    ),
    (
        ("כתיבה עסקית",),
        "Design Docs, Technical Reports, Professional English Communication",
    ),
    (("אתיקה", "Ethics"), "Data Privacy, Copyrights, Algorithmic Bias, Engineering Ethics"),
    (
        ("סמינר בשיטות פיתוח", "סמינר מדעי מחשב"),
        "Literature Review, Independent Research, Presentation Skills",
    ),
    # 3. Systems, Hardware & Networking
    (
        ("ארגון המחשב", "שפת סף"),
        "Assembly Language, Registers, CPU Cache, Processor Architecture",
    ),
    (
        ("מערכות הפעלה",),
        "C, C++, Processes, Threads, Mutex Synchronization, Virtual Memory",
    ),
    (
        ("תקשורת מחשבים",),
        "Wireshark, OSI Model, TCP/IP, HTTP, DNS, Socket Programming",
    ),
    (
        ("מערכות משובצות", "Embedded"),
        "C, C++, Microcontrollers, RTOS, I2C, SPI",
    ),
    (
        ("מחשוב מקבילי", "מבוזר"),
        "OpenMP, MPI, CUDA, GPU Programming, Deadlock Prevention",
    ),
    # 4. Web, Mobile & Enterprise Frameworks
    (
        ("WEB", "אינטרנט", "פיתוח אפליקציות"),
        "HTML, CSS, JavaScript, TypeScript, React, Angular, Node.js, FastAPI, REST APIs",
    ),
    (
        ("Dot Net", "דרונט", "נט."),
        "C#, .NET Core, Web APIs, Entity Framework ORM",
    ),
    (
        ("C++", "סי פלוס פלוס"),
        "Modern C++, Smart Pointers, STL, RAII Resource Management",
    ),
    (
        ("IOS", "איי או אס"),
        "Swift Language, Xcode IDE, SwiftUI, UIKit, Mobile Lifecycle",
    ),
    (
        ("טכנולוגיות סלולריות",),
        "Hybrid Mobile Apps, Sensor Monitoring, Mobile Battery Optimization",
    ),
    (
        ("בסיסי נתונים", "Databases"),
        "SQL, PostgreSQL, MySQL, NoSQL, MongoDB, Database Indexing, Database Schema",
    ),
    (
        ("בלוקצ'יין", "Blockchain"),
        "Solidity, Smart Contracts, Ethereum Network, Applied Cryptography",
    ),
    # 5. UI/UX
    (
        ("אפיון ממשק", "פיתוח ממשק"),
        "Figma, Interactive Prototyping, User Flows, Usability Testing",
    ),
    (
        ("עיצוב חזותי",),
        "Color Theory, Typography, Visual Hierarchy, Design Systems",
    ),
    (
        ("אבטחת ממשק",),
        "Interface Privacy, Multi-Factor Authentication, 2FA, Biometrics, GDPR Compliance",
    ),
    # 6. Cybersecurity
    (
        ("סמינר בסייבר",),
        "Advanced Persistent Threats, APTs, Cyber Attack Vectors, Cyber Intelligence",
    ),
    (
        ("אבטחת מידע", "אבטחת סייבר"),
        "Cryptography, AES, RSA, OWASP Top 10, Software Risk Management",
    ),
    (
        ("אבטחת רשתות",),
        "Firewalls, HTTPS, SSH, DDoS Mitigation, MitM Prevention",
    ),
    # 7. AI, Data Science & Machine Learning
    (
        ("מבוא לבינה מלאכותית",),
        "Python, A* Search, Minimax Algorithm, Rule-Based Systems",
    ),
    (
        ("למידת מכונה", "Machine Learning"),
        "Python, Scikit-Learn, Pandas, NumPy, Regression, Classification, Feature Engineering",
    ),
    (
        ("רשתות נוירונים", "למידה עמוקה"),
        "PyTorch, TensorFlow, Deep Neural Networks, CNN, Transformers Architecture",
    ),
    (
        ("עיבוד שפה", "NLP"),
        "Hugging Face, Large Language Models, LLMs, Tokenization, Sentiment Analysis",
    ),
    (
        ("מפתח AI", "מונחה בינה מלאכותית"),
        "OpenAI API, Anthropic API, Vector Databases, RAG Architecture, AI Coding Assistant, Cursor, Copilot",
    ),
    (
        ("ראייה ממוחשבת", "Computer Vision"),
        "OpenCV, Object Detection, YOLO, Digital Image Processing, Video Tracking",
    ),
    (
        ("כריית מידע", "נתוני עתק"),
        "Apache Spark, Hadoop, MapReduce Model, Pattern Recognition",
    ),
    (
        ("אנליזה מתמטית של רשתות", "רשתות חברתיות"),
        "Python, NetworkX Library, Centrality Metrics, Community Detection",
    ),
    (
        ("רכבים אוטונומיים",),
        "Real-Time Decision Making, Sensor Fusion, AI Human-Machine Interface",
    ),
    # 8. Gaming & Computer Graphics
    (
        ("בינה מלאכותית לפיתוח משחקים",),
        "Smart NPCs, Behavior Trees, A* Pathfinding",
    ),
    (
        ("עיצוב ופיתוח משחקים", "פיתוח משחקים"),
        "Unity, C#, Unreal Engine, C++, Game Loop, Game Physics",
    ),
    (
        ("גרפיקה ממוחשבת",),
        "OpenGL, WebGL, Matrix Mathematics, Vectors, Shaders, 3D Rendering Pipeline",
    ),
    # 9. Mathematics & Optimization
    (
        ("חשבון דיפרנציאלי", "אינטגרלי", "אלגברה ליניארית"),
        "Calculus, Vector Spaces, Matrix Mathematics, Linear Algebra",
    ),
    (
        ("מתמטיקה בדידה", "לוגיקה מתמטית"),
        "Graph Theory, Combinatorics, Propositional Logic, Discrete Mathematics",
    ),
    (
        ("הסתברות", "סטטיסטיקה", "מודלים סטוכסטיים"),
        "Probability Distributions, Hypothesis Testing, Markov Chains, Uncertainty Analysis",
    ),
    (
        ("חקר ביצועים", "שיטות באופטימיזציה", "תורת המשחקים"),
        "Linear Programming, Constrained Optimization, Strategic Decision Theory",
    ),
    (
        ("תורת המידע",),
        "Information Theory, Entropy, Huffman Coding, Error-Correcting Codes",
    ),
    # 10. Soft Skills & General Electives
    (
        ("אנגלית", "English"),
        "Technical Documentation Reading, Coding in English, International Communication",
    ),
    (
        ("יזמים", "יזמות", 'מבוא לפכ"מ'),
        "Business Models, Economics, Market Opportunity Identification, Product Thinking",
    ),
    (
        ("Black Belt",),
        "Engineering Excellence, Tech Leadership, High-Pressure Operations",
    ),
    (
        ("פילוסופיה", "היסטוריה", "אקזיסטנציאליזם", "קולנוע"),
        "Critical Thinking, Complex Text Analysis, Global Process Analysis",
    ),
    (
        ("מודיעין",),
        "Uncertainty Decision Making, Situation Assessment, Intelligence Data Analysis",
    ),
    (
        ("Human Language",),
        "Theoretical Linguistics, Syntax, Language Structure",
    ),
    (
        ("תרבות וחברה", "עוני", "בריאות", "מגדר"),
        "Empathy, Target Audience Analysis, Societal Technology Impact",
    ),
    (
        ("טכנולוגיה ובני אדם",),
        "Human-Computer Interface, HCI, Attention Mechanisms, Digital Psychology",
    ),
    (
        ("תעופה", "אנרגיה גרעינית", "ארכיאולוגיה", "שיטות מחקר"),
        "Research Methodologies, Mission-Critical Systems",
    ),
    # 11. Final Capstone Project
    (
        ("פרויקט גמר",),
        "Full-Stack Development, React, Node.js, Python, Architecture Design, Time Management, Product Presentation",
    ),
)


def resolve_skills_from_course_title(title: str) -> str:
    """Return skills for a course title using case-insensitive keyword substring matching."""
    if not title:
        return DEFAULT_COURSE_SKILLS

    normalized_title = title.casefold()
    for keywords, skills in COURSE_SKILL_RULES:
        for keyword in keywords:
            if keyword.casefold() in normalized_title:
                return skills
    return DEFAULT_COURSE_SKILLS
