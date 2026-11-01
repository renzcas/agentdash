import numpy as np

class ChaoticAttention:
    def __init__(self, sigma=10, rho=28, beta=8/3, dt=0.01):
        # Initial Lorenz state
        self.state = {'x': 1.0, 'y': 1.0, 'z': 1.0}
        self.params = {'sigma': sigma, 'rho': rho, 'beta': beta}
        self.dt = dt
        self.trace = []  # Store attractor evolution over time

    def lorenz_step(self):
        x, y, z = self.state['x'], self.state['y'], self.state['z']
        s, r, b = self.params['sigma'], self.params['rho'], self.params['beta']

        dx = s * (y - x)
        dy = x * (r - z) - y
        dz = x * y - b * z

        # Update state with timestep
        self.state['x'] += dx * self.dt
        self.state['y'] += dy * self.dt
        self.state['z'] += dz * self.dt

        # Log trace for visualization
        self.trace.append((self.state['x'], self.state['y'], self.state['z']))

    def score(self, query, key):
        self.lorenz_step()

        # Complex-valued attention score
        z = complex(np.dot(query, key.T))  # Inner product as complex magnitude
        attractor_z = complex(self.state['x'], self.state['y'])  # Lorenz projection

        salience = np.exp(-abs(z - attractor_z))  # Distance-based decay
        phase = np.exp(1j * np.angle(z))          # Phase encoding

        return salience * phase  # Final complex attention score