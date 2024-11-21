# Below is a cleaner implementation of our basic prey/predator system from the lab
import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600

# Colors
BACKGROUND_COLOR = (30, 30, 30)
PREY_COLOR = (0, 255, 0)
PREDATOR_COLOR = (255, 0, 0)
TEXT_COLOR = (200, 200, 200)

# Frame rate
FPS = 60

# Initialize screen and clock
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Predator-Prey Simulation")
clock = pygame.time.Clock()

# Font for text
FONT = pygame.font.SysFont(None, 24)

class Agent:
    """Base class for all agents in the simulation."""
    def __init__(self, position=None, velocity=None, speed=2, color=PREY_COLOR):
        self.position = position or pygame.math.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        self.velocity = velocity or pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.speed = speed
        self.color = color
        self.trail = []
        self.max_trail_length = 10

    def update_position(self):
        """Update the agent's position based on its velocity and speed."""
        self.position += self.velocity * self.speed
        self._bounce_off_walls()
        self._update_trail()

    def _bounce_off_walls(self):
        """Bounce the agent off the screen edges."""
        if self.position.x < 0 or self.position.x > WIDTH:
            self.velocity.x *= -1
        if self.position.y < 0 or self.position.y > HEIGHT:
            self.velocity.y *= -1

        # Keep position within bounds
        self.position.x = max(0, min(self.position.x, WIDTH))
        self.position.y = max(0, min(self.position.y, HEIGHT))

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
        """Method to draw the agent. To be implemented by subclasses."""
        raise NotImplementedError("Draw method must be implemented by subclasses.")

class Prey(Agent):
    """Class representing a prey agent."""
    def __init__(self):
        super().__init__(speed=2, color=PREY_COLOR)
        self.vision_radius = 50  # Detection radius for predators

    def update(self, predators):
        """Update the prey's state based on nearby predators."""
        nearest_predator = self._find_nearest_predator(predators)
        if nearest_predator:
            self.flee_from(nearest_predator)
        self.update_position()

    def _find_nearest_predator(self, predators):
        """Find the nearest predator within vision radius."""
        nearest = None
        min_distance = self.vision_radius
        for predator in predators:
            distance = self.position.distance_to(predator.position)
            if distance < min_distance:
                min_distance = distance
                nearest = predator
        return nearest

    def flee_from(self, predator):
        """Change velocity to flee away from the predator."""
        flee_direction = (self.position - predator.position).normalize()
        self.velocity = flee_direction

    def draw(self):
        """Draw the prey as a circle with its trail."""
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), 4)
        self.draw_trail()

class Predator(Agent):
    """Class representing a predator agent."""
    def __init__(self):
        super().__init__(speed=3, color=PREDATOR_COLOR)

    def update(self, prey_list):
        """Update the predator's state based on nearby prey."""
        if prey_list:
            nearest_prey = self._find_nearest_prey(prey_list)
            if nearest_prey:
                self.hunt(nearest_prey)
        else:
            self.update_position()

    def _find_nearest_prey(self, prey_list):
        """Find the nearest prey."""
        return min(prey_list, key=lambda prey: self.position.distance_to(prey.position), default=None)

    def hunt(self, prey):
        """Change velocity to move towards the prey."""
        direction = (prey.position - self.position).normalize()
        self.velocity = direction
        self.update_position()

    def draw(self):
        """Draw the predator as a rotated triangle with its trail."""
        # Calculate the angle in degrees between the velocity and the x-axis
        angle = self.velocity.angle_to(pygame.math.Vector2(1, 0))

        # Define the triangle points relative to the origin, pointing right
        point_list = [
            pygame.math.Vector2(10, 0),   # Tip of the triangle
            pygame.math.Vector2(-5, -5),  # Bottom left
            pygame.math.Vector2(-5, 5),   # Top left
        ]

        # Rotate the points and translate to the predator's position
        rotated_points = [self.position + p.rotate(-angle) for p in point_list]

        # Draw the predator as a triangle
        pygame.draw.polygon(screen, self.color, rotated_points)

        # Draw the trail
        self.draw_trail()

class Simulation:
    """Class to manage the entire simulation."""
    def __init__(self, num_prey=50, num_predators=3):
        self.prey_list = [Prey() for _ in range(num_prey)]
        self.predator_list = [Predator() for _ in range(num_predators)]
        self.running = True

    def run(self):
        """Main loop of the simulation."""
        while self.running:
            clock.tick(FPS)
            self.handle_events()
            self.update_agents()
            self.handle_collisions()
            self.render()

        pygame.quit()

    def handle_events(self):
        """Handle user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.add_prey()
                elif event.key == pygame.K_o:
                    self.add_predator()

    def add_prey(self):
        """Add a new prey to the simulation."""
        self.prey_list.append(Prey())

    def add_predator(self):
        """Add a new predator to the simulation."""
        self.predator_list.append(Predator())

    def update_agents(self):
        """Update all agents in the simulation."""
        for prey in self.prey_list:
            prey.update(self.predator_list)

        for predator in self.predator_list:
            predator.update(self.prey_list)

    def handle_collisions(self):
        """Handle collisions between predators and prey."""
        for predator in self.predator_list:
            for prey in self.prey_list[:]:
                if predator.position.distance_to(prey.position) < 6:
                    self.prey_list.remove(prey)

    def render(self):
        """Render all elements on the screen."""
        screen.fill(BACKGROUND_COLOR)
        self.draw_legend()
        self.draw_stats()

        # Draw all prey
        for prey in self.prey_list:
            prey.draw()

        # Draw all predators
        for predator in self.predator_list:
            predator.draw()

        pygame.display.flip()

    def draw_legend(self):
        """Draw the legend on the screen."""
        prey_text = FONT.render('Prey (Green Circle) - Press P to add', True, PREY_COLOR)
        predator_text = FONT.render('Predator (Red Triangle) - Press O to add', True, PREDATOR_COLOR)
        screen.blit(prey_text, (10, 10))
        screen.blit(predator_text, (10, 30))

    def draw_stats(self):
        """Draw the simulation statistics on the screen."""
        prey_count_text = FONT.render(f'Prey Count: {len(self.prey_list)}', True, TEXT_COLOR)
        predator_count_text = FONT.render(f'Predator Count: {len(self.predator_list)}', True, TEXT_COLOR)
        screen.blit(prey_count_text, (WIDTH - 150, 10))
        screen.blit(predator_count_text, (WIDTH - 150, 30))

if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()
