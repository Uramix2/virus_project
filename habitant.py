from random import choices, random, shuffle

# --- Paramètres ---
action_job = {"farmer": 35, "doctor": 3, "worker": 3, "jobless": 2}
action_personalities_for_sickness = {"strong": 6, "weak": 2, "rich": 5, "poor": 3, "normal": 4}
action_personalities_for_food = {"strong": 3, "weak": 3, "rich": 5, "poor": 1, "normal": 3}

# --- Classe Habitant ---
class Habitant:
    def __init__(self, age=25):
        self.etat = choices(["infect", "healthy"], weights=[80, 20])[0]
        self.perso = choices(["strong", "weak", "rich", "poor", "normal"], weights=[5, 5, 5, 10, 75])[0]
        self.job = choices(["farmer", "doctor", "worker", "jobless"], weights=[17, 5, 45, 8])[0] if age >= 15 else "none"
        self.age = age
        self.day_infect = 0
        self.at_the_doctor = False
        self.hospital_days = 0
        self.food_deficit = 0
        self.days_of_hunger = 0
        self.partner = None

# --- Former des couples ---
def form_couples(population, existing_couples):
    eligible = [h for h in population if h.partner is None and h.age >= 18]
    shuffle(eligible)
    new_couples = []
    i = 0
    while i < len(eligible) - 1:
        eligible[i].partner = eligible[i + 1]
        eligible[i + 1].partner = eligible[i]
        new_couples.append((eligible[i], eligible[i + 1]))
        i += 2
    valid_couples = [(p1, p2) for p1, p2 in existing_couples if p1 in population and p2 in population]
    return valid_couples + new_couples

# --- Gérer les naissances ---
def handle_births(population, satisfaction, jour, couples, nourriture, consommation):
    births = []
    eligible_couples = [(p1, p2) for p1, p2 in couples]
    if satisfaction > 30:
        proba_birth = 0.05 if nourriture < consommation else 0.2
        if len(population) > 1000:
            proba_birth /= 10
        for parent1, parent2 in eligible_couples:
            if random() < proba_birth:
                child = Habitant(age=0)
                population.append(child)
                births.append((jour, child.perso, child.job))
    return population, births

# --- Morts naturelles ---
def check_natural_death(population, jour, deaths_today):
    for h in population[:]:
        if 10 <= h.age <= 100:
            proba = 0.0005 if h.age < 60 else (0.0005 + (h.age - 60) / 40 * 0.0095)
            if random() < proba:
                deaths_today.append((jour, h.job, h.perso, h.day_infect, h.at_the_doctor, h.hospital_days, "naturel"))
                if h.partner:
                    h.partner.partner = None
                population.remove(h)
    return population, deaths_today

# --- Mise à jour nourriture ---
def update_food(population, nourriture):
    production = sum(action_job["farmer"] for h in population if h.job == "farmer")
    consommation = sum(action_personalities_for_food[h.perso] + (action_job[h.job] if h.job in ["worker", "jobless"] else 0) for h in population)
    nourriture += production
    return nourriture, consommation

# --- Distribution nourriture ---
def distribute_food(population, nourriture):
    for h in population:
        h.daily_need = action_personalities_for_food[h.perso] + (action_job[h.job] if h.job in ["worker", "jobless"] else 0)
    priority_groups = [
        [h for h in population if h.perso == "rich"],
        [h for h in population if h.job in ["doctor", "farmer", "worker"]],
        [h for h in population if h.job == "jobless"],
        [h for h in population if h.perso == "poor"]
    ]
    mal_nourris = 0
    for group in priority_groups:
        for h in group:
            if nourriture >= h.daily_need:
                nourriture -= h.daily_need
                h.days_of_hunger = 0
                h.food_deficit = 0
            else:
                deficit = h.daily_need - nourriture
                nourriture = 0
                h.food_deficit += deficit
                h.days_of_hunger += 1
                mal_nourris += 1
    return nourriture, mal_nourris

# --- Mort de faim ---
def check_starvation(population, jour, deaths_today):
    for h in population[:]:
        if h.days_of_hunger >= 7 and h.food_deficit > 10:
            deaths_today.append((jour, h.job, h.perso, 0, False, 0, "faim"))
            if h.partner:
                h.partner.partner = None
            population.remove(h)
    return population, deaths_today

