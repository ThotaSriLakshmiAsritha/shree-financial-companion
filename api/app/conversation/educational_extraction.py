def extract_educational_concept(message: str) -> str | None:
    normalized = message.casefold()
    if any(
        term in normalized
        for term in (
            "budget",
            "बजट",
            "బడ్జెట్",
            "school expense",
            "set aside",
            "kept money aside",
            "unnecessary purchase",
        )
    ):
        return "budgeting"
    if any(term in normalized for term in ("loan", "interest", "emi", "వడ్డీ", "ब्याज")):
        return "loan_interest"
    if any(term in normalized for term in ("saving", "save money", "बचत", "పొదుపు")):
        return "saving"
    return None
