# brains/perso.py
import random
import math
import json
from brain_interface import SpaceshipBrain, Action, GameState

class GeneticHunterBrain(SpaceshipBrain):
    def __init__(self, params=None):
        """
        Initializes the GeneticHunterBrain.

        :param params: Optionally, an existing dictionary of parameters.
                       If none is provided, random parameters will be generated.
        """
        self._id = "group1-CharlesK"

        # If params is not provided, create a random dictionary of parameters
        self.params = params if params else self.random_params()

        # Attempt to load previously trained parameters from best_brain_params.json
        try:
            with open("best_brain_params.json", "r") as f:
                loaded_params = json.load(f)
            # Merge any existing keys rather than overwriting them entirely
            self.params.update(loaded_params)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or JSON is invalid, we just keep our local params
            pass

    @property
    def id(self) -> str:
        """
        Returns a unique identifier for this brain instance.
        """
        return self._id

    def random_params(self):
        """
        Generate a dictionary of random parameters for this brain's behavior.
        
        Explanation of each parameter:
          - retreat_threshold: If the ship's health drops below (threshold * 100),
                               the ship attempts to retreat (accelerate away).
          - targeting_weight:  Currently unused, but can be used to modify targeting logic.
          - shoot_accuracy:    The angle tolerance (+/- degrees) for deciding to shoot.
          - distance_weight:   The max distance factor for shooting (multiplied by 300).
          - aggressiveness:    Probability of accelerating towards a target instead of turning.
          - brake_usage:       Probability of braking, if logic were to be added for it.
        """
        return {
            'retreat_threshold': random.uniform(0.1, 0.5),  # fraction of max health below which the ship flees
            'targeting_weight': random.uniform(0.5, 1.5),
            'shoot_accuracy': random.uniform(5, 20),        # +/- angle tolerance for shooting
            'distance_weight': random.uniform(0.5, 2.0),    # distance factor for shooting range
            'aggressiveness': random.uniform(0.0, 1.0),     # chance of accelerating instead of turning
            'brake_usage': random.uniform(0.0, 1.0)         # chance of using brake (unused in simple logic)
        }

    def decide_what_to_do_next(self, game_state: GameState) -> Action:
        """
        Determines the ship's next action based on the current game state.
        
        :param game_state: A GameState instance containing info about all ships, bullets, etc.
        :return: An Action enum value representing the chosen action.
        """
        # Attempt to find this brain's ship in the list of all ships
        try:
            my_ship = next(ship for ship in game_state.ships if ship['id'] == self.id)
        except StopIteration:
            # If for some reason the ship is missing, just rotate right as a fallback
            return Action.ROTATE_RIGHT

        # 1) If health is too low, accelerate away (retreat)
        if my_ship['health'] < self.params['retreat_threshold'] * 100:
            return Action.ACCELERATE

        # 2) Identify all living enemy ships
        enemy_ships = [
            ship for ship in game_state.ships
            if ship['id'] != self.id and ship['health'] > 0
        ]
        if not enemy_ships:
            # If no enemies remain, just rotate right
            return Action.ROTATE_RIGHT

        # 3) Pick the nearest target
        current_target = min(
            enemy_ships,
            key=lambda s: math.hypot(s['x'] - my_ship['x'], s['y'] - my_ship['y'])
        )
        dx = current_target['x'] - my_ship['x']
        dy = current_target['y'] - my_ship['y']
        distance = math.hypot(dx, dy)
        target_angle = math.degrees(math.atan2(dy, dx))
        # Calculate angle difference between my ship's orientation and the target
        angle_diff = (target_angle - my_ship['angle'] + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360

        # 4) Shooting logic: shoot if aligned enough and within distance
        if abs(angle_diff) < self.params['shoot_accuracy'] and \
           distance < self.params['distance_weight'] * 300:
            return Action.SHOOT

        # 5) Otherwise, if the target is too far, attempt to move closer
        if distance > self.params['distance_weight'] * 300:
            # Either accelerate or just turn, depending on 'aggressiveness'
            if random.random() < self.params['aggressiveness']:
                return Action.ACCELERATE

        # 6) If we're not too far, turn to align with the target
        if angle_diff > 0:
            return Action.ROTATE_RIGHT
        else:
            return Action.ROTATE_LEFT

    def on_game_complete(self, final_state: GameState, won: bool):
        """
        This method is called at the end of each game, providing the final game state while training
        Optional: end-of-game logic. For instance, you could adjust parameters here 
        based on final results, do logging, or implement incremental learning.
        
        :param final_state: Final game state, containing info about all ships, 
                            bullets, etc. at the end of the match.
        :param won: Boolean indicating if this ship was the winner.
        """
        pass