# --- Mise à jour statuts sociaux ---
def update_status_changes(population, satisfaction, satisfaction_previous):
    status_changes = []
    for h in population:
        if h.job == "worker" and random() < 0.01:
            h.job = "jobless"
            status_changes.append(f"Worker -> Jobless : Perso: {h.perso}")
        if h.job == "jobless" and h.age >= 15 and random() < 0.05:
            new_job = choices(["doctor", "farmer", "worker"], weights=[1, 30, 69])[0]
            h.job = new_job
            status_changes.append(f"Jobless -> {new_job} : Perso: {h.perso}")
        if h.job == "none" and h.age >= 15:
            h.job = choices(["farmer", "doctor", "worker", "jobless"], weights=[17, 5, 45, 8])[0]
            status_changes.append(f"None -> {h.job} : Perso: {h.perso}")
        if h.perso == "poor" and random() < 0.05:
            h.perso = "normal"
            status_changes.append(f"Poor -> Normal : Métier: {h.job}")
        if h.perso == "rich":
            proba = (100 - satisfaction) / 100 * 0.1 + (0.05 if satisfaction < satisfaction_previous else 0)
            if random() < proba:
                h.perso = "normal"
                status_changes.append(f"Rich -> Normal : Métier: {h.job}")
        if h.perso == "normal":
            proba = satisfaction / 100 * 0.05 + (0.05 if satisfaction > satisfaction_previous else 0)
            if random() < proba:
                h.perso = "rich"
                status_changes.append(f"Normal -> Rich : Métier: {h.job}")
    return population, status_changes

# --- Mise à jour maladies ---
def update_disease(population, jour, deaths_today):
    for h in population[:]:
        if h.etat == "infect":
            h.day_infect += 1
            if h.at_the_doctor:
                h.hospital_days += 1
            if h.day_infect > action_personalities_for_sickness[h.perso]:
                deaths_today.append((jour, h.job, h.perso, h.day_infect, h.at_the_doctor, h.hospital_days, "infection"))
                if h.partner:
                    h.partner.partner = None
                population.remove(h)
    return population, []

# --- Mise à jour docteurs ---
def update_doctor(population, jour, visits_today):
    nb_doctor = sum(1 for h in population if h.job == "doctor")
    visits_today = []
    if nb_doctor > 0 and jour > 2:
        nb_visits = nb_doctor * action_job["doctor"]
        for h in [h for h in population if h.etat == "infect" and h.at_the_doctor]:
            if nb_visits <= 0:
                break
            proba_success = max(0, 0.80 - (h.day_infect - 1) * 0.10)
            if random() < proba_success:
                h.etat = "healthy"
                h.day_infect = 0
                h.at_the_doctor = False
                h.hospital_days = 0
            nb_visits -= 1
        if nb_visits > 0:
            for h in [h for h in population if h.etat == "infect" and not h.at_the_doctor]:
                prob_to_see_doctor = min(1, 0.30 + (h.day_infect - 1) * 0.10)
                if random() < prob_to_see_doctor:
                    h.at_the_doctor = True
                    h.hospital_days = 1
                    visits_today.append((h.job, h.perso, h.day_infect))
                    nb_visits -= 1
    return population, visits_today, nb_doctor

# --- Calcul satisfaction ---
def calculate_satisfaction(satisfaction, consommation, nourriture, deaths_today, nb_hospitalises, nb_doctor, population, mal_nourris):
    deficit = max(0, consommation - nourriture)
    deficit_ratio = deficit / consommation if consommation > 0 else 0
    surplus = max(0, nourriture - consommation)
    surplus_ratio = surplus / consommation if consommation > 0 else 0
    mortalite_ratio = len(deaths_today) / len(population) if population else 0
    capacite_docteurs = nb_doctor * action_job["doctor"]
    hospitalisation_ratio = nb_hospitalises / capacite_docteurs if capacite_docteurs > 0 else 0
    nourriture_impact = (5 + 2 * surplus_ratio) if deficit_ratio == 0 else -5 * deficit_ratio * (1.2 if deficit_ratio > 0.3 else 1)
    mortalite_impact = -25 * mortalite_ratio
    hospitalisation_impact = -15 * hospitalisation_ratio
    mal_nourris_impact = -0.5 * mal_nourris
    amortissement = 1 if satisfaction < 50 else (-2 if satisfaction > 90 else 0)
    seuil_critique = 1.2 if satisfaction < 30 else 1.0
    delta_s = (nourriture_impact + mortalite_impact + hospitalisation_impact + mal_nourris_impact + amortissement) * seuil_critique
    return max(0, min(100, satisfaction + delta_s))

# --- Simulation d'un jour ---
def simulate_day(population, nourriture, satisfaction, jour, satisfaction_previous, couples):
    deaths_today = []
    visits_today = []
    status_changes = []
    births = []

    for h in population:
        h.age += 1

    couples = form_couples(population, couples)
    population, deaths_today = check_natural_death(population, jour, deaths_today)
    nourriture, consommation = update_food(population, nourriture)
    population, births = handle_births(population, satisfaction, jour, couples, nourriture, consommation)
    population, status_changes = update_status_changes(population, satisfaction, satisfaction_previous)
    nourriture, mal_nourris = distribute_food(population, nourriture)
    population, deaths_starvation = check_starvation(population, jour, deaths_today)
    deaths_today.extend(deaths_starvation)
    population, deaths_disease = update_disease(population, jour, deaths_today)
    deaths_today.extend(deaths_disease)
    population, visits_today, nb_doctor = update_doctor(population, jour, visits_today)
    nb_hospitalises = sum(1 for h in population if h.at_the_doctor)
    satisfaction = calculate_satisfaction(satisfaction, consommation, nourriture, deaths_today, nb_hospitalises, nb_doctor, population, mal_nourris)

    return population, nourriture, satisfaction, deaths_today, visits_today, status_changes, births, couples


