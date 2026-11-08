"""Example 4 - Gymnasium interface for reinforcement learning / supervisory control agents."""
import numpy as np

from virtualbas.ai.gym_env import VirtualBASEnv

env = VirtualBASEnv("buildings/large_office",
                    scenario={"start": "2023-07-10", "end": "2023-07-12", "realism": 1.0,
                              "random_faults": {"rate_per_week": 2}},
                    decision_steps=3)   # one decision every 15 min
obs, info = env.reset(seed=0)
ret = 0.0
while True:
    oat = obs[env.obs_points.index("WX/OA-T")]
    sat = float(np.clip(16.5 - (oat - 15) * 0.4, 12.8, 16.5))       # simple reset rule as a stand-in for a policy
    action = np.array([sat] * 4 + [6.7], dtype=np.float32)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated:
        break
    ret += reward
print("episode return", round(ret, 2))
env.close()
