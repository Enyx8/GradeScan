import re

# Номер команды: только цифры (как в подсказке «например: 101»)
_TEAM_RE = re.compile(r"^\d{1,10}$")


def validate_fio_parts(parts: list[str]) -> tuple[bool, str]:
    """
    Фамилия и имя — не только цифры; в каждом из первых двух слов есть буква (RU/LAT).
    Отчество (если есть) — тоже не «только цифры», если непустое.
    """
    if len(parts) < 2:
        return False, "Укажите как минимум фамилию и имя через пробел."

    for i, label in ((0, "фамилия"), (1, "имя")):
        raw = parts[i].strip()
        if not raw:
            return False, f"Пустое поле ({label}). Введите ФИО заново."
        if raw.isdigit():
            return False, f"{label.capitalize()} не может состоять только из цифр. Укажите буквы (русские или латинские)."
        if not re.search(r"[A-Za-zА-Яа-яЁё]", raw):
            return False, f"В {label} должны быть буквы. Недопустимы только символы без букв."

    for extra in parts[2:]:
        t = extra.strip()
        if not t:
            continue
        if t.isdigit():
            return False, "Отчество не может состоять только из цифр."
        if not re.search(r"[A-Za-zА-Яа-яЁё]", t):
            return False, "В отчестве должны быть буквы или оставьте его пустым."

    return True, ""


def validate_team_code(team_raw: str) -> tuple[bool, str]:
    s = team_raw.strip()
    if not s:
        return False, "Введите номер команды (только цифры, например: 101)."
    if not _TEAM_RE.match(s):
        return (
            False,
            "Номер команды — только цифры, без букв и пробелов (например: 101). Попробуйте снова.",
        )
    return True, ""
