"""Generate data/sample_resumes.csv: 40 synthetic, mixed-case resumes (no real people)."""

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


def main(path: str) -> None:
    roles = list(ROLES)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Name", "Category", "Resume_str"])
        for index in range(40):
            name = f"{FIRST[index % len(FIRST)]} {LAST[(index * 3) % len(LAST)]}"
            role = roles[index % len(roles)]
            writer.writerow([name, role, resume(name, role, index)])


if __name__ == "__main__":
    main(sys.argv[1])
