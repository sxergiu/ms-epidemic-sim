import pygame
import random
import matplotlib.pyplot as plot
from data import extract_probabilities

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 1300, 800

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)        # Infected
GREEN = (0, 255, 0)      # Recovered
BLUE = (0, 0, 255)       # Susceptible
GRAY = (169, 169, 169)   # Quarantine zones

FPS = 144

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Epidemic Simulation")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 24)

# Simulation constants
# region = 'France'
region = 'Israel'

no_agents = 200
no_infected = 10

slowdown = 0.65
speedup = 1.65

repel_radius = 10
infection_radius = 30
grouping_radius = 90

infection_probability = 0.2
recovery_probability = 0.2
vaccination_succes_probability = 0.05

vaccination_rate = 0.8

infection_rate = 0
recovery_rate = 0
successful_vax_rate = 0
failed_vax_rate = 0
death_count = 0

class Agent:
    def __init__(self, position=None, velocity=None, state="S"):
        self.position = position or pygame.math.Vector2(random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT))
        self.velocity = velocity or pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.speed = 1
        self.state = state
        self.color = BLUE if state == "S" else (RED if state == "I" else GREEN)
        self.infection_timer = 0
        self.recovery_duration = FPS * (random.uniform(5,10))
        self.proximity_duration = 0  # Time spent near an infected agent
        self.quarantine_time = FPS * (random.uniform(10,30))
        self.in_quarantine = False
        self.time_in_quarantine = 0
        self.will_vax = True if random.random() < vaccination_rate else False
        self.slowdown = False
        self.speedup = False

    def update_state(self):
        self.color = BLUE if self.state == "S" else (RED if self.state == "I" else GREEN)

    def update_position(self):
        if not self.in_quarantine: 
            self.position += self.velocity * self.speed
            self._bounce_off_walls()

    def _bounce_off_walls(self):
        """Bounce the agent off the screen edges."""
        if self.position.x < 0 or self.position.x > SCREEN_WIDTH:
            self.velocity.x *= -1
        if self.position.y < 0 or self.position.y > SCREEN_HEIGHT:
            self.velocity.y *= -1

        # Keep position within bounds
        self.position.x = max(0, min(self.position.x, SCREEN_WIDTH))
        self.position.y = max(0, min(self.position.y, SCREEN_HEIGHT))

    def draw(self):
        if self.state == "I":
            pygame.draw.circle(screen, RED, (int(self.position.x), int(self.position.y)), infection_radius, width=1)
        if self.state == "S":
            pygame.draw.circle(screen, BLUE, (int(self.position.x), int(self.position.y)), repel_radius-5, width=1)
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), 3)
    
    def move_in_quarantine(self, rectangle):
        if self.in_quarantine:
            quarantine_zone = rectangle  # Example zone bounds
            if not quarantine_zone.collidepoint(self.position):
                # If the agent is out of bounds, redirect them towards the quarantine zone center
                direction_to_center = pygame.math.Vector2(quarantine_zone.centerx, quarantine_zone.centery) - self.position
                self.velocity = direction_to_center.normalize()  # Normalize to prevent high-speed movement

            self.position += self.velocity * self.speed

    def exit_quarantine(self, rectangle, succes): # Remove agent from quarantine
            self.in_quarantine = False
            self.will_vax = False
            self.state = "R" if succes else "S"
            self.update_state()
            self.position = pygame.math.Vector2(self.position.x, rectangle.top)

    def repel_from_others(self, agents, min_distance=repel_radius):
        """Steer the agent away from others if they are too close."""
        for other_agent in agents:
            if other_agent is not self:  # Don't compare the agent to itself
                distance = self.position.distance_to(other_agent.position)
                if distance < min_distance:
                    # Calculate the repulsion direction
                    repulsion_direction = self.position - other_agent.position
                    if repulsion_direction.length() > 0:
                        repulsion_direction = repulsion_direction.normalize()
                    self.velocity += repulsion_direction * 0.1  # Adjust repulsion strength
                    self.velocity = self.velocity.normalize()


class QuarantineZone:
    def __init__(self, x, y, width, height, avoidance_radius, avoidance_strength):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GRAY
        self.avoidance_radius = avoidance_radius
        self.avoidance_strength = avoidance_strength
        self.agents_in_quarantine = []
        self.quarantine_delay = 0

    def draw(self):
        """Draw the quarantine zone."""
        pygame.draw.rect(screen, self.color, self.rect, 2)
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(30)
        s.fill(self.color)
        screen.blit(s, (self.rect.x, self.rect.y))

    def steer_agents(self, agents):
        """Steer non-infected agents away from the quarantine zone."""
        for agent in agents:
            if agent.state != "I" or agent.will_vax is False:  # Only affect susceptible or recovered agents or anti-vaxxers
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
            if agent.velocity.length() > 1:
                agent.velocity = agent.velocity.normalize()

            # Check if the agent has reached the quarantine zone
            if agent.position.distance_to(zone_center) < infection_radius:
                self.agents_in_quarantine.append(agent)
                agent.in_quarantine = True

