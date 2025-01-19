# genetic_trainer.py
import os
import csv
import json
import random

from space_game import GameEnvironment, SpaceGame

# Nombre de parties jouées pour évaluer la fitness d'un individu
GAMES_PER_INDIVIDUAL = 3

###################
# Algorithme génétique principal
###################
def genetic_training(population_size=100, generations=100, mutation_rate=0.1):
    """
    Entraîne le cerveau 'GeneticHunterBrain' (perso.py) via 'space_game.py',
    en loguant chaque individu (fitness, params) dans un fichier CSV
    et en sauvegardant le meilleur individu global dans best_brain_params.json.
    """

    # (1) Population initiale
    population = [random_params() for _ in range(population_size)]

    # Variables pour suivre le meilleur individu absolu
    best_params_ever = None
    best_fitness_ever = float('-inf')

    # Fichier CSV de logs
    LOG_FILE = "training_logs.csv"
    create_csv_header_if_needed(LOG_FILE)

    for gen in range(generations):
        print(f"\n=== Génération {gen+1}/{generations} ===")

        # (2) Évaluation de la population
        fitness_results = []
        for i, params in enumerate(population):
            fitness = evaluate_params(params, GAMES_PER_INDIVIDUAL)
            fitness_results.append((params, fitness))
            print(f"  Individu #{i+1}: fitness={fitness:.2f}")

            # Log dans le CSV
            log_to_csv(LOG_FILE, gen+1, i+1, fitness, params)

            # Mise à jour du meilleur absolu (record global)
            if fitness > best_fitness_ever:
                best_fitness_ever = fitness
                best_params_ever = params.copy()
                print(f"    => Nouveau record absolu ! fitness={fitness:.2f}")

        # (3) Tri pour identifier le meilleur de la génération
        fitness_results.sort(key=lambda x: x[1], reverse=True)
        gen_best_params, gen_best_fitness = fitness_results[0]
        print(f"  => Meilleur de la génération: fitness={gen_best_fitness:.2f}")

        # (4) Création de la nouvelle génération (reproduction + élitisme)
        population = reproduce_population(
            fitness_results,
            best_params_ever,       # Élitisime : on inclut le meilleur global inchangé
            population_size,
            mutation_rate
        )

    # Fin de l’entraînement : sauvegarde du meilleur global
    print(f"\n=== Entraînement terminé ===")
    print(f"Meilleure fitness absolue: {best_fitness_ever:.2f}")
    if best_params_ever:
        with open("best_brain_params.json", "w") as f:
            json.dump(best_params_ever, f)
        print("Meilleurs paramètres finaux sauvegardés dans 'best_brain_params.json'.")


###################
# Évaluation (lancement du jeu)
###################
def evaluate_params(params, num_games):
    """
    Injecte 'params' dans best_brain_params.json pour que perso.py les lise,
    joue num_games parties, et retourne la fitness moyenne (score + bonus survie).
    """
    # 1) Écrit temporairement params pour le brain 'Perso'
    with open("best_brain_params.json", "w") as f:
        json.dump(params, f)

    total_fitness = 0
    for _ in range(num_games):
        env = GameEnvironment(training_mode=True)
        game = SpaceGame(env, wins_per_brain={})
        winner = game.run()

        # Récupère le vaisseau Perso
        ship_perso = next((s for s in game.ships if s.id == "Perso"), None)
        if not ship_perso:
            # S’il n’existe pas, fitness nulle
            continue

        # Score + bonus si survie
        fitness = ship_perso.score
        if not ship_perso.is_destroyed:
            fitness += 50
        total_fitness += fitness

    if num_games > 0:
        return total_fitness / num_games
    else:
        return 0


###################
# Reproduction (sélection, crossover, mutation)
###################
def reproduce_population(fitness_results, best_params_ever, population_size, mutation_rate):
    """
    Crée la nouvelle population en incluant le meilleur individu global (élitisme),
    puis en complétant via crossover/mutation avec les meilleurs de la génération courante.
    """
    new_population = []

    # (1) Élitisime : on ajoute le meilleur global inchangé
    if best_params_ever is not None:
        new_population.append(best_params_ever.copy())

    # (2) Sélection : on prend la meilleure moitié
    half = len(fitness_results) // 2
    best_half = fitness_results[:half]
    selected_params = [x[0] for x in best_half]

    # (3) Compléter la population
    while len(new_population) < population_size:
        parent1 = random.choice(selected_params)
        parent2 = random.choice(selected_params)
        child = crossover(parent1, parent2)
        mutate(child, mutation_rate)
        new_population.append(child)

    return new_population


def crossover(params1, params2):
    """ Crossover simple : moyenne de chaque paramètre. """
    child = {}
    for k in params1:
        child[k] = (params1[k] + params2[k]) / 2.0
    return child

def mutate(params, mutation_rate):
    """ Mutation aléatoire dans [-0.2, +0.2], avec bornes adaptées si besoin. """
    for k in params:
        if random.random() < mutation_rate:
            variation = random.uniform(-0.2, 0.2)
            params[k] += variation

    # Exemple : clamp optionnel
    if 'distance_weight' in params:
        params['distance_weight'] = max(0.1, min(5.0, params['distance_weight']))
    if 'shoot_accuracy' in params:
        params['shoot_accuracy'] = max(1, min(40, params['shoot_accuracy']))
    if 'retreat_threshold' in params:
        params['retreat_threshold'] = max(0.0, min(1.0, params['retreat_threshold']))
    if 'aggressiveness' in params:
        params['aggressiveness'] = max(0.0, min(1.0, params['aggressiveness']))

###################
# Génération/initialisation de paramètres
###################
def random_params():
    """
    Crée un dictionnaire de paramètres aléatoires 
    (même structure que dans GeneticHunterBrain.random_params()).
    """
    return {
        'distance_weight': random.uniform(0.5, 2.0),
        'shoot_accuracy': random.uniform(5, 20),
        'retreat_threshold': random.uniform(0.1, 0.5),
        'aggressiveness': random.uniform(0.0, 1.0),
    }

###################
# Logging CSV
###################
def create_csv_header_if_needed(csv_file_name):
    """ Crée le CSV avec un header s'il n'existe pas encore. """
    if not os.path.exists(csv_file_name):
        with open(csv_file_name, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Generation", "Individual", "Fitness", "Params"])

def log_to_csv(csv_file_name, generation, index, fitness, params):
    """ Ajoute une ligne [generation, index, fitness, JSON(params)] dans le CSV. """
    with open(csv_file_name, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        params_str = json.dumps(params)
        writer.writerow([generation, index, f"{fitness:.2f}", params_str])


###################
# Point d'entrée
###################
if __name__ == "__main__":
    # Lance l'entraînement génétique avec des paramètres par défaut
    genetic_training(
        population_size=100,
        generations=100,
        mutation_rate=0.1
    )