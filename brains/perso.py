import random
from brain_interface import SpaceshipBrain, Action, GameState
import math
import json


class GeneticHunterBrain(SpaceshipBrain):
    def __init__(self, params=None):
        self._id = "Perso"
        self.params = params if params else self.random_params()

        try:
            with open("best_brain_params.json", "r") as f:
                params = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to random parameters if the file doesn't exist or is invalid
            params = None
        self.params = params if params else self.random_params()
        
    @property
    def id(self) -> str:
        return self._id

    def random_params(self):
        """Generate random parameters for the genetic algorithm."""
        return {
            'retreat_threshold': random.uniform(0.1, 0.5),  # Fraction of health to trigger retreat
            'targeting_weight': random.uniform(0.5, 1.5),  # Weight for selecting targets
            'shoot_accuracy': random.uniform(5, 20),  # Acceptable angle difference for shooting
            'distance_weight': random.uniform(0.5, 2.0),  # Weight for maintaining optimal range
        }

    def decide_what_to_do_next(self, game_state: GameState) -> Action:
        try:
            # Locate the player's ship
            my_ship = next(ship for ship in game_state.ships if ship['id'] == self.id)
        except StopIteration:
            return Action.ROTATE_RIGHT

        # Retreat logic: If health is below threshold, accelerate away
        if my_ship['health'] < self.params['retreat_threshold'] * 100:
            return Action.ACCELERATE

        # Identify enemy ships
        enemy_ships = [
            ship for ship in game_state.ships if ship['id'] != self.id and ship['health'] > 0
        ]
        if not enemy_ships:
            # No enemies, rotate in search of targets
            return Action.ROTATE_RIGHT

        # Select the closest target
        current_target = min(
            enemy_ships,
            key=lambda ship: math.hypot(ship['x'] - my_ship['x'], ship['y'] - my_ship['y']),
        )

        # Calculate angles and distances
        dx = current_target['x'] - my_ship['x']
        dy = current_target['y'] - my_ship['y']
        target_angle = math.degrees(math.atan2(dy, dx))
        angle_diff = (target_angle - my_ship['angle'] + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360

        distance = math.hypot(dx, dy)

        # Shooting logic
        if abs(angle_diff) < self.params['shoot_accuracy'] and distance < self.params['distance_weight'] * 300:
            return Action.SHOOT
        # Movement logic
        elif distance > self.params['distance_weight'] * 300:
            return Action.ACCELERATE
        elif angle_diff > 0:
            return Action.ROTATE_RIGHT
        else:
            return Action.ROTATE_LEFT
        
    