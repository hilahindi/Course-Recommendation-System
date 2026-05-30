"""Explicit course-title → skills mapping (comma-separated)."""

from __future__ import annotations

# Canonical Hebrew course name → skills text
COURSE_SKILLS_BY_NAME: dict[str, str] = {
    # Core CS
    "מבוא למדעי המחשב": (
        "Algorithmic Thinking, Python, Problem Decomposition, Functions, Recursion"
    ),
    "מבוא לתכנות מערכות": (
        "C Language, Manual Memory Management, Dynamic Allocation, Pointers, "
        "GCC, Valgrind, Linux Terminal"
    ),
    "תכנות מונחה עצמים": (
        "Java, C#, OOP Principles, Design Patterns, Reusable Code Engineering"
    ),
    "מבני נתונים": (
        "Hash Tables, Binary Search Trees, Heaps, Linked Lists, Abstract Data Types, Complexity Analysis"
    ),
    "מתמטיקה בדידה": (
        "Graph Theory, Combinatorics, Propositional Logic, Set Theory, Mathematical Proofs, Discrete Structures"
    ),
    "חשבון דיפרנציאלי ואינטגרלי 1": (
        "Limits, Continuity, Derivatives, Integrals, Taylor Series, Single-Variable Calculus"
    ),
    "חשבון דיפרנציאלי ואינטגרלי 2": (
        "Multivariable Calculus, Partial Derivatives, Multiple Integrals, Vector Calculus, Series"
    ),
    "אלגברה ליניארית 1": (
        "Matrices, Vector Spaces, Linear Transformations, Determinants, Eigenvalues, Systems of Equations"
    ),
    "לוגיקה מתמטית למדעי המחשב": (
        "Propositional Logic, Predicate Logic, Proof Techniques, Set Theory, Formal Reasoning"
    ),
    "פרויקט גמר למדעים 1": (
        "Requirements Analysis, System Design, Technical Documentation, Team Collaboration, Milestone Planning"
    ),
    "פרויקט גמר למדעים 2": (
        "Full-Stack Integration, Testing Strategy, Deployment, Project Presentation, Engineering Trade-offs"
    ),
    "הסקה סטטיסטית": (
        "Statistical Inference, Confidence Intervals, Bayesian Reasoning, Hypothesis Testing, Data Interpretation"
    ),
    "אלגוריתמים אקראיים, מקורבים ומקוונים": (
        "Randomized Algorithms, Approximation Algorithms, Online Algorithms, Probabilistic Analysis, Performance Bounds"
    ),
    "תכנון וניתוח אלגוריתמים": (
        "Greedy Algorithms, Dynamic Programming, Graph Algorithms, Dijkstra, "
        "BFS, DFS, Time and Space Complexity Analysis"
    ),
    "אלגוריתמים מתקדמים וסיבוכיות": (
        "Problem Classification, P vs NP, Approximation Algorithms, Heuristics, "
        "Hard Optimization, NP-Hard Problems"
    ),
    "אלגוריתם מתקדם וסיבוכיות": (
        "Problem Classification, P vs NP, Approximation Algorithms, Heuristics, "
        "Hard Optimization, NP-Hard Problems"
    ),
    "מבוא למערכות הפעלה": (
        "Process Management, Threads, Mutex, Semaphore, Virtual Memory, Parallel Programming"
    ),
    "מערכות הפעלה": (
        "Process Management, Threads, Mutex, Semaphore, Virtual Memory, Parallel Programming"
    ),
    "תקשורת מחשבים לתוכנה": (
        "Wireshark, Socket Programming, Layered Model, TCP, IP, HTTP, DNS, Client-Server Architecture"
    ),
    "ארגון המחשב ושפת סף": (
        "Assembly Language, x86, ARM, Register Management, Processor Optimization, Cache, Hardware Instructions"
    ),
    "מודלים חישוביים": (
        "Finite Automata, Formal Languages, Regular Expressions, Regex, Turing Machines, Text Analysis Foundations"
    ),
    "מבוא להנדסת תוכנה": (
        "SDLC, System Architecture, MVC, Unit Testing, Product Requirements Analysis"
    ),
    "בסיסי נתונים": (
        "SQL, Relational Databases, PostgreSQL, MySQL, NoSQL, MongoDB, Schema Design, Query Optimization"
    ),
    "קומפילציה": (
        "Lexers, Parsers, Syntax Analysis, LL Parsing, LR Parsing, Code Translation, State Machines, Compilers"
    ),
    # Frameworks & applied dev
    "פיתוח בפלטפורמות WEB": (
        "Full-Stack Development, HTML5, CSS3, JavaScript, TypeScript, React.js, Node.js, FastAPI, REST APIs"
    ),
    "פיתוח בפלטפורמת WEB": (
        "Full-Stack Development, HTML5, CSS3, JavaScript, TypeScript, React.js, Node.js, FastAPI, REST APIs"
    ),
    "תכנות בפלטפורמת Dot Net": (
        "C#, .NET Core, Entity Framework, ORM, Dependency Injection, Enterprise Systems"
    ),
    "סדנא בתכנות מונחה עצמים עם C++": (
        "Modern C++, Resource Management, RAII, Smart Pointers, STL, Templates"
    ),
    "פיתוח בסביבת IOS": (
        "Swift, Xcode, SwiftUI, UIKit, Memory Management, ARC, Mobile App Development"
    ),
    "פיתוח משחקים": (
        "Unity Engine, C#, Digital Assets, Game Physics, Game Loop Architecture"
    ),
    "סדנה בעיצוב ופיתוח משחקי מחשב": (
        "Game Production, Gameplay Flow Design, Game Mechanics, Cross-Disciplinary Teamwork"
    ),
    "כלי פיתוח": (
        "Git, GitHub, Docker, Bash Scripting, Environment Automation, npm, Maven"
    ),
    "מערכות משובצות מחשב": (
        "Embedded C, Microcontrollers, RTOS, Hardware Protocols, I2C, SPI, UART"
    ),
    "מחשוב מקבילי ומבוזר": (
        "OpenMP, MPI, GPU Programming, CUDA, Distributed Computing, Deadlock Prevention"
    ),
    "מתודולוגיות תכנות Agile": (
        "Jira, Scrum, Sprints, Task Prioritization, Backlog Management, Team Collaboration"
    ),
    "בלוקצ'יין חזון ופרקטיקה": (
        "Solidity, Smart Contracts, DApps, Ethereum, Consensus Mechanisms, PoW, PoS, Web3 Architecture"
    ),
    # AI & data science
    "מבוא לבינה מלאכותית": (
        "A* Search, Knowledge Representation, Intelligent Agents, Minimax Algorithm"
    ),
    "למידת מכונה": (
        "Python, Scikit-Learn, Pandas, NumPy, Classification, Regression, SVM, Random Forest, K-Means, Model Evaluation"
    ),
    "רשתות נוירונים ולמידה עמוקה": (
        "PyTorch, TensorFlow, Deep Neural Networks, CNN, Transformers, Overfitting Prevention"
    ),
    "עיבוד שפה טבעית": (
        "Large Language Models, LLMs, Hugging Face, spaCy, Tokenization, Sentiment Analysis, Text Classification"
    ),
    "פיתוח תוכנה מונחה בינה מלאכותית למפתחים": (
        "OpenAI APIs, Vector Databases, Pinecone, RAG Architecture, AI-Assisted Coding, Prompt Engineering"
    ),
    "מבוא לראייה ממוחשבת": (
        "OpenCV, Image Filtering, Edge Detection, Feature Extraction, Camera Geometry Algorithms"
    ),
    "רשתות נוירונים לראייה ממוחשבת": (
        "Deep Learning for Images, Real-Time Object Detection, YOLO, Segmentation, Video Classification"
    ),
    "כריית מידע": (
        "Pattern Discovery, Data Noise Filtering, Recommendation Engines, Business Insights from Raw Data"
    ),
    "ניתוח נתוני עתק": (
        "Apache Spark, Hadoop, MapReduce, ETL Pipelines, Large-Scale Data Processing"
    ),
    "בינה מלאכותית לפיתוח משחקים": (
        "NPC AI, Behavior Trees, Finite State Machines, FSM, Pathfinding, Navigation Algorithms"
    ),
    "ניתוח רשתות חברתיות": (
        "Social Network Modeling, Centrality Metrics, Influencer Detection, Network Vulnerability Analysis"
    ),
    "אנליזה מתמטית של רשתות": (
        "Graph Modeling, Flow Networks, Dynamic Network Analysis, Routing Optimization Under Load"
    ),
    "אנליזה מתמטית של רשתות חברתיות": (
        "Social Network Modeling, Centrality Metrics, Influencer Detection, Network Vulnerability Analysis"
    ),
    "רכבים אוטונומיים והנדסת אנוש בעולמות ה-AI": (
        "Sensor Fusion, Real-Time Decision Making, Human-Computer Interaction, HCI, Learning AI Systems"
    ),
    # Cyber
    "אבטחת מידע": (
        "Cryptography, Password Security, Vulnerability Identification, Injection Prevention, Key Management"
    ),
    "אבטחת סייבר": (
        "OWASP Top 10, Vulnerability Assessment, Burp Suite, Access Control, Penetration Testing Basics"
    ),
    "אבטחת רשתות תקשורת": (
        "Firewalls, Secure Traffic Analysis, HTTPS, SSH, DDoS Prevention, Spoofing, Man-in-the-Middle"
    ),
    "סייבר-אבטחת רשתות תקשורת": (
        "Firewalls, Secure Traffic Analysis, HTTPS, SSH, DDoS Prevention, Spoofing, Man-in-the-Middle"
    ),
    "פיתוח מאובטח": (
        "Secure Coding, Vulnerability Prevention, Buffer Overflow Prevention, API Security"
    ),
    "אבטחת מובייל": (
        "Android Security, iOS Security, Local Storage Protection, Cellular Network Security, Reverse Engineering Prevention"
    ),
    "קריפטוגרפיה מודרנית": (
        "AES, RSA, Hashing, Digital Signatures, Public Key Infrastructure, PKI"
    ),
    # UI/UX & additional electives
    "אפיון ממשקי משתמש": (
        "Figma, Interactive Prototyping, User Flows, Usability Testing, Requirements Gathering"
    ),
    "פיתוח ממשקי משתמש": (
        "Kotlin, Android Studio, Android SDK, UI Components, XML Layouts, Mobile App Development"
    ),
    "עיצוב חזותי של ממשקי משתמש": (
        "Color Theory, Typography, Visual Hierarchy, Design Systems, UI Composition"
    ),
    "גרפיקה ממוחשבת": (
        "OpenGL, WebGL, Linear Algebra for Graphics, Shaders, 3D Rendering Pipeline"
    ),
    "סטטיסטיקה": "Descriptive Statistics, Inferential Statistics, Hypothesis Testing, Data Analysis",
    "תורת המידע": "Entropy, Huffman Coding, Error-Correcting Codes, Information Theory",
    "אתיקה בהנדסת תוכנה": "Engineering Ethics, Data Privacy, Algorithmic Bias, Professional Responsibility",
    "עקרונות שפות תכנות": (
        "Programming Paradigms, Functional Programming, Type Systems, Language Semantics"
    ),
    "למידה חישובית": "Computational Learning, Algorithm Analysis for ML, Theoretical ML Foundations",
    # Seminars
    "סמינר במדעי המחשב": "Independent Research, Literature Review, Technical Presentation",
    "סמינר מתקדם בטכנולוגיות סלולריות": "Mobile Technologies, Hybrid Apps, Sensor Monitoring, Battery Optimization",
    "סמינר בסייבר": "Advanced Threats, Attack Vectors, Cyber Intelligence",
    "סמינר בלמידה חישובית": "Computational Learning Theory, ML Research Methods",
    "סמינר בשפות תכנות": "Programming Language Theory, Paradigms Comparison",
}