# --- Test simulation ---
pop = [Habitant(age=25) for _ in range(150)]
nourriture = 2000
satisfaction = 80
jours = 100

couples = form_couples(pop, [])
print("\n╔════════════════════════════════════════════════════╗")
print(" 🎬   SIMULATION LANCÉE")
print(f" 👥 Couples initiaux : {len(couples)}")
print("╚════════════════════════════════════════════════════╝\n")

deaths_log = []
visits_log = []
status_changes_log = []
births_log = []
satisfaction_previous = satisfaction

for jour in range(1, jours + 1):
    pop, nourriture, satisfaction, deaths_today, visits_today, status_changes, births, couples = simulate_day(
        pop, nourriture, satisfaction, jour, satisfaction_previous, couples
    )
    deaths_log.extend(deaths_today)
    visits_log.extend(visits_today)
    status_changes_log.extend(status_changes)
    births_log.extend(births)
    satisfaction_previous = satisfaction

    if jour % 5 == 0:
        jobs = {"farmer": 0, "doctor": 0, "worker": 0, "jobless": 0, "none": 0}
        etats = {"infect": 0, "healthy": 0}
        persos = {"strong": 0, "weak": 0, "rich": 0, "poor": 0, "normal": 0}
        chez_le_docteur = 0
        for h in pop:
            jobs[h.job] += 1
            etats[h.etat] += 1
            persos[h.perso] += 1
            if h.at_the_doctor:
                chez_le_docteur += 1

        print("════════════════════════════════════════════════════")
        print(f" 📊 JOUR {jour} - BILAN")
        print("────────────────────────────────────────────────────")
        print(f" 👥 Population : {len(pop)}   |   💞 Couples : {len(couples)}")
        print(f" 🍖 Nourriture : {nourriture:.0f}   |   😊 Satisfaction : {satisfaction:.0f}")
        print("────────────────────────────────────────────────────")
        print(f" 🩺 Santé : {etats}   |   👨‍⚕️ Patients : {chez_le_docteur}")
        print(f" 🏭 Métiers : {jobs}")
        print(f" 💡 Personnalités : {persos}")
        print("────────────────────────────────────────────────────")
        if deaths_today:
            print(f" ⚰️ Décès aujourd'hui : {len(deaths_today)}")
        if visits_today:
            print(f" 🩺 Visites médecin : {len(visits_today)}")
        if status_changes:
            print(f" 🔄 Changements : {len(status_changes)}")
        if births:
            print(f" 👶 Naissances : {len(births)}")
        else:
            print(" 😔 Aucune naissance")
        print("════════════════════════════════════════════════════\n")

    else:
        nb_infectes = sum(1 for h in pop if h.etat == "infect")
        print(f" Jour {jour:3} → 👥 {len(pop)} | 🦠 Infectés : {nb_infectes} | ⚰️ Morts : {len(deaths_today)}")


        
# --- Rapport Final ---
print(f"\n🏁 FIN DE SIMULATION")
print(f"--- Bilan Final ---")

# Total décès
print(f"⚰️ Décès totaux: {len(deaths_log)}")

# Comptage par cause
causes = {"infection": 0, "faim": 0, "naturel": 0, "autre": 0}
for death in deaths_log:
    cause = death[-1]
    if cause in causes:
        causes[cause] += 1
    else:
        causes["autre"] += 1

print("📊 Causes des décès:")
for cause, count in causes.items():
    print(f"   - {cause}: {count}")

# Autres stats
print(f"🩺 Visites médecin: {len(visits_log)}")

conversions = {
    "Worker -> Jobless": 0, "Jobless -> Doctor": 0, "Jobless -> Farmer": 0, "Jobless -> Worker": 0,
    "None -> Farmer": 0, "None -> Doctor": 0, "None -> Worker": 0, "None -> Jobless": 0,
    "Poor -> Normal": 0, "Rich -> Normal": 0, "Normal -> Rich": 0
}
for change in status_changes_log:
    for conv in conversions:
        if change.startswith(conv):
            conversions[conv] += 1

print("🔄 Conversions:")
for conv, count in conversions.items():
    if count > 0:
        print(f"   - {conv}: {count}")

print(f"👶 Naissances totales: {len(births_log)}")