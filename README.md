# 🦠 Virus Simulation Project

This project simulates the spread of a virus within a virtual population using **Python**.  
It combines **mathematical modeling**, **probability-based events**, and a **real-time visualization with Pygame**.

---

## 🎥 Demo Video 

![Image](https://github.com/user-attachments/assets/39cc0116-5ab4-4abf-a4ba-a8d20ae7d311)

---

## 📌 Features

- **Population dynamics**
  - Births, deaths (natural causes, starvation, infection).
  - Job assignments (farmer, doctor, worker, jobless, children).
  - Social mobility (job changes, personality/status shifts).

- **Disease simulation**
  - Infection spread based on proximity.
  - Probabilistic recovery or death depending on personality traits.
  - Doctor treatment capacity and hospital stays.

- **Food system**
  - Farmers produce food, residents consume it based on personality and job.
  - Starvation occurs if food deficit persists.

- **Couples & reproduction**
  - Eligible residents form couples.
  - Birth rates depend on satisfaction and food availability.

- **Satisfaction system**
  - Adjusted based on food balance, mortality, hospitalizations, and more.

- **Visualization (Pygame)**
  - Interactive window with a gradient background.
  - Each inhabitant represented as a colored dot:
    - 🔴 Infected  
    - 🟡 Farmer  
    - 🟢 Doctor  
    - 🔵 Worker  
    - ⚪ Jobless  
    - 🟠 Children  
  - Legend box in the bottom-right corner.

---

## 🎮 Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/Uramix2/virus_project.git
   cd virus_project
   ```

2. **Install dependencies**
   ```bash
   pip install pygame
   ```

3. **Run the simulation**
   ```bash
   python main.py
   ```

4. **Optional: test the model without Pygame**
   ```bash
   python habitant.py
   ```

---

## 🖥️ Project Structure

```
virus-simulation/
│
├── habitant.py      # Inhabitant class definition and Core logic (population, disease, food, satisfaction)
├── final_test.py    # Pygame visualization and main simulation loop
└── README.md        # Project documentation
```

---

## 📊 Example Output

Console log (every few days):
```
Day  5: 👥 148 | 🍖 1800 | 😊 74.2 | ⚰️ 2 deaths | 👶 1 births
Day 10: 👥 153 | 🍖 2100 | 😊 76.8 | ⚰️ 3 deaths | 👶 2 births
...
```

Pygame visualization shows inhabitants in real-time with color-coded roles and infection states.
