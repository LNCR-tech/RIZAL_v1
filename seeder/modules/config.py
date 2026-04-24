import os
from typing import List, Dict

# ==============================================================================
# NAMES & IDENTITIES
# ==============================================================================

FIRST_NAMES: List[str] = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica",
    "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra",
    "Miguel", "Alejandro", "Carlos", "Mateo", "Juan", "Diego", "Luis",
    "Sofia", "Valentina", "Isabella", "Camila", "Valeria", "Mariana",
    "Liam", "Noah", "Oliver", "Elijah", "Lucas", "Mason", "Logan",
    "Emma", "Olivia", "Ava", "Sophia", "Mia", "Amelia", "Harper",
    "Aiden", "Jackson", "Ethan", "Samuel", "Sebastian", "Jack", "Owen",
    "Grace", "Chloe", "Aria", "Lily", "Evelyn", "Abigail", "Ella",
    "Gabriel", "Carter", "Isaac", "Jayden", "Julian", "Dylan", "Luke",
    "Hannah", "Addison", "Aubrey", "Stella", "Natalie", "Zoe", "Leah",
    "Hiroshi", "Kenji", "Akira", "Yuki", "Mei", "Aoi", "Hinata", "Sakura",
    "Amina", "Zainab", "Fatima", "Omar", "Tariq", "Hassan", "Ali", "Hussain",
    "Aarav", "Vihaan", "Aditya", "Sai", "Aisha", "Diya", "Sanya", "Kavya",
    "Paolo", "Enrico", "Jerome", "Nathaniel", "Christian", "Adrian", "Joshua",
    "Czarina", "Angelica", "Marianne", "Katrina", "Jasmine", "Rhea", "Camille"
]

LAST_NAMES: List[str] = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Reyes", "Cruz", "Bautista", "Santos", "Gomez", "Rizal", "Aquino", "Mendoza",
    "Kim", "Chen", "Park", "Patel", "Singh", "Das", "Ali", "Hassan",
    "Villanueva", "Ocampo", "Dela Cruz", "Tolentino", "Velasco", "Soriano",
    "Rivera", "Domingo", "Ramos", "Castro", "Pascual", "Bautista", "Navarro",
    "Alcantara", "Molina", "Aguilar", "Cortez", "Ferrer", "Miranda", "Padilla",
    "Flores", "Guzman", "Salazar", "Bermudez", "Trinidad", "Castillo", "Maceda",
    "Yamamoto", "Sato", "Suzuki", "Takahashi", "Watanabe", "Tanaka", "Ito", "Nakamura",
    "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao",
    "Gupta", "Sharma", "Kumar", "Verma", "Reddy", "Nair", "Rao", "Jain"
]

MIDDLE_NAMES: List[str] = [
    "Lee", "Ann", "Marie", "Rose", "Jane", "Grace", "Louise", "Lynn",
    "Ray", "Jay", "Alan", "Paul", "Dean", "Scott", "James", "Edward",
    "Reyes", "Villanueva", "Garcia", "Ocampo", "Dela Cruz", "Tolentino",
    "Velasco", "Soriano", "Rivera", "Domingo", "Ramos", "Castro",
    "Pascual", "Navarro", "Alcantara", "Molina", "Aguilar", "Cortez",
    "Ferrer", "Miranda", "Padilla", "Flores", "Guzman", "Salazar",
    "Hope", "Faith", "Joy", "Pearl", "Dawn", "Mae", "Faye", "Ruth",
    "Alexander", "Anthony", "Charles", "David", "Joseph", "Michael"
]

SUFFIXES: List[str] = ["Jr.", "Sr.", "II", "III", "IV"]

# ==============================================================================
# ACADEMIC STRUCTURE (Universities mostly)
# ==============================================================================

