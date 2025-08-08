import numpy as np
import matplotlib.pyplot as plt

# Step 1: Create 15 dummy 2D vectors to simulate a trajectory
np.random.seed(42)
trajectory = np.cumsum(np.random.randn(15, 2), axis=0)  # cumulative sum = smoother path

# Step 2: Identify control points based on geometric distortion
threshold = 0.5  # adjust this to tune sensitivity
control_points = []

for i in range(1, len(trajectory)-1):
    p0, p1, p2 = trajectory[i-1], trajectory[i], trajectory[i+1]
    
    full_path_len = np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1)
    shortcut_len = np.linalg.norm(p2 - p0)
    delta = full_path_len - shortcut_len

    if delta > threshold:
        control_points.append(i)

# Step 3: Create shortcut trajectory by skipping non-control middle points
simplified = [trajectory[0]]
for i in range(1, len(trajectory) - 1):
    if i in control_points:
        simplified.append(trajectory[i])
simplified.append(trajectory[-1])
simplified = np.array(simplified)

# Step 4: Visualize everything
plt.figure(figsize=(10, 6))
plt.plot(trajectory[:, 0], trajectory[:, 1], 'o-', label="Original Path", color='gray')
plt.plot(simplified[:, 0], simplified[:, 1], 'o--', label="Simplified Path", color='blue')

# Highlight control points
for i in control_points:
    plt.scatter(*trajectory[i], color='red', s=100, label="Control Point" if i == control_points[0] else "")

plt.title("Trajectory and Control Point Analysis")
plt.legend()
plt.grid(True)
plt.xlabel("X")
plt.ylabel("Y")
plt.axis('equal')
plt.show()
