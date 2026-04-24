import random
from typing import Iterator, List, Dict, Any
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import bcrypt

def get_random_date_in_range(
    rng: random.Random,
    start_year: int,
    end_year: int,
    start_month_day: tuple[int, int] = (1, 1),
    end_month_day: tuple[int, int] = (12, 31)
) -> datetime:
    """
    Returns a deterministic random datetime within the given MMDDYY bounds.
    """
    # Safe fallback if month/day is invalid for a specific year
    try:
        start_dt = datetime(start_year, start_month_day[0], start_month_day[1], tzinfo=timezone.utc)
    except ValueError:
        start_dt = datetime(start_year, 1, 1, tzinfo=timezone.utc)

    try:
        end_dt = datetime(end_year, end_month_day[0], end_month_day[1], 23, 59, 59, tzinfo=timezone.utc)
    except ValueError:
        # Month/day might be invalid for this year (e.g. Feb 29)
        end_dt = datetime(end_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    
    delta_seconds = int((end_dt - start_dt).total_seconds())
        
    random_second = rng.randint(0, delta_seconds)
    return start_dt + timedelta(seconds=random_second)

def chunked(items: list, size: int) -> Iterator[list]:
    """Yields successive chunks of `size` from `items`."""
    for i in range(0, len(items), size):
        yield items[i:i + size]

def hash_passwords_parallel(passwords: List[str], rounds: int = 6, workers: int = 10) -> List[str]:
    """
    Hashes a list of passwords concurrently.
    We use a lower rounds value (e.g., 6) for seeding to speed it up.
    """
    def _hash(pw: str) -> str:
        return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")
        
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_hash, passwords))

def pick_colleges(rng: random.Random, dataset: Dict[str, List[str]], n_colleges: int, min_programs: int = 1) -> Dict[str, List[str]]:
    """
    Randomly selects N colleges and a random subset of their programs.
    Returns a dict of {college_name: [program_names]}.
    """
    available_colleges = list(dataset.keys())
    # Deterministic choice
    selected_colleges = rng.sample(available_colleges, min(n_colleges, len(available_colleges)))
    
    result = {}
    for college in selected_colleges:
        programs = dataset[college]
        # Ensure min_programs respects actual array bounds
        safe_min = min(len(programs), max(1, min_programs))
        num_programs = rng.randint(safe_min, len(programs))
        result[college] = rng.sample(programs, num_programs)
        
    return result

def is_absent(rng: random.Random, base_prob: float = 0.2) -> bool:
    """
    Rolls a probability for whether a student is absent.
    In real use, you'd vary base_prob per student.
    """
    return rng.random() <= base_prob

def apply_suffix(rng: random.Random, name: str, suffixes: List[str], probability: float) -> str:
    """Applies a suffix to a name with the given probability."""
    if rng.random() <= probability:
        return f"{name} {rng.choice(suffixes)}"
    return name
