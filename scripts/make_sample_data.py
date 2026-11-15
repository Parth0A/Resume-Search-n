"""Generate synthetic sample data (no real people).

    python scripts/make_sample_data.py data/sample_resumes.csv data/sample_relevance.csv

Writes 40 mixed-case resumes and, optionally, graded relevance labels for scripts/evaluate.py.
The random seed is fixed, so the output is the same every time.
"""

import csv
import random
import sys

random.seed(7)
FIRST = ["Asha", "Ben", "Chen", "Divya", "Elif", "Farid", "Grace", "Hiro", "Ines", "Jonas", "Kavya", "Liam",
         "Maya", "Noah", "Olu", "Priya", "Quinn", "Rosa", "Sami", "Tara"]
LAST = ["Rao", "Okafor", "Lindqvist", "Mehta", "Novak", "Silva", "Tanaka", "Haddad", "Moreau", "Kowalski"]
ROLES = {
    "Python Developer": ["Python", "Django", "Flask", "REST API", "PostgreSQL", "Docker", "Git", "Pandas"],
    "Data Scientist": ["Python", "Machine Learning", "Pandas", "NumPy", "TensorFlow", "SQL", "Statistics"],
    "Frontend Developer": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Figma", "Jest"],
    "Java Developer": ["Java", "Spring Boot", "Microservices", "MySQL", "Kafka", "Docker", "AWS"],
    "DevOps Engineer": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "CI/CD", "Python"],
    "Data Analyst": ["SQL", "Excel", "Power BI", "Tableau", "Python", "Statistics", "Communication"],
    "QA / Test Engineer": ["Selenium", "Testing", "Python", "Java", "Jira", "API testing", "Git"],
    "UI / UX Designer": ["Figma", "UI/UX", "User research", "Prototyping", "HTML", "CSS", "Accessibility"],
}
EXPERIENCE = ["{n} years of experience", "{n}+ years experience", "over {n} years of experience",
              "experience of {n} years", None]
STYLE = [str.upper, str.title, str.lower, lambda s: s]


def resume(name: str, role: str, index: int) -> str:
    skills = random.sample(ROLES[role], k=min(5, len(ROLES[role])))
    phrase = random.choice(EXPERIENCE)
    years = random.randint(1, 12)
    experience = "with " + phrase.format(n=years) if phrase else "and recent graduate (B.Sc. 2023)"
    style = STYLE[index % len(STYLE)]
    contact = f"{name.split()[0].lower()}.{index}@example.com | +1 555 01{index:02d} {random.randint(1000, 9999)}"
    body = (
        f"{style(role)} {experience}. Skilled in {', '.join(skills)}. "
        f"Built and maintained production systems, collaborated with cross-functional teams, "
        f"and mentored junior colleagues. Strong written communication and problem solving. "
        f"Projects: internal analytics dashboard, customer onboarding service, automated reporting pipeline."
    )
    return f"{name} - {contact}. {body}"


QUERIES = {
    "python developer django api": {"Python Developer": 2, "Data Scientist": 1, "DevOps Engineer": 1},
    "data scientist machine learning": {"Data Scientist": 2, "Data Analyst": 1, "Python Developer": 1},
    "frontend developer react javascript": {"Frontend Developer": 2, "UI / UX Designer": 1},
    "java backend spring microservices": {"Java Developer": 2, "Python Developer": 1},
    "devops engineer kubernetes aws": {"DevOps Engineer": 2, "Java Developer": 1},
    "data analyst sql power bi": {"Data Analyst": 2, "Data Scientist": 1},
    "qa automation selenium testing": {"QA / Test Engineer": 2},
    "ux designer figma prototyping": {"UI / UX Designer": 2, "Frontend Developer": 1},
    "cloud engineer docker terraform": {"DevOps Engineer": 2},
    "machine learning engineer tensorflow python": {"Data Scientist": 2, "Python Developer": 1},
}
"""Synthetic relevance judgements: query -> category -> grade (other categories are 0)."""


def main(path: str, labels_path: str | None = None) -> None:
    roles = list(ROLES)
    categories: list[str] = []
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Name", "Category", "Resume_str"])
        for index in range(40):
            name = f"{FIRST[index % len(FIRST)]} {LAST[(index * 3) % len(LAST)]}"
            role = roles[index % len(roles)]
            categories.append(role)
            writer.writerow([name, role, resume(name, role, index)])
    if labels_path:
        with open(labels_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["query", "resume_id", "grade"])
            for query, grades in QUERIES.items():
                for resume_id, category in enumerate(categories):
                    writer.writerow([query, resume_id, grades.get(category, 0)])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
