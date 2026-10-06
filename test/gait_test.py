#!/bin/env python
# 
#%% 
import numpy as np
import matplotlib.pyplot as plt

class DogWalkGait:
    def __init__(self, cycle_duration=1.0):
        # Cycle duration in seconds
        self.T = cycle_duration
        
        # Standard symmetrical walk phase offsets for quadruped legs
        # Order: [Left Front (LF), Right Front (RF), Left Rear (LR), Right Rear (RR)]
        # Walk pattern offsets (fraction of cycle 0 to 1)
        self.phases = np.array([0.0, 0.5, 0.75, 0.25])
        
        # Duty factor: fraction of cycle the foot is on the ground (stance phase > 0.5 for walk)
        self.duty_factor = 0.625 


    def get_leg_states(self, t):
        """
        Determines if each leg is in 'Stance' (1) or 'Swing' (0) at time t.
        """
        # Normalize time to cycle progress [0, 1)
        normalized_time = (t % self.T) / self.T
        
        # Shift relative to each leg's phase offset
        leg_progress = (normalized_time - self.phases) % 1.0
        
        # Stance if progress is less than duty factor, else swing
        stance_state = (leg_progress < self.duty_factor).astype(int)
        return stance_state

# Simulation example
gait = DogWalkGait(cycle_duration=1.2)
time_steps = np.linspace(0, 3.6, 360) # 3 gait cycles
leg_names = ['Left Front', 'Right Front', 'Left Rear', 'Right Rear']

# Compute states over time
states = np.array([gait.get_leg_states(t) for t in time_steps])

# Plotting the gait diagram (footfall chart)
plt.figure(figsize=(10, 4))
for i, name in enumerate(leg_names):
    plt.plot(time_steps, states[:, i] + i * 1.5, label=name, lw=4)

plt.yticks([i * 1.5 for i in range(4)], leg_names)
plt.xlabel('Time (s)')
plt.title('Dog Walking Gait Footfall Diagram (Stance = High, Swing = Low)')
plt.ylim(-0.5, 6)
plt.grid(True, axis='x')
plt.show()