def infect_random_agent(agents):
    global infection_rate
    index = random.randint(0,len(agents) - 1) 
    agents[index].state = "I"
    agents[index].update_state()
    infection_rate += 1

def add_sus_agent(agents):
    agents.append(Agent())

def plot_population_stats(stats):
    time_steps = [i for i in range(len(stats))]
    susceptible = [stat[0] for stat in stats]
    infected = [stat[1] for stat in stats]
    recovered = [stat[2] for stat in stats]
    death_count = [stat[3] for stat in stats]
    vax_succes_rate = [stat[4] for stat in stats]
    vax_fail_rate = [stat[5] for stat in stats]
    infection_rate = [stat[6] for stat in stats]
    recovery_rate = [stat[7] for stat in stats]

    plot.figure(figsize=(10, 6))
    
    plot.subplot(3, 1, 1)
    plot.plot(time_steps, susceptible, label='Susceptible', color='blue')
    plot.plot(time_steps, infected, label='Infected', color='red')
    plot.plot(time_steps, recovered, label='Recovered', color='green')
    plot.xlabel('Time')
    plot.ylabel('Population')
    plot.legend()
    plot.title('Epidemic Population Over Time')

    plot.subplot(3, 1, 2)
    plot.plot(time_steps, infection_rate, label='Infection Rate', color='purple')
    plot.plot(time_steps, death_count, label='Virus Kill Count', color='orange')
    plot.xlabel('Time')
    plot.ylabel('Tragedy')
    plot.legend()
    plot.title('Epidemic Casulaties Over Time')

    plot.subplot(3, 1, 3)
    plot.plot(time_steps, recovery_rate, label='Recovered Patients', color='yellow')
    plot.plot(time_steps, vax_fail_rate, label='Failed Vaccines', color='green')
    plot.plot(time_steps, vax_succes_rate, label='Succesful Vaccines', color='blue')
    plot.xlabel('Time')
    plot.ylabel('Vaccine efficiencly')
    plot.legend()
    plot.title('Epidemic Impact Over Time')

    plot.tight_layout()
    plot.show()


def track_history(agents, stats):
    global death_count
    global failed_vax_rate
    global successful_vax_rate
    global infection_rate
    global recovery_rate

    susceptible = sum(1 for a in agents if a.state == "S")
    infected = sum(1 for a in agents if a.state == "I")
    recovered = sum(1 for a in agents if a.state == "R")

    stats.append((susceptible, infected, recovered, death_count, failed_vax_rate, successful_vax_rate, infection_rate, recovery_rate ))

def document_probabilities():
    global infection_probability
    global recovery_probability
    global vaccination_rate

    infection_probability, recovery_probability, vaccination_rate = extract_probabilities(selected_region=region)

