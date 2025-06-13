#!/usr/bin/env python3

import argparse
import sqlite3
import os
import random
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
import pdfplumber

DB_FILE = "questions.db"


@dataclass
class Question:
    level: str
    subject: str
    text: str
    option1: str
    option2: str
    option3: str
    option4: str
    correct: int
    explanation: str


def init_db(db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            subject TEXT NOT NULL,
            text TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct INTEGER NOT NULL,
            explanation TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def add_question(q: Question, db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO questions
        (level, subject, text, option1, option2, option3, option4, correct, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            q.level,
            q.subject,
            q.text,
            q.option1,
            q.option2,
            q.option3,
            q.option4,
            q.correct,
            q.explanation,
        ),
    )
    conn.commit()
    conn.close()


def import_excel(path: str, db_path: str = DB_FILE):
    df = pd.read_excel(path)
    required_cols = [
        "level",
        "subject",
        "text",
        "option1",
        "option2",
        "option3",
        "option4",
        "correct",
        "explanation",
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
    for _, row in df.iterrows():
        q = Question(
            level=str(row["level"]),
            subject=str(row["subject"]),
            text=str(row["text"]),
            option1=str(row["option1"]),
            option2=str(row["option2"]),
            option3=str(row["option3"]),
            option4=str(row["option4"]),
            correct=int(row["correct"]),
            explanation=str(row["explanation"]),
        )
        add_question(q, db_path)


def parse_pdf(path: str, level: str, subject: str, db_path: str = DB_FILE):
    """Naively parse a PDF expecting each question to be in the form:
    1. Question text
    A) option1
    B) option2
    C) option3
    D) option4
    Answer: B
    Explanation: ...
    """
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = text.splitlines()
    current_q = None
    data = []
    options = []
    explanation = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() and line[1:3] == ". ":
            if current_q:
                if len(options) == 4:
                    data.append((current_q, options, correct, explanation))
            current_q = line[3:]
            options = []
            correct = 0
            explanation = ""
        elif line.startswith("A)") or line.startswith("B)") or line.startswith("C)") or line.startswith("D)"):
            options.append(line[3:].strip())
        elif line.startswith("Answer:"):
            letter = line.split(":", 1)[1].strip().upper()
            correct = {"A": 1, "B": 2, "C": 3, "D": 4}.get(letter, 0)
        elif line.startswith("Explanation:"):
            explanation = line.split(":", 1)[1].strip()
        else:
            if current_q:
                current_q += " " + line

    if current_q and len(options) == 4:
        data.append((current_q, options, correct, explanation))

    for qtext, opts, corr, expl in data:
        q = Question(level, subject, qtext, opts[0], opts[1], opts[2], opts[3], corr, expl)
        add_question(q, db_path)


def get_questions(subject: Optional[str], num: int, db_path: str = DB_FILE) -> List[Question]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    if subject:
        cur.execute(
            "SELECT level, subject, text, option1, option2, option3, option4, correct, explanation FROM questions WHERE subject=?",
            (subject,),
        )
    else:
        cur.execute(
            "SELECT level, subject, text, option1, option2, option3, option4, correct, explanation FROM questions"
        )
    rows = cur.fetchall()
    conn.close()
    random.shuffle(rows)
    rows = rows[:num]
    return [Question(*row) for row in rows]


def evaluate(subject: Optional[str], num: int, db_path: str = DB_FILE):
    questions = get_questions(subject, num, db_path)
    if not questions:
        print("No hay preguntas disponibles.")
        return
    score = 0
    for q in questions:
        print(f"\n{q.text}")
        print(f"1) {q.option1}")
        print(f"2) {q.option2}")
        print(f"3) {q.option3}")
        print(f"4) {q.option4}")
        ans = input("Tu respuesta (1-4): ")
        try:
            ans = int(ans)
        except ValueError:
            ans = 0
        if ans == q.correct:
            score += 1
            print("Correcto!")
        else:
            print(f"Incorrecto. {q.explanation}")
    print(f"\nResultado: {score}/{len(questions)} correctas")


def main():
    parser = argparse.ArgumentParser(description="Aplicación de exámenes")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init-db", help="Inicializa la base de datos")

    parser_excel = sub.add_parser("import-excel", help="Importa preguntas desde un archivo Excel")
    parser_excel.add_argument("path")

    parser_pdf = sub.add_parser("import-pdf", help="Extrae preguntas de un PDF")
    parser_pdf.add_argument("path")
    parser_pdf.add_argument("--level", required=True)
    parser_pdf.add_argument("--subject", required=True)

    parser_eval = sub.add_parser("evaluate", help="Evalúa a una persona")
    parser_eval.add_argument("--subject")
    parser_eval.add_argument("--num", type=int, default=5)

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "import-excel":
        import_excel(args.path)
    elif args.command == "import-pdf":
        parse_pdf(args.path, args.level, args.subject)
    elif args.command == "evaluate":
        evaluate(args.subject, args.num)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
