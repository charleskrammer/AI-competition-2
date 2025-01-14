# brains/perso.py
import random
import math
import json
from brain_interface import SpaceshipBrain, Action, GameState

class GeneticHunterBrain(SpaceshipBrain):
    def __init__(self, params=None):
        self._id = "Perso"
        # On ajoute de nouveaux paramètres pour varier le comportement
        self.params = params if params else self.random_params()

        # Tentative de chargement de paramètres déjà entraînés
        try:
            with open("best_brain_params.json", "r") as f:
                loaded_params = json.load(f)
            # On fusionne en conservant les clés existantes
            self.params.update(loaded_params)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    @property
    def id(self) -> str:
        return self._id

    def random_params(self):
        return {
            'retreat_threshold': random.uniform(0.1, 0.5),  # % de vie en dessous duquel on fuit
            'targeting_weight': random.uniform(0.5, 1.5),
            'shoot_accuracy': random.uniform(5, 20),        # angle +/- avant SHOOT
            'distance_weight': random.uniform(0.5, 2.0),    # distance max pour tirer
            'aggressiveness': random.uniform(0.0, 1.0),     # envie de se rapprocher ou non
            'brake_usage': random.uniform(0.0, 1.0)         # probabilité de freiner
        }

    def decide_what_to_do_next(self, game_state: GameState) -> Action:
        try:
            my_ship = next(ship for ship in game_state.ships if ship['id'] == self.id)
        except StopIteration:
            return Action.ROTATE_RIGHT  # Si jamais on ne trouve pas notre ship

        # 1) Si points de vie trop bas, on s'éloigne (accélération pour fuir).
        if my_ship['health'] < self.params['retreat_threshold'] * 100:
            return Action.ACCELERATE

        # 2) Repérer les ennemis encore vivants
        enemy_ships = [
            ship for ship in game_state.ships
            if ship['id'] != self.id and ship['health'] > 0
        ]
        if not enemy_ships:
            # S’il n’y a plus d’ennemi, on tourne
            return Action.ROTATE_RIGHT

        # 3) Choisir la cible la plus proche
        current_target = min(
            enemy_ships,
            key=lambda s: math.hypot(s['x'] - my_ship['x'], s['y'] - my_ship['y'])
        )
        dx = current_target['x'] - my_ship['x']
        dy = current_target['y'] - my_ship['y']
        distance = math.hypot(dx, dy)
        target_angle = math.degrees(math.atan2(dy, dx))
        angle_diff = (target_angle - my_ship['angle'] + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360

        # 4) Logique de tir (on tire si aligné et à bonne distance)
        if abs(angle_diff) < self.params['shoot_accuracy'] and \
           distance < self.params['distance_weight'] * 300:
            return Action.SHOOT

        # 5) Sinon, on essaie de se rapprocher s’il est trop loin
        if distance > self.params['distance_weight'] * 300:
            # En fonction de l'agressivité, on accélère ou on tourne
            if random.random() < self.params['aggressiveness']:
                return Action.ACCELERATE

        # 6) Tourner pour s’aligner
        if angle_diff > 0:
            return Action.ROTATE_RIGHT
        else:
            return Action.ROTATE_LEFT

    def on_game_complete(self, final_state: GameState, won: bool):
        # Optionnel : logique de fin de partie, ex. logs, apprentissage etc.
        pass