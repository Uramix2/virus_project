from random import choices, random, shuffle
from math import sqrt

# --- Simulation settings ---
JOB_ACTION = {"farmer": 35, "doctor": 3,"worker": 3, "jobless": 2}  # farmer produces 35 food units/day, doctor can treat 3 ppl/day
HEALTH_TTL_BY_PERSONA = {"strong": 7, "weak": 3, "rich": 8, "poor": 4, "normal": 5}  # days before death if infected
DAILY_NEED_BY_PERSONA_AND_JOB = {
    "strong": 3, "weak": 3, "rich": 5, "poor": 1, "normal": 3,
    "worker": 3, "jobless": 2
}

# --- hanitant class ---
class Habitant:
    def __init__(self, age: int = 25):
        """
        Initialize a habitant with:
        - infection state, persona, job, age
        - hospital-related fields
        - food shortage tracking
        - partner
        - spawn position (screen-space)
        """
        self.state = choices(["infect", "healthy"], weights=[1, 99])[0]
        self.persona = choices(["strong", "weak", "rich", "poor", "normal"],
                               weights=[5, 5, 5, 10, 75])[0]
        self.job = choices(["farmer", "doctor", "worker", "jobless"],
                           weights=[17, 5, 45, 8])[0] if age >= 15 else "none"
        self.age = age

        # Disease / hospital
        self.days_infected = 0
        self.at_hospital = False
        self.hospital_days = 0

        # Food tracking
        self.food_deficit = 0
        self.days_hungry = 0

        # Social
        self.partner = None

        # Position (adapt as needed to avoid your legend zone)
        self.x = int(random() * 1720)
        self.y = int(random() * 860)


# --- Couple formation ---
def form_couples(population, existing_couples):
    """
    Pair up residents who are >=18 and currently single.
    Returns old valid couples + newly formed ones.

    Argments: population, existing_couples
    Returns: valid_old + new_couples
    """
    eligible = [r for r in population if r.partner is None and r.age >= 18]
    shuffle(eligible)

    new_couples = []
    i = 0
    while i < len(eligible) - 1:
        eligible[i].partner = eligible[i + 1]
        eligible[i + 1].partner = eligible[i]
        new_couples.append((eligible[i], eligible[i + 1]))
        i += 2

    valid_old = [(a, b) for a, b in existing_couples if a in population and b in population]
    return valid_old + new_couples


# --- Births ---
def handle_births(population, satisfaction, day, couples, food, consumption):
    """
    Decide births when satisfaction is decent. Probability depends on food balance.
    Returns (population, births_log).

    Argments: population, satisfaction, day, couples, food, consumption
    Returns: population, births
    """
    births = []
    if satisfaction > 30:
        p_birth = 0.05 if food < consumption else 0.2
        if len(population) > 1000:
            p_birth /= 10

        for p1, p2 in couples:
            if random() < p_birth:
                child = Habitant(age=0)
                population.append(child)
                births.append((day, child.persona, child.job))
    return population, births


# --- Unified deaths (natural + starvation) ---
def check_deaths(population, day, deaths_today):
    """
    Remove residents who die either from:
      - natural death (age-based probability)
      - starvation (too many hungry days + deficit)
    Appends a record to deaths_today and unlinks partners.

    Argments: population, day, deaths_today
    Returns: population, deaths_today
    """
    for r in population[:]:
        cause = None

        # Natural death (independent of starvation)
        if 10 <= r.age <= 100:
            p = 0.0005 if r.age < 60 else (0.0005 + (r.age - 60) / 40 * 0.0095)
            if random() < p:
                cause = "natural"

        # Starvation death
        if r.days_hungry >= 7 and r.food_deficit > 10:
            cause = "starvation"

        if cause:
            deaths_today.append(
                (day, r.job, r.persona, getattr(r, "days_infected", 0),
                 getattr(r, "at_hospital", False), getattr(r, "hospital_days", 0),
                 cause)
            )
            if r.partner:
                r.partner.partner = None
            population.remove(r)

    return population, deaths_today


# --- Food production & consumption ---
def update_food(population, food):
    """
    Update food for population

    Arguments: population, food
    Returns: new_food_stock, total_consumption_for_the_day).
    """
    production = sum(JOB_ACTION["farmer"] for r in population if r.job == "farmer")
    consumption = sum(
        DAILY_NEED_BY_PERSONA_AND_JOB[r.persona] +
        (JOB_ACTION[r.job] if r.job in ["worker", "jobless"] else 0)
        for r in population
    )
    food += production
    return food, consumption


