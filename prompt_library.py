# prompt_library.py

SOP_CONFIG = {
    "Question Bank (MCQ) Review": {
        "rubric": """
        Evaluate out of 100% and apply point deductions:
        - Subject Knowledge / Factual Errors (-30% max): Factually incorrect answers or wrong domain mapping.
        - Technical Errors (-30% max): Mismatch between the specified correct option letter and the actual answer text.
        - Clarity & Repetition (-20% max): Incomplete questions, confusing options, or repeated questions.
        - Grammar & Semantics (-10% max): Non-trivial grammatical or semantic errors.
        - Subject Mismatch (-10% max): Questions irrelevant to the core subject.
        """,
        "auto_fail": False,
    },
    "Subject Learning Material (SLM) Review": {
        "rubric": """
        Evaluate out of 100% and apply point deductions:
        - Inclusivity & Bias (-100% Auto-Fail): Racist, classist, casteist, sexist examples, or physical disability/offensive professional references.
        - Subject Knowledge (-30% max): Factual inaccuracies or wrongly explained concepts.
        - Missing Structure / TOC (-30% max): Missing Summary, Keywords, Self-Assessment Questions, References, or TOC mismatch.
        - Grammar & Repetition (-20% max): Major grammatical errors or duplicated paragraphs.
        - AI Terms / Naming Inconsistencies (-20% max): Words like 'ChatGPT'/'AI', or mismatched subject/e-book names.
        """,
        "auto_fail": True,
    },
    "PPT Checking": {
        "rubric": """
        Evaluate out of 100% and apply point deductions:
        - Missing Key Points from SLM (-50% max): Crucial source concepts omitted.
        - Factual Mistakes (-30% max): Contradicts verified source material.
        - Formatting & Tone Mismatch (-20% max): Tone and style inconsistent with presentation format.
        Provide exact slide headings and concise additions for any required improvements.
        """,
        "auto_fail": False,
    },
    "FAQs & Misconceptions Review": {
        "rubric": """
        Evaluate out of 100% and apply point deductions:
        - Sequence & Unit Skips (-40% max): Content not ordered unit-wise or units are skipped.
        - Factual Accuracy & Grammar (-30% max): Errors in validity or severe grammatical issues.
        - Misconception Labeling (-20% max): Categorizing misconceptions vaguely as 'Miscellaneous'.
        - AI Terminology (-10% max): Inclusion of words like 'ChatGPT', 'AI', etc.
        """,
        "auto_fail": False,
    },
    "Video Script Checking": {
        "rubric": """
        Evaluate out of 100% and apply point deductions:
        - Strict Avoidance (-100% Auto-Fail): Time-specific greetings (e.g., 'Good Morning'), discriminatory language, or offensive references.
        - Tone & Examples (-40% max): Not conversational, missing Indian audience context, or incomplete knowledge coverage.
        - Structure Missing (-30% max): Missing greeting, recap of previous session, transitions, or concluding summary.
        - Format Violations (-30% max): Uses bullet points, emojis, icons, or negative brand name mentions. Must be essay format.
        """,
        "auto_fail": True,
    },
    "Subjective Question Bank Review": {
        "rubric": """
        Evaluate out of 100% and apply point deductions:
        - Clarity, Relevance & Complexity (-30% max): Irrelevant questions, unclear phrasing, or misaligned difficulty/marks.
        - Answer Guidelines & Engagement (-30% max): Weak model answers, or questions relying on rote memorization over critical thinking.
        - Variety & Inclusivity (-20% max): Lack of question types, or biased/outdated examples.
        - Technicalities & Formatting (-20% max): Grammar errors, formatting issues, or invalid media upload permissions.
        """,
        "auto_fail": False,
    },
}