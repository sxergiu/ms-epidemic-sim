
import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)        # Infected
GREEN = (0, 255, 0)      # Recovered
BLUE = (0, 0, 255)       # Susceptible
GRAY = (169, 169, 169)   # Quarantine zones

FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Epidemic Simulation")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont(None, 24)

class Agent:

    def __init__(self, position=None, velocity=None, speed=2, state="S"):
        self.position = position or pygame.math.Vector2(random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT))
        self.velocity = velocity or pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.speed = speed
        self.state = state
        self.color = BLUE if state == "S" else (RED if state == "I" else GREEN)
        self.infection_timer = 0  
        self.trail = []
        self.max_trail_length = 10

    def update_state(self):
        self.color = BLUE if self.state == "S" else (RED if self.state == "I" else GREEN)
    
    def update_position(self):
        """Update the agent's position based on its velocity and speed."""
        self.position += self.velocity * self.speed
        self._bounce_off_walls()
        self._update_trail()
    
    def _bounce_off_walls(self):
        """Bounce the agent off the screen edges."""
        if self.position.x < 0 or self.position.x > SCREEN_WIDTH:
            self.velocity.x *= -1
        if self.position.y < 0 or self.position.y > SCREEN_HEIGHT:
            self.velocity.y *= -1

        # Keep position within bounds
        self.position.x = max(0, min(self.position.x, SCREEN_WIDTH))
        self.position.y = max(0, min(self.position.y, SCREEN_HEIGHT))

    def _update_trail(self):
        """Update the trail of the agent for visualization."""
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

    def draw_trail(self):
        """Draw the trail of the agent."""
        if len(self.trail) > 1:
            pygame.draw.lines(screen, self.color, False, [(int(p.x), int(p.y)) for p in self.trail], 1)

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), 4)

def infect_agents(agents, infection_radius, infection_probability):
    for agent in agents:
        if agent.state == "I":  # Only infected agents can infect others
            for other_agent in agents:
                if other_agent.state == "S":  # Only infect susceptible agents
                    distance = ((agent.position.x - other_agent.position.x) ** 2 + (agent.position.y - other_agent.position.y) ** 2) ** 0.5
                    if distance <= infection_radius and random.random() < infection_probability:
                        other_agent.state = "I"
                        other_agent.update_state()

def update_infections(agents, recovery_time, mortality_probability):
    for agent in agents:
        if agent.state == "I":
            agent.infection_timer += 1
            if agent.infection_timer >= recovery_time:
                if random.random() < mortality_probability:
                    agents.remove(agent)  # Simulate death
                else:
                    agent.state = "R"  # Recover
                    agent.update_state()

class QuarantineZone:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)

    def isolate(self, agents):
        for agent in agents:
            if agent.state == "I" and not self.rect.collidepoint(agent.position.x, agent.position.y):
                agent.position.x = random.randint(self.rect.left, self.rect.right)
                agent.position.y = random.randint(self.rect.top, self.rect.bottom)

def vaccinate_agents(agents, vaccination_probability, success_rate):
    for agent in agents:
        if agent.state == "S" and random.random() < vaccination_probability:
            if random.random() < success_rate:
                agent.state = "R"
                agent.update_state()

def plot_population_stats(stats):
    # Simple terminal-based plot (extend to graphs if desired)
    print("Time:", len(stats), " | ", stats[-1])

def track_history(agents, stats):
    susceptible = sum(1 for a in agents if a.state == "S")
    infected = sum(1 for a in agents if a.state == "I")
    recovered = sum(1 for a in agents if a.state == "R")
    stats.append((susceptible, infected, recovered))

class Simulation:
     
    def __init__(self, num_agents = 50, num_infected = 5):

        self.agents = [Agent() for _ in range(num_agents)]

        for _ in range(num_infected):
            self.agents[random.randint(0, len(self.agents) - 1)].state = "I"

        self.quarantine = QuarantineZone(600, 400, 100, 100)

        self.stats = []
        self.running = True
    
    def run(self):
        
        while self.running:
            clock.tick(FPS)
            self.handle_events()
            self.update_agents()
            self.handle_collisions()
            self.handle_quarantine()
            self.hanlde_infections()
            self.render()

        pygame.quit()

    def handle_events(self):
   
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.infect_agent()
    
    def infect_agent(self):
        self.agents[random.randint(0, len(self.agents) - 1)].state = "I"

    def update_agents(self):

        for agent in self.agents:
            agent.update_position()

    def handle_collisions(self):
      
        for agent in self.agents:
            for other_agent in self.agents[:]:
                if agent.position.distance_to(other_agent.position) < 5:
                    if( agent.state=="I" and other_agent.state=='S'):
                        other_agent.state = "I"
                        other_agent.update_state
    
    def hanlde_infections(self):
        infect_agents(self.agents, infection_radius=10, infection_probability=0.1)
        update_infections(self.agents, recovery_time=300, mortality_probability=0.02)

    def handle_quarantine(self):
        self.quarantine.isolate(self.agents)

    def render(self):
        
        screen.fill(WHITE)

        #self.draw_legend()
        #self.draw_stats()

        for agent in self.agents:
             agent.draw()

        self.quarantine.draw(screen)

        track_history(self.agents, self.stats)
        if len(self.stats) % 60 == 0:  # Plot every second
            plot_population_stats(self.stats)

        pygame.display.flip()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()