# --- Food distribution (priority-based) ---
def distribute_food(population, food):
    """
    Distribute food by priority groups.

    Argments: population, food
    Returns: food, underfed
    """
    for r in population:
        r.daily_need = DAILY_NEED_BY_PERSONA_AND_JOB[r.persona] + \
                       (JOB_ACTION[r.job] if r.job in ["worker", "jobless"] else 0)

    priority_groups = [
        [r for r in population if r.persona == "rich"],
        [r for r in population if r.job in ["doctor", "farmer", "worker"]],
        [r for r in population if r.job == "jobless"],
        [r for r in population if r.persona == "poor"]
    ]

    underfed = 0
    for group in priority_groups:
        for r in group:
            if food >= r.daily_need:
                food -= r.daily_need
                r.days_hungry = 0
                r.food_deficit = 0
            else:
                deficit = r.daily_need - food
                food = 0
                r.food_deficit += deficit
                r.days_hungry += 1
                underfed += 1
    return food, underfed


# --- Social status changes ---
def update_status_changes(population, satisfaction, satisfaction_prev):
    """
    Random transitions between jobs/personas based on satisfaction trends.

    Argments: population, satisfaction, satisfaction_prev
    Returns: population, changes

    """
    changes = []
    for r in population:
        if r.job == "worker" and random() < 0.01:
            r.job = "jobless"
            changes.append(f"Worker -> Jobless : Persona: {r.persona}")

        if r.job == "jobless" and r.age >= 15 and random() < 0.05:
            new_job = choices(["doctor", "farmer", "worker"], weights=[1, 30, 69])[0]
            r.job = new_job
            changes.append(f"Jobless -> {new_job} : Persona: {r.persona}")

        if r.job == "none" and r.age >= 15:
            r.job = choices(["farmer", "doctor", "worker", "jobless"], weights=[17, 5, 45, 8])[0]
            changes.append(f"None -> {r.job} : Persona: {r.persona}")

        if r.persona == "poor" and random() < 0.05:
            r.persona = "normal"
            changes.append(f"Poor -> Normal : Job: {r.job}")

        if r.persona == "rich":
            p = (100 - satisfaction) / 100 * 0.1 + (0.05 if satisfaction < satisfaction_prev else 0)
            if random() < p:
                r.persona = "normal"
                changes.append(f"Rich -> Normal : Job: {r.job}")

        if r.persona == "normal":
            p = satisfaction / 100 * 0.05 + (0.05 if satisfaction > satisfaction_prev else 0)
            if random() < p:
                r.persona = "rich"
                changes.append(f"Normal -> Rich : Job: {r.job}")

    return population, changes


# --- Disease update (death by infection threshold) ---
def update_disease(population, day, deaths_today):
    """
    Infected residents progress one day; if they exceed their TTL, they die.

    Argments: population, day, deaths_today 
    Returns: population, []
    """
    for r in population[:]:
        if r.state == "infect":
            r.days_infected += 1
            if r.at_hospital:
                r.hospital_days += 1
            if r.days_infected > HEALTH_TTL_BY_PERSONA[r.persona]:
                deaths_today.append(
                    (day, r.job, r.persona, r.days_infected, r.at_hospital, r.hospital_days, "infection")
                )
                if r.partner:
                    r.partner.partner = None
                population.remove(r)
    return population, []


# --- Doctors visits & cures ---
def update_doctor(population, day, visits_today):
    """
    Doctors attend a number of visits per day; some infected are cured.

    Argments: population, day, visits_today
    Returns: population, visits_today, nb_doctors
    """
    nb_doctors = sum(1 for r in population if r.job == "doctor")
    visits_today = []

    if nb_doctors > 0 and day > 2:
        capacity = nb_doctors * JOB_ACTION["doctor"]

        # Treat already hospitalized first
        for r in [x for x in population if x.state == "infect" and x.at_hospital]:
            if capacity <= 0:
                break
            success = max(0, 0.80 - (r.days_infected - 1) * 0.10)
            if random() < success:
                r.state = "healthy"
                r.days_infected = 0
                r.at_hospital = False
                r.hospital_days = 0
            capacity -= 1

        # Then send new infected to hospital
        if capacity > 0:
            for r in [x for x in population if x.state == "infect" and not x.at_hospital]:
                prob_to_visit = min(1, 0.30 + (r.days_infected - 1) * 0.10)
                if random() < prob_to_visit:
                    r.at_hospital = True
                    r.hospital_days = 1
                    visits_today.append((r.job, r.persona, r.days_infected))
                    capacity -= 1
                if capacity <= 0:
                    break

    return population, visits_today, nb_doctors