class Simulation:
     
    def __init__(self, num_agents = no_agents, num_infected = no_infected, withDataset = False):
        
        global infection_rate
        infection_rate += num_infected

        self.agents = [Agent() for _ in range(num_agents)]

        for _ in range(num_infected):
            self.agents[random.randint(0, len(self.agents) - 1)].state = "I"

        self.quarantine = QuarantineZone(
            SCREEN_WIDTH - 600,
            SCREEN_HEIGHT - 400,
            200,
            100,
            200,
            5
        )

        self.stats = []
        self.running = True

        self.withDataset = withDataset
        if( withDataset is True ):
            document_probabilities()
    
    def run(self):
        
        while self.running:
            clock.tick(FPS)
            self.handle_events()
            self.update_agents()
            self.handle_quarantine()
            self.handle_infections()
            self.handle_grouping()
            self.handle_death()
            self.slow_down_infected_agents()
            self.speed_up_recovered_agents()
            self.render()
        
        plot_population_stats(self.stats)
        pygame.quit()

    def handle_events(self):
   
        global infection_probability
        global recovery_probability
        global vaccination_succes_probability

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    infect_random_agent(self.agents)
                elif event.key == pygame.K_z:
                    add_sus_agent(self.agents)
                elif event.key == pygame.K_1:
                   infection_probability = min(1.00, infection_probability + 0.05)
                elif event.key == pygame.K_2:
                    infection_probability = max(0.00, infection_probability - 0.05)
                elif event.key == pygame.K_3:
                   recovery_probability = min(1.00, recovery_probability + 0.05)
                elif event.key == pygame.K_4:
                   recovery_probability = max(0.00, recovery_probability - 0.05)
                elif event.key == pygame.K_5:
                   vaccination_succes_probability = min(1.00, vaccination_succes_probability + 0.05)
                elif event.key == pygame.K_6:
                   vaccination_succes_probability = max(0.00, vaccination_succes_probability - 0.05)
                elif event.key == pygame.K_r:
                    plot_population_stats(self.stats)
                    self.__init__()

    def update_agents(self):
        for agent in self.agents:
            agent.update_position()
            agent.repel_from_others(self.agents)

    def handle_grouping(self):
        """Handle the grouping of infected agents and redirect them to the quarantine zone."""
        for agent in self.agents:
            if agent.state == "I" and agent.will_vax == True:
                nearby_infected = [
                    other_agent for other_agent in self.agents 
                    if other_agent.state == "I"
                    and other_agent.will_vax == True 
                    and agent.position.distance_to(other_agent.position) < grouping_radius
                ]
                if len(nearby_infected) > 1:  # If there are nearby infected agents, form a group
                    group_center = pygame.math.Vector2(0, 0)
                    for nearby_agent in nearby_infected:
                        group_center += nearby_agent.position
                    group_center /= len(nearby_infected)  # Find the center of the group

                    self.quarantine.redirect_group_to_quarantine(nearby_infected)
    
    def handle_infections(self):
        global infection_rate
        for agent in self.agents:
            if agent.state == "I": 
                    for other_agent in self.agents:
                        if other_agent.state == "S": 
                            distance = agent.position.distance_to(other_agent.position)
                            if distance <= infection_radius:
                                # Proximity factor: closer agents have higher chance of infection
                                proximity_factor = 1 - (distance / infection_radius)
                                
                                # Increment duration counter if agents stay close
                                other_agent.proximity_duration += 1

                                # Infection probability increases with time spent close
                                aux_infection_probability = infection_probability + (proximity_factor * other_agent.proximity_duration)
                                aux_infection_probability = min(0.8, aux_infection_probability)  # Cap at 100%

                                if random.random() < aux_infection_probability:
                                    other_agent.state = "I"
                                    other_agent.update_state()
                                    infection_rate += 1
                                    other_agent.proximity_duration = 0  
                            else:
                                other_agent.proximity_duration = 0

    def handle_quarantine(self):
        global successful_vax_rate
        global failed_vax_rate
        global recovery_rate
        succes = False
        self.quarantine.quarantine_delay += 1

        for agent in self.quarantine.agents_in_quarantine:
            if agent.time_in_quarantine >= agent.quarantine_time:
                if random.random() < vaccination_succes_probability:
                    succes = True
                    successful_vax_rate += 1
                    recovery_rate += 1
                else:
                    failed_vax_rate += 1
        
                self.quarantine.agents_in_quarantine.remove(agent)
                agent.exit_quarantine(self.quarantine.rect, succes)
            else:
                agent.time_in_quarantine += 1

        self.quarantine.steer_agents(self.agents)

    def handle_death(self):
        global death_count
        global recovery_rate
        for agent in self.agents:
            if agent.state == "I":
                agent.infection_timer += 1
                if agent.infection_timer >= agent.recovery_duration:
                    if random.random() < recovery_probability:
                        recovery_rate += 1
                        agent.state = "S"  
                        agent.update_state()  
                    else:
                        self.agents.remove(agent)  
                        death_count += 1
    
    def slow_down_infected_agents(self, slowdown_factor=slowdown):
        for agent in self.agents:
            if agent.state == "I" and agent.slowdown is False:  
                agent.speed *= slowdown_factor  
                agent.slowdown = True

    def speed_up_recovered_agents(self, speedup_factor = speedup):
        for agent in self.agents:
            if agent.state == "R" and agent.speedup is False:  
                agent.speed *= speedup_factor  
                agent.speedup = True


    def draw_legend(self):
    
        infect_text = FONT.render('Infect Random Agent: Press Q', True, BLACK)
        sus_text = FONT.render('Add Susceptible Agent: Press Z', True, BLACK)
        infection_probability_text = FONT.render(f'Infection Rate: {infection_probability:.2f}', True, BLACK)
        recovery_probability_text = FONT.render(f'Recovery Rate: {recovery_probability:.2f}', True, BLACK)
        vaccination_rate_text = FONT.render(f'Vax Succes Rate: {vaccination_succes_probability:.2f}', True, BLACK)
        death_count_text = FONT.render(f'Death count: {death_count}',True, BLACK)
        total_count_text = FONT.render(f'Agent count: {len(self.agents)}', True, BLACK )

        screen.blit(infect_text, (20, 10))
        screen.blit(sus_text,(20,30))
        screen.blit(infection_probability_text, (20, 730))
        screen.blit(recovery_probability_text, (20, 750))
        screen.blit(vaccination_rate_text, (20, 770))
        screen.blit(death_count_text, (SCREEN_WIDTH - 140, SCREEN_HEIGHT - 30))
        screen.blit(total_count_text, (SCREEN_WIDTH - 160, SCREEN_HEIGHT - 50))
        

    def render(self):
        
        screen.fill(WHITE)

        self.draw_legend()

        for agent in self.agents:
             agent.update_state()
             agent.draw()

        self.quarantine.draw()

        track_history(self.agents, self.stats)
        pygame.display.flip()        

if __name__ == "__main__":
    sim = Simulation(withDataset=True)
    sim.run()

