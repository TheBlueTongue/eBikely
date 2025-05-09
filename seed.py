from app import db
from database_setup import PracticeQuestion

questions = [
    PracticeQuestion(
        question_text="What should you always wear while riding an e-bike?",
        correct_answer="A",
        option_a="Helmet",
        option_b="Sunglasses",
        option_c="Backpack",
        option_d="Sandals"
    ),
    PracticeQuestion(
        question_text="What is the maximum legal speed for an e-bike in Australia?",
        correct_answer="C",
        option_a="15 km/h",
        option_b="20 km/h",
        option_c="25 km/h",
        option_d="30 km/h"
    ),
    PracticeQuestion(
        question_text="Which of the following should you check before riding?",
        correct_answer="D",
        option_a="Battery level",
        option_b="Brakes",
        option_c="Tyre pressure",
        option_d="All of the above"
    ),
    PracticeQuestion(
        question_text="What is a safe distance to keep from other vehicles?",
        correct_answer="B",
        option_a="1 metre",
        option_b="2 metres",
        option_c="3 metres",
        option_d="4 metres"
    ),
]

db.session.add_all(questions)
db.session.commit()

print("Database seeded successfully!")