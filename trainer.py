# genetic_trainer.py
import os
import csv
import json
import random

from space_game import GameEnvironment, SpaceGame

# Number of games played to evaluate the fitness of each individual
GAMES_PER_INDIVIDUAL = 3

###################
# Main Genetic Algorithm
###################
def genetic_training(population_size=100, generations=100, mutation_rate=0.1):
    """
    Trains the 'GeneticHunterBrain' (perso.py) via 'space_game.py',
    logs each individual (fitness, params) in a CSV file,
    and saves the best global individual in 'best_brain_params.json'.
    """

    # (1) Initial population
    population = [random_params() for _ in range(population_size)]

    # Variables to track the best global individual
    best_params_ever = None
    best_fitness_ever = float('-inf')

    # CSV log file
    LOG_FILE = "training_logs.csv"
    create_csv_header_if_needed(LOG_FILE)

    for gen in range(generations):
        print(f"\n=== Generation {gen+1}/{generations} ===")

        # (2) Evaluate the population
        fitness_results = []
        for i, params in enumerate(population):
            fitness = evaluate_params(params, GAMES_PER_INDIVIDUAL)
            fitness_results.append((params, fitness))
            print(f"  Individual #{i+1}: fitness={fitness:.2f}")

            # Log in the CSV
            log_to_csv(LOG_FILE, gen+1, i+1, fitness, params)

            # Update the best global record
            if fitness > best_fitness_ever:
                best_fitness_ever = fitness
                best_params_ever = params.copy()
                print(f"    => New global record! fitness={fitness:.2f}")

        # (3) Sort to identify the best individual of this generation
        fitness_results.sort(key=lambda x: x[1], reverse=True)
        gen_best_params, gen_best_fitness = fitness_results[0]
        print(f"  => Best of this generation: fitness={gen_best_fitness:.2f}")

        # (4) Create the new generation (reproduction + elitism)
        population = reproduce_population(
            fitness_results,
            best_params_ever,       # Elitism: include the best global individual
            population_size,
            mutation_rate
        )

    # End of training: save the best global individual
    print(f"\n=== Training completed ===")
    print(f"Best global fitness: {best_fitness_ever:.2f}")
    if best_params_ever:
        with open("best_brain_params.json", "w") as f:
            json.dump(best_params_ever, f)
        print("Best final parameters saved in 'best_brain_params.json'.")


###################
# Evaluation (launch the game)
###################
def evaluate_params(params, num_games):
    """
    Injects 'params' into 'best_brain_params.json' so that perso.py uses them,
    plays 'num_games' games, and returns the average fitness (score + survival bonus).
    """
    # (1) Temporarily write params for the 'Perso' brain
    with open("best_brain_params.json", "w") as f:
        json.dump(params, f)

    total_fitness = 0
    for _ in range(num_games):
        env = GameEnvironment(training_mode=True)
        game = SpaceGame(env, wins_per_brain={})
        winner = game.run()

        # Retrieve the 'Perso' ship
        ship_perso = next((s for s in game.ships if s.id == "Perso"), None)
        if not ship_perso:
            # If it does not exist, fitness is zero
            continue

        # Score + survival bonus
        fitness = ship_perso.score
        if not ship_perso.is_destroyed:
            fitness += 50
        total_fitness += fitness

    if num_games > 0:
        return total_fitness / num_games
    else:
        return 0


###################
# Reproduction (selection, crossover, mutation)
###################
def reproduce_population(fitness_results, best_params_ever, population_size, mutation_rate):
    """
    Creates the new population by including the best global individual (elitism),
    then filling the rest via crossover/mutation with the best of this generation.
    """
    new_population = []

    # (1) Elitism: add the best global individual unchanged
    if best_params_ever is not None:
        new_population.append(best_params_ever.copy())

    # (2) Selection: take the best half
    half = len(fitness_results) // 2
    best_half = fitness_results[:half]
    selected_params = [x[0] for x in best_half]

    # (3) Fill the population
    while len(new_population) < population_size:
        parent1 = random.choice(selected_params)
        parent2 = random.choice(selected_params)
        child = crossover(parent1, parent2)
        mutate(child, mutation_rate)
        new_population.append(child)

    return new_population


def crossover(params1, params2):
    """ Simple crossover: average for each parameter. """
    child = {}
    for k in params1:
        child[k] = (params1[k] + params2[k]) / 2.0
    return child

def mutate(params, mutation_rate):
    """ Random mutation in [-0.2, +0.2], with optional clamping if needed. """
    for k in params:
        if random.random() < mutation_rate:
            variation = random.uniform(-0.2, 0.2)
            params[k] += variation

    # Example: optional clamping
    if 'distance_weight' in params:
        params['distance_weight'] = max(0.1, min(5.0, params['distance_weight']))
    if 'shoot_accuracy' in params:
        params['shoot_accuracy'] = max(1, min(40, params['shoot_accuracy']))
    if 'retreat_threshold' in params:
        params['retreat_threshold'] = max(0.0, min(1.0, params['retreat_threshold']))
    if 'aggressiveness' in params:
        params['aggressiveness'] = max(0.0, min(1.0, params['aggressiveness']))


###################
# Generation/initialization of parameters
###################
def random_params():
    """
    Creates a dictionary of random parameters
    (same structure as in GeneticHunterBrain.random_params()).
    """
    return {
        'distance_weight': random.uniform(0.5, 2.0),
        'shoot_accuracy': random.uniform(5, 20),
        'retreat_threshold': random.uniform(0.1, 0.5),
        'aggressiveness': random.uniform(0.0, 1.0),
    }


###################
# CSV Logging
###################
def create_csv_header_if_needed(csv_file_name):
    """ Creates the CSV with a header if it does not exist. """
    if not os.path.exists(csv_file_name):
        with open(csv_file_name, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Generation", "Individual", "Fitness", "Params"])

def log_to_csv(csv_file_name, generation, index, fitness, params):
    """ Appends a line [generation, index, fitness, JSON(params)] into the CSV. """
    with open(csv_file_name, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        params_str = json.dumps(params)
        writer.writerow([generation, index, f"{fitness:.2f}", params_str])


###################
# Main entry point
###################
if __name__ == "__main__":
    # Launches the genetic training with default parameters
    genetic_training(
        population_size=100,
        generations=100,
        mutation_rate=0.1
    )