# Fallback inference when a course is not in the explicit catalog (no generic CS default).
_INFERENCE_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("אנגלית", "english"), "Technical Reading, Academic Writing, Professional Communication"),
    (("סמינר",), "Literature Review, Academic Writing, Oral Presentation, Critical Analysis"),
    (("סדנא", "סדנה"), "Hands-on Practice, Lab Work, Implementation Exercises"),
    (("פרויקט", "גמר"), "Project Management, Integration, Documentation, Demo Presentation"),
    (("מתמטיק", "אלגברה", "חשבון", "הסתברות", "סטטיסטיק"), "Mathematical Modeling, Quantitative Reasoning, Problem Solving"),
    (("פיזיק",), "Physical Modeling, Scientific Computing, Measurement Analysis"),
    (("כלכלה", "יזמות", "עסקי"), "Business Analysis, Market Research, Decision Making"),
    (("פסיכולוג", "חברה", "תרבות"), "Critical Thinking, Qualitative Analysis, Research Methods"),
)


def infer_skills_from_course_title(course_name: str) -> str:
    """Derive contextual skills from the course title without a generic CS placeholder."""
    name = (course_name or "").strip()
    if not name:
        return ""

    folded = name.casefold()
    for keywords, skills in _INFERENCE_RULES:
        for keyword in keywords:
            if keyword.casefold() in folded:
                return skills

    tokens = [word for word in folded.replace("–", " ").split() if len(word) > 2]
    if any(t in tokens for t in ("תכנות", "פיתוח", "מערכת", "תוכנה")):
        return "Programming Practice, Debugging, Code Design, Technical Problem Solving"
    if any(t in tokens for t in ("מידע", "נתונ", "דאטה")):
        return "Data Analysis, Data Modeling, Analytical Thinking"
    if any(t in tokens for t in ("אבטח", "סייבר", "קריפטו")):
        return "Security Analysis, Risk Assessment, Defensive Thinking"
    if any(t in tokens for t in ("בינה", "למיד", "ai")):
        return "Model Building, Experimentation, Evaluation Metrics"

    return "Domain Concepts, Analytical Thinking, Applied Problem Solving"


def resolve_skills_for_course_name(course_name: str) -> str:
    name = (course_name or "").strip()
    if not name:
        return ""

    if name in COURSE_SKILLS_BY_NAME:
        return COURSE_SKILLS_BY_NAME[name]

    folded = name.casefold()
    for canonical, skills in COURSE_SKILLS_BY_NAME.items():
        if canonical.casefold() in folded or folded in canonical.casefold():
            return skills

    return infer_skills_from_course_title(name)


def parse_skill_names(skills_text: str) -> list[str]:
    if not skills_text.strip():
        return []
    return [part.strip() for part in skills_text.split(",") if part.strip()]