SCHOOL_NAMES: List[str] = [
    "Aura University",
    "Crestview College",
    "Northwood Institute of Technology",
    "St. Jude State University",
    "Meridian Polytechnic College",
    "Lumina Global Academy",
    "Horizon Technical Institute",
    "Misamis University",
    "La Salle University",
    "St. Rita College",
    "Xavier University",
    "Ateneo de Manila University",
    "University of Santo Tomas",
    "Far Eastern University",
    "Mapua University",
    "Jose Rizal University",
    "Silliman University",
    "University of the Philippines",
    "Polytechnic University of the Philippines",
    "San Beda University",
    "National University"
]

# A generic pool of colleges. When a school is generated, it will pick N colleges 
# from this list, and for each college, pick M programs.
COLLEGES_DATASET: Dict[str, List[str]] = {
    "College of Computer Studies": [
        "BS Information Technology",
        "BS Computer Science",
        "BS Information Systems",
        "BS Software Engineering",
        "BS Cybersecurity",
        "BS Data Science",
        "BS Game Development",
        "BS Artificial Intelligence"
    ],
    "College of Engineering": [
        "BS Civil Engineering",
        "BS Mechanical Engineering",
        "BS Electrical Engineering",
        "BS Computer Engineering",
        "BS Electronics Engineering",
        "BS Industrial Engineering",
        "BS Chemical Engineering",
        "BS Aerospace Engineering",
        "BS Agricultural Engineering"
    ],
    "College of Architecture and Fine Arts": [
        "BS Architecture",
        "BS Interior Design",
        "BS Landscape Architecture",
        "B Fine Arts in Visual Communication",
        "B Fine Arts in Painting",
        "B Fine Arts in Sculpture",
        "B Multimedia Arts"
    ],
    "College of Business Administration": [
        "BS Accountancy",
        "BS Business Administration",
        "BS Marketing Management",
        "BS Financial Management",
        "BS Entrepreneurship",
        "BS Human Resource Management",
        "BS Operations Management",
        "BS Business Analytics",
        "BS Economics",
        "BS Real Estate Management"
    ],
    "College of Hospitality and Tourism": [
        "BS Hospitality Management",
        "BS Tourism Management",
        "BS Culinary Arts",
        "BS Hotel and Restaurant Management",
        "BS Travel Management"
    ],
    "College of Education": [
        "B Elementary Education",
        "B Secondary Education",
        "B Physical Education",
        "B Early Childhood Education",
        "B Special Needs Education",
        "B Technology and Livelihood Education"
    ],
    "College of Arts and Sciences": [
        "AB Psychology",
        "AB Communication",
        "AB Political Science",
        "AB English Language",
        "AB Literature",
        "AB Sociology",
        "AB Philosophy",
        "BS Biology",
        "BS Mathematics",
        "BS Chemistry",
        "BS Physics",
        "BS Environmental Science"
    ],
    "College of Nursing and Allied Health": [
        "BS Nursing",
        "BS Medical Technology",
        "BS Radiologic Technology",
        "BS Pharmacy",
        "BS Physical Therapy",
        "BS Occupational Therapy",
        "BS Respiratory Therapy",
        "BS Nutrition and Dietetics"
    ],
    "College of Medicine": [
        "Doctor of Medicine",
        "Pre-Medicine",
        "BS Public Health"
    ],
    "College of Dentistry": [
        "Doctor of Dental Medicine"
    ],
    "College of Law": [
        "Juris Doctor",
        "AB Pre-Law",
        "AB Legal Management"
    ],
    "College of Criminal Justice": [
        "BS Criminology",
        "BS Forensic Science",
        "BS Industrial Security Management",
        "BS Law Enforcement Administration"
    ],
    "College of Agriculture and Forestry": [
        "BS Agriculture",
        "BS Forestry",
        "BS Agribusiness",
        "BS Environmental Management",
        "BS Fishery and Aquatic Sciences"
    ],
    "College of Veterinary Medicine": [
        "Doctor of Veterinary Medicine"
    ],
    "College of Maritime Studies": [
        "BS Marine Transportation",
        "BS Marine Engineering",
        "BS Customs Administration",
        "BS Naval Architecture"
    ]
}

# ==============================================================================
# ROLES
# ==============================================================================

