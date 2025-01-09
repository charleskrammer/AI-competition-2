from brain_interface import SpaceshipBrain, Action, GameState
import math

class AggressiveHunterBrain(SpaceshipBrain):
    def __init__(self):
        self._id = "Perso"
        self.current_target_id = None
        self.optimal_range = 300
        self.being_hit = False  # Track if the ship is being hit

    @property
    def id(self) -> str:
        return self._id

    def decide_what_to_do_next(self, game_state: GameState) -> Action:
        # Find my ship
        try:
            my_ship = next(ship for ship in game_state.ships if ship['id'] == self.id)
        except StopIteration:
            return Action.ROTATE_RIGHT  # Default action if my ship isn't found

        # Check if the ship is being hit
        if my_ship['health'] < getattr(self, 'previous_health', my_ship['health']):
            self.being_hit = True
        else:
            self.being_hit = False

        self.previous_health = my_ship['health']  # Update health for the next cycle

        # If being hit, search for gold
        if self.being_hit:
            gold_piles = game_state.gold_positions
            if gold_piles:
                # Find the closest gold pile
                closest_gold = min(gold_piles, key=lambda gold: math.hypot(gold[0] - my_ship['x'], gold[1] - my_ship['y']))
                dx = closest_gold['x'] - my_ship['x']
                dy = closest_gold['y'] - my_ship['y']
                target_line_angle = math.degrees(math.atan2(dy, dx))

                # Calculate angle difference
                angle_diff = (target_line_angle - my_ship['angle'] + 360) % 360
                if angle_diff > 180:
                    angle_diff -= 360

                if abs(angle_diff) < 10:
                    # Move toward gold
                    return Action.ACCELERATE
                elif angle_diff > 0:
                    return Action.ROTATE_RIGHT
                else:
                    return Action.ROTATE_LEFT
            else:
                # No gold available, rotate to search
                return Action.ROTATE_RIGHT

        # Original aggressive behavior when not being hit
        enemy_ships = [ship for ship in game_state.ships if ship['id'] != self.id and ship['health'] > 0]
        if not enemy_ships:
            self.current_target_id = None  # Reset target if no enemies are left
            return Action.ROTATE_RIGHT

        # Select target - either keep current or pick closest if no valid target
        current_target = next((ship for ship in enemy_ships if ship['id'] == self.current_target_id), None)
        if not current_target or current_target['health'] <= 0:
            current_target = min(enemy_ships, 
                key=lambda ship: math.hypot(ship['x'] - my_ship['x'], ship['y'] - my_ship['y']))
            self.current_target_id = current_target['id']

        # Calculate angle to target
        dx = current_target['x'] - my_ship['x']
        dy = current_target['y'] - my_ship['y']
        target_line_angle = math.degrees(math.atan2(dy, dx))

        # Calculate angle difference and normalize to -180 to 180
        angle_diff = (target_line_angle - my_ship['angle'] + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360

        # Get distance to target
        distance = math.hypot(dx, dy)

        # Check if target is ahead within shooting range
        if abs(angle_diff) < 10:  # Angle difference is small enough to be considered "ahead"
            if distance < self.optimal_range:
                return Action.SHOOT
            elif distance > self.optimal_range:
                return Action.ACCELERATE
            else:
                return Action.BRAKE

        # Turn toward target
        if angle_diff > 0:
            return Action.ROTATE_RIGHT
        return Action.ROTATE_LEFT