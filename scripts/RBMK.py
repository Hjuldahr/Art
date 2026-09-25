import random

# Uses Markov Chains

STATES = ("LOW", "NOMINAL", "HIGH", "ALARM", "SCRAM")

PROBS = {
    "LOW":     (0.70, 0.25, 0.02, 0.02, 0.01),
    "NOMINAL": (0.10, 0.75, 0.10, 0.03, 0.02),
    "HIGH":    (0.05, 0.10, 0.70, 0.10, 0.05),
    "ALARM":   (0.20, 0.40, 0.10, 0.25, 0.05),
    "SCRAM":   (0.30, 0.50, 0.00, 0.10, 0.10)
}

def step(current_state):
    r = random.random();
    s = 0
    for i in range(len(STATES)):
        s += PROBS[current_state][i]
        if r < s:
            return STATES[i]

current_state = "NOMINAL"
for i in range(100):
    current_state = step(current_state)
    print(current_state)