# Mirrors the core platform permissions/roles hierarchy
DEFAULT_ROLE_NAMES: List[str] = [
    "student",       
    "campus_admin",  
    "admin",         
    "ssg",           
    "sg",            
    "org"            
]

# ==============================================================================
# EVENTS
# ==============================================================================

EVENT_THEMES: List[str] = [
    "General Assembly", "Leadership Seminar", "Career Fair", "Intramurals",
    "Hackathon", "Research Symposium", "Cultural Festival", "Sports Fest",
    "Freshmen Orientation", "Graduation Ceremony", "Alumni Homecoming",
    "Health and Wellness Expo", "Debate Tournament", "Community Outreach",
    "Start-up Pitching", "Arts and Music Night", "Academic Contest",
    "Job Interview Workshop", "Mental Health Seminar", "Enviro-Action Day",
    "Founders Day Celebration", "Seniors Night", "Tech Conference"
]

EVENT_TYPES: List[str] = [
    "General Assembly", "Academic Seminar", "Orientation", 
    "Workshop", "Conference", "Meeting"
]

EVENT_LOCATIONS: List[str] = [
    "Main Gymnasium", "University Auditorium", "Student Center", "Open Field",
    "College Library", "Conference Hall A", "Conference Hall B", "Audio Visual Room",
    "University Theater", "Virtual Meeting (Zoom)", "Virtual Meeting (Teams)",
    "Innovative Hub", "Science Laboratory", "Cafeteria Event Space",
    "University Quadrangle", "Acacia Park", "Covered Court 1", "Swimming Pool Area"
]

# ==============================================================================
# PRODUCTION-GRADE SOCIAL & HISTORY MOCKS
# ==============================================================================

ANNOUNCEMENT_DATA: List[Dict[str, str]] = [
    {
        "title": "Welcome to the New Academic Semester!",
        "body": "We are excited to welcome all new and returning students. Let's make this year productive and filled with growth. Check your student portals for the updated academic calendar."
    },
    {
        "title": "Intramurals 2026: Call for Athletes",
        "body": "The annual Intramurals are approaching! Students interested in joining the basketball, volleyball, or chess teams, please sign up at the SSG office by next Friday."
    },
    {
        "title": "New Campus Security Protocols",
        "body": "For everyone's safety, please ensure your Student ID is visible at all times while on campus. Visitors must sign in at the North Gate."
    },
    {
        "title": "Upcoming Career Fair",
        "body": "Join us next month for our Grand Career Fair. Over 50 companies will be visiting to recruit for internships and full-time positions. Bring your updated CVs!"
    },
    {
        "title": "Community Cleanup Drive",
        "body": "The SSG is organizing a community cleanup drive this Saturday. Participating students will receive 5 hours of community service credit. Meet at the Quadrangle at 8:00 AM."
    }
]

MOCK_NOTE_TAGS: List[str] = ["Disciplinary", "Academic", "Leadership", "Health", "Social", "Financial"]

MOCK_NOTES_POOL: List[str] = [
    "Student is very active in class and shows great leadership potential.",
    "Needs improvement in attendance. Has missed several major assemblies.",
    "Caught using mobile phone during examination. First warning issued.",
    "Student leader for the Science Club. Very reliable and organized.",
    "Inquired about scholarship opportunities and financial aid. Referred to the FAO.",
    "Exhibited exemplary behavior during the recent outreach program.",
    "Student has been consistently late for first period classes. Advised to improve time management.",
    "Requested a change in program specialization. Currently under evaluation.",
    "A bit shy but works well in team projects. Needs encouragement to speak up.",
    "Demonstrates high proficiency in technical laboratory work."
]

COMPLIANCE_NOTES: List[str] = [
    "Handwritten apology letter submitted and verified.",
    "Community fine paid at the Finance Office. Receipt #AURA-924-X.",
    "Student completed 2 hours of library service in lieu of fine.",
    "Medical certificate provided to justify absence. Sanction waived.",
    "Late submission accepted due to technical difficulties.",
    "Requirement met after a brief interview with the Discipline Officer.",
    "Documentation verified by the SG representative."
]
