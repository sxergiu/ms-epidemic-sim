
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

# Simulation constants
infection_radius = 30
grouping_radius = 15

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
        self.in_quarantine = False
        self.time_in_quarantine = 0  # Track time in quarantine zone

    def update_state(self):
        self.color = BLUE if self.state == "S" else (RED if self.state == "I" else GREEN)

    def update_position(self):
        """Update the agent's position based on its velocity and speed."""
        if not self.in_quarantine:  # Only update position if not in quarantine
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
        if self.state == "I":
            pygame.draw.circle(screen, RED, (int(self.position.x), int(self.position.y)), infection_radius, width=1)

        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), 4)
        self.draw_trail()

    def enter_quarantine(self):
        self.in_quarantine = True
        self.time_in_quarantine = 0  # Reset the time in quarantine when they enter

    def update_quarantine_time(self):
        if self.in_quarantine:
            self.time_in_quarantine += 1
    
    def move_in_quarantine(self, rectangle):
        """Move the agent inside the quarantine zone, keeping it within the bounds."""
        if self.in_quarantine:
            zone_center = pygame.math.Vector2(self.position.x, self.position.y)  # Get the current position of the agent

            # Make sure the agent stays within the quarantine area by checking bounds
            quarantine_zone = rectangle  # Example zone bounds

            if not quarantine_zone.collidepoint(self.position):
                # If the agent is out of bounds, redirect them towards the quarantine zone center
                direction_to_center = pygame.math.Vector2(quarantine_zone.centerx, quarantine_zone.centery) - self.position
                self.velocity = direction_to_center.normalize()  # Normalize to prevent high-speed movement

            self.position += self.velocity * self.speed
            self._update_trail()

def infect_agents(agents, infection_radius, infection_probability):
    for agent in agents:
        if agent.state == "I":  # Only infected agents can infect others
            for other_agent in agents:
                if other_agent.state == "S":  # Only infect susceptible agents
                    distance = agent.position.distance_to(other_agent.position)
                    if distance <= infection_radius and random.random() < infection_probability:
                        other_agent.state = "I"
                        other_agent.update_state()

class QuarantineZone:
    def __init__(self, x, y, width, height, avoidance_radius=100, avoidance_strength=1, quarantine_time=300):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY
        self.avoidance_radius = avoidance_radius
        self.avoidance_strength = avoidance_strength
        self.quarantine_time = quarantine_time  # Time infected agents stay in the quarantine zone
        self.infected_agents_in_quarantine = []

    def draw(self):
        """Draw the quarantine zone."""
        pygame.draw.rect(screen, self.color, self.rect, 2)  # 2 pixel border
        # Add some transparency to fill
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(50)
        s.fill(self.color)
        screen.blit(s, (self.rect.x, self.rect.y))

    def steer_agents(self, agents):
        """Steer non-infected agents away from the quarantine zone."""
        for agent in agents:
            if agent.state != "I":  # Only affect susceptible or recovered agents
                distance = agent.position.distance_to(pygame.math.Vector2(self.rect.centerx, self.rect.centery))
                if distance <= self.avoidance_radius:  # Agent is within avoidance range
                    self.steer_away(agent)

    def steer_away(self, agent):
        """Steer the agent away from the quarantine zone."""
        zone_center = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        avoidance_direction = agent.position - zone_center
        avoidance_direction = avoidance_direction.normalize()  # Normalize to avoid making it too fast
        agent.velocity += avoidance_direction * self.avoidance_strength  # Modify the velocity to steer away

        # Normalize the velocity to avoid making the agent go too fast
        if agent.velocity.length() > 1:
            agent.velocity = agent.velocity.normalize()

    def redirect_group_to_quarantine(self, group):
        """Redirect a group of infected agents towards the quarantine zone."""
        zone_center = pygame.math.Vector2(self.rect.centerx, self.rect.centery)

        for agent in group:
            steering_direction = zone_center - agent.position
            steering_direction = steering_direction.normalize()
            agent.velocity += steering_direction * 0.1  # Modify the velocity to move towards the quarantine center

            # Normalize the velocity to avoid fast movement
            if agent.velocity.length() >= 1:
                agent.velocity = agent.velocity.normalize()

            # Check if the agent has reached the quarantine zone
            if agent.position.distance_to(zone_center) < infection_radius:
                agent.enter_quarantine()
    
    def check_quarantine_status(self, agents):
        """Check and update the quarantine status for each agent."""
        for agent in agents:
            if agent.in_quarantine:
                agent.update_quarantine_time()
                if agent.time_in_quarantine >= self.quarantine_time:
                    agent.state = "R"  # Once the agent has been in quarantine for long enough, they recover
                    agent.update_state()
                    agent.in_quarantine = False  # Exit quarantine
                    agent.time_in_quarantine = 0  # Reset time

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
     
    def __init__(self, num_agents = 50, num_infected = 0):

        self.agents = [Agent() for _ in range(num_agents)]

        for _ in range(num_infected):
            self.agents[random.randint(0, len(self.agents) - 1)].state = "I"

        self.quarantine = QuarantineZone(
            SCREEN_WIDTH - 500,
            SCREEN_HEIGHT - 500,
            350,
            200,
            150,
            10
        )

        self.stats = []
        self.running = True
    
    def run(self):
        
        while self.running:
            clock.tick(FPS)
            self.handle_events()
            self.update_agents()
            self.handle_collisions()
            self.handle_quarantine()
            self.handle_infections()
            self.handle_grouping()
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
                if agent.position.distance_to(other_agent.position) < infection_radius:
                    if( agent.state=="I" and other_agent.state=='S'):
                        other_agent.state = "I"
                        other_agent.update_state

    def handle_grouping(self):
        """Handle the grouping of infected agents and redirect them to the quarantine zone."""
        for agent in self.agents:
            if agent.state == "I":
                nearby_infected = [
                    other_agent for other_agent in self.agents if other_agent.state == "I" and agent.position.distance_to(other_agent.position) < grouping_radius
                ]
                if len(nearby_infected) > 1:  # If there are nearby infected agents, form a group
                    group_center = pygame.math.Vector2(0, 0)
                    for nearby_agent in nearby_infected:
                        group_center += nearby_agent.position
                    group_center /= len(nearby_infected)  # Find the center of the group

                    # Redirect the group toward the quarantine zone
                    self.quarantine.redirect_group_to_quarantine(nearby_infected)
    
    def handle_infections(self):
        infect_agents(self.agents, infection_radius=10, infection_probability=0.1)

    def handle_quarantine(self):
        for agent in self.agents:
            if agent.in_quarantine:
                agent.move_in_quarantine(self.quarantine.rect)
        self.quarantine.steer_agents(self.agents)

    def render(self):
        
        screen.fill(WHITE)

        #self.draw_legend()
        #self.draw_stats()

        for agent in self.agents:
             agent.update_state()
             agent.draw()

        self.quarantine.draw()

        track_history(self.agents, self.stats)
        if len(self.stats) % 60 == 0:  # Plot every second
            plot_population_stats(self.stats)

        pygame.display.flip()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()