# --- Satisfaction scoring ---
def calculate_satisfaction(satisfaction, consumption, food, deaths_today,
                           nb_hospitalized, nb_doctors, population, underfed_count):
    """
    Aggregate score influenced by food balance, mortality, hospital load, hunger.
    
    Argments: satisfaction, consumption, food, deaths_today,
    nb_hospitalized, nb_doctors, population, underfed_count

    Returns: new satisfaction in [0, 100]

    """
    deficit = max(0, consumption - food)
    deficit_ratio = deficit / consumption if consumption > 0 else 0
    surplus = max(0, food - consumption)
    surplus_ratio = surplus / consumption if consumption > 0 else 0

    mortality_ratio = len(deaths_today) / len(population) if population else 0
    capacity_doctors = nb_doctors * JOB_ACTION["doctor"]
    hospital_ratio = nb_hospitalized / capacity_doctors if capacity_doctors > 0 else 0

    food_impact = (5 + 2 * surplus_ratio) if deficit_ratio == 0 else -5 * deficit_ratio * (1.2 if deficit_ratio > 0.3 else 1)
    mortality_impact = -25 * mortality_ratio
    hospital_impact = -15 * hospital_ratio
    underfed_impact = -0.5 * underfed_count

    damping = 1 if satisfaction < 50 else (-2 if satisfaction > 90 else 0)
    critical = 1.2 if satisfaction < 30 else 1.0

    delta = (food_impact + mortality_impact + hospital_impact + underfed_impact + damping) * critical
    return max(0, min(100, satisfaction + delta))


# --- One-day simulation ---
def simulate_day(population, food, satisfaction, day, satisfaction_prev, couples):
    """
    Runs one full day of the simulation
    
    Argments: population, food, satisfaction, day, satisfaction_prev, couples

    Returns: population, food, satisfaction, deaths_today, visits_today, 
    status_changes, births, couples
    """
    deaths_today = []
    visits_today = []
    status_changes = []
    births = []

    # Age everyone by 1 day (or 1 unit)
    for r in population:
        r.age += 1

    couples = form_couples(population, couples)
    population, deaths_today = check_deaths(population, day, deaths_today)

    food, consumption = update_food(population, food)
    population, births = handle_births(population, satisfaction, day, couples, food, consumption)

    population, status_changes = update_status_changes(population, satisfaction, satisfaction_prev)

    food, underfed = distribute_food(population, food)

    # Local virus transmission based on distance
    transmissions = 0
    to_infect = []
    for a in population:
        if a.state == "infect":
            for b in population:
                if b.state == "healthy" and b not in to_infect:
                    dist = sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
                    if dist < 45 and random() < 0.45:
                        to_infect.append(b)
                        transmissions += 1
    for r in to_infect:
        r.state = "infect"
        r.days_infected = 1
    print(f"Day {day} : {transmissions} transmissions")

    population, deaths_disease = update_disease(population, day, deaths_today)
    deaths_today.extend(deaths_disease)

    population, visits_today, nb_doctors = update_doctor(population, day, visits_today)
    nb_hospitalized = sum(1 for r in population if r.at_hospital)

    satisfaction = calculate_satisfaction(
        satisfaction, consumption, food, deaths_today,
        nb_hospitalized, nb_doctors, population, underfed
    )

    return population, food, satisfaction, deaths_today, visits_today, status_changes, births, couples



# --- TEST FONCTION ---


if __name__ == "__main__":
    from random import seed
    seed(42)  # makes the run deterministic for testing

    # Initial population
    population = [Habitant(age=25) for _ in range(50)]
    food = 500
    satisfaction = 70
    day = 1
    couples = form_couples(population, [])

    print("=== TEST SIMULATION (running model.py directly) ===")
    print(f"Initial population: {len(population)} | Food: {food} | Satisfaction: {satisfaction}")

    # Simulate 5 days
    for _ in range(5):
        population, food, satisfaction, deaths, visits, status_changes, births, couples = simulate_day(
            population, food, satisfaction, day, satisfaction, couples
        )
        print(f"Day {day}: 👥 {len(population)} | 🍖 {food:.0f} | 😊 {satisfaction:.1f} | ⚰️ {len(deaths)} deaths | 👶 {len(births)} births")
        day += 1

    print("=== END OF TEST ===")

