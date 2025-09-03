import pygame
from habitant_final import Habitant, form_couples, simulate_day

# --- Pygame init ---
pygame.init()
SCREEN = pygame.display.set_mode((1720, 880))
pygame.display.set_caption("Virus_Sim")
CLOCK = pygame.time.Clock()


def render_population(population, screen):
    """
    function that displays the result 
    in graphical form using pygame   
    
    Arguments: population, screen
    Return: display 
    """
    
    width, height = screen.get_size()

    # --- Cyan/blue gradient background ---
    for y in range(height):
        r = 100 + (y // 15) * 1  
        g = 150 - (y // 20) * 2  
        b = 255 - (y // 10) * 1  
        r = min(150, max(100, r))  
        g = min(150, max(50, g))   
        b = min(255, max(50, b))  
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))

    # --- Legend area (bottom-right) ---
    legend_w, legend_h = 260, 200
    legend_x, legend_y = width - legend_w - 20, height - legend_h - 20
    legend_rect = pygame.Rect(legend_x, legend_y, legend_w, legend_h)

    # --- Draw residents ---
    for r in population:
        pos = (r.x, r.y)

        # If a resident spawns under the legend, draw it slightly above
        if legend_rect.collidepoint(pos):
            pos = (r.x, r.y - legend_h - 10)

        # Color by job/state
        if r.state == "infect":
            color = (220, 20, 60)     # red
        elif r.job == "farmer":
            color = (255, 215, 0)     # yellow
        elif r.job == "doctor":
            color = (34, 139, 34)     # green
        elif r.job == "worker":
            color = (65, 105, 225)    # blue
        elif r.job == "jobless":
            color = (128, 128, 128)   # gray
        else:
            color = (255, 140, 0)     # orange

        # Radius by age bucket (tiny stylistic cue)
        radius = 3 if r.age < 12 else 5 if r.age < 60 else 4

        # Soft halo for infected
        if r.state == "infect":
            pygame.draw.circle(screen, (255, 160, 160), pos, radius + 4)

        # Outline + fill
        pygame.draw.circle(screen, (0, 0, 0), pos, radius + 1)
        pygame.draw.circle(screen, color, pos, radius)

    # --- Legend ---
    font = pygame.font.SysFont("Segoe UI", 20, bold=True)
    items = [
        ("Infected",   (220, 20, 60)),
        ("Farmer",     (255, 215, 0)),
        ("Doctor",     (34, 139, 34)),
        ("Worker",     (65, 105, 225)),
        ("Jobless",    (128, 128, 128)),
        ("Child",      (255, 140, 0)),
    ]

    legend_surf = pygame.Surface((legend_w, legend_h), pygame.SRCALPHA)
    legend_surf.fill((0, 120, 180, 180))  # semi-transparent cyan/blue

    y = 10
    for text, col in items:
        pygame.draw.circle(legend_surf, col, (15, y + 10), 8)
        label = font.render(text, True, (240, 240, 255))
        legend_surf.blit(label, (35, y))
        y += 30

    screen.blit(legend_surf, (legend_x, legend_y))
    pygame.display.flip()


# --- Simulation test ---
def main():
    """
    Function test who displays the simulation result in the console + with pygame
    """
    
    population = [Habitant(age=25) for _ in range(100)]
    food = 0
    satisfaction = 50
    total_days = 100

    couples = form_couples(population, [])
    print("\n╔════════════════════════════════════════════╗")
    print(" 🎬   SIMULATION STARTED")
    print(f" 💞 Initial couples: {len(couples)}")
    print("╚════════════════════════════════════════════╝\n")

    deaths_log = []
    visits_log = []
    status_changes_log = []
    births_log = []
    satisfaction_prev = satisfaction

    running = True
    day = 1

    while day <= total_days and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        (population, food, satisfaction, deaths_today,
         visits_today, status_changes, births, couples) = simulate_day(
            population, food, satisfaction, day, satisfaction_prev, couples
        )

        deaths_log.extend(deaths_today)
        visits_log.extend(visits_today)
        status_changes_log.extend(status_changes)
        births_log.extend(births)
        satisfaction_prev = satisfaction

        # Console snapshot every 5 days
        if day % 5 == 0:
            jobs = {"farmer": 0, "doctor": 0, "worker": 0, "jobless": 0, "none": 0}
            states = {"infect": 0, "healthy": 0}
            personas = {"strong": 0, "weak": 0, "rich": 0, "poor": 0, "normal": 0}
            at_hospital = 0
            for r in population:
                jobs[r.job] += 1
                states[r.state] += 1
                personas[r.persona] += 1
                if r.at_hospital:
                    at_hospital += 1

            print("════════════════════════════════════════════")
            print(f" 📊 DAY {day} - SNAPSHOT")
            print("────────────────────────────────────────────")
            print(f" 👥 Pop: {len(population)}   |   💞 Couples: {len(couples)}")
            print(f" 🍖 Food: {int(food)}        |   😊 Satisf.: {int(satisfaction)}")
            print("────────────────────────────────────────────")
            print(f" 🩺 States : {states}   |   👨‍⚕️ Patients: {at_hospital}")
            print(f" 🏭 Jobs   : {jobs}")
            print(f" 💡 Persona: {personas}")
            print("────────────────────────────────────────────")
            if deaths_today:
                print(f" ⚰️ Deaths today: {len(deaths_today)}")
            if visits_today:
                print(f" 🩺 Doctor visits: {len(visits_today)}")
            if status_changes:
                print(f" 🔄 Status changes: {len(status_changes)}")
            if births:
                print(f" 👶 Births: {len(births)}")
            else:
                print(" 😔 No births")
            print("════════════════════════════════════════════\n")
        else:
            nb_infected = sum(1 for r in population if r.state == "infect")
            print(f" Day {day:3} → 👥 {len(population)} | 🦠 Infected: {nb_infected} | ⚰️ Deaths: {len(deaths_today)}")

        # Draw
        render_population(population, SCREEN)
        CLOCK.tick(4) # fps for days in simulation
        day += 1

    # Final report
    print("\n🏁 END OF SIMULATION")
    print("--- Final Report ---")
    print(f"⚰️ Total deaths: {len(deaths_log)}")

    causes = {"infection": 0, "starvation": 0, "natural": 0, "other": 0}
    for death in deaths_log:
        cause = death[-1]
        if cause in causes:
            causes[cause] += 1
        else:
            causes["other"] += 1

    print("📊 Causes of death:")
    for cause, count in causes.items():
        print(f"   - {cause}: {count}")

    print(f"🩺 Doctor visits: {len(visits_log)}")

    conversions = {
        "Worker -> Jobless": 0, "Jobless -> Doctor": 0, "Jobless -> Farmer": 0, "Jobless -> Worker": 0,
        "None -> Farmer": 0, "None -> Doctor": 0, "None -> Worker": 0, "None -> Jobless": 0,
        "Poor -> Normal": 0, "Rich -> Normal": 0, "Normal -> Rich": 0
    }
    for change in status_changes_log:
        for key in conversions:
            if change.startswith(key):
                conversions[key] += 1

    print("🔄 Conversions:")
    for key, count in conversions.items():
        if count > 0:
            print(f"   - {key}: {count}")

    print(f"👶 Total births: {len(births_log)}")

    pygame.quit()


if __name__ == "__main__":
    main()
