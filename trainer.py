# genetic_trainer.py
import os
import json
import random

# On importe GameEnvironment et SpaceGame sans faire d'import circulaire
from space_game import GameEnvironment, SpaceGame

# Nombre de parties jouées pour évaluer la fitness d'un individu
GAMES_PER_INDIVIDUAL = 3

def genetic_training(
    population_size=10,
    generations=5,
    mutation_rate=0.1
):
    """
    Exécute un algorithme génétique pour entraîner le cerveau 'perso.py' 
    (classe GeneticHunterBrain) via 'space_game.py' sans le modifier.
    """

    # 1) Créer une population initiale de paramètres
    population = [random_params() for _ in range(population_size)]

    best_params_ever = None
    best_fitness_ever = float('-inf')

    for gen in range(generations):
        print(f"\n=== Génération {gen+1}/{generations} ===")
        # 2) Évaluation de la population
        fitness_results = []
        for i, params in enumerate(population):
            fitness = evaluate_params(params, GAMES_PER_INDIVIDUAL)
            fitness_results.append((params, fitness))
            print(f"  Individu #{i+1}: fitness={fitness:.2f}")

        # Trier par fitness décroissante
        fitness_results.sort(key=lambda x: x[1], reverse=True)

        # Meilleur individu de la génération
        gen_best_params, gen_best_fitness = fitness_results[0]
        if gen_best_fitness > best_fitness_ever:
            best_params_ever = gen_best_params
            best_fitness_ever = gen_best_fitness

        print(f"  => Meilleur individu de la génération: fitness={gen_best_fitness:.2f}")

        # 3) Sélection & Reproduction
        population = reproduce_population(
            fitness_results,
            population_size,
            mutation_rate
        )

    # Après toutes les générations, on sauvegarde les meilleurs params
    print(f"\n=== Entraînement terminé ===")
    print(f"Meilleure fitness globale: {best_fitness_ever:.2f}")
    if best_params_ever:
        with open("best_brain_params.json", "w") as f:
            json.dump(best_params_ever, f)
        print("Meilleurs paramètres sauvegardés dans 'best_brain_params.json'.")

def evaluate_params(params, num_games):
    """
    Joue 'num_games' parties en mode training, 
    chaque fois en injectant 'params' dans best_brain_params.json.
    Calcule une fitness (ex: score moyen).
    """
    # On écrit 'params' dans best_brain_params.json
    with open("best_brain_params.json", "w") as f:
        json.dump(params, f)

    total_fitness = 0
    for _ in range(num_games):
        # Crée l'environnement en mode training
        env = GameEnvironment(training_mode=True)
        wins_per_brain = {}
        # Lance le jeu (SpaceGame), qui chargera le brain 'perso.py' 
        # et lira best_brain_params.json
        game = SpaceGame(env, wins_per_brain)
        winner = game.run()

        # On recherche le vaisseau 'Perso' pour lire son score
        # (le code space_game.py stocke tous les ships dans game.ships)
        ship_perso = next((s for s in game.ships if s.id == "Perso"), None)
        if not ship_perso:
            # Pas trouvé => Fitness nulle
            continue

        # Par exemple : fitness = score + bonus si survie
        fitness = ship_perso.score
        if not ship_perso.is_destroyed:
            fitness += 50  # petit bonus si survit
        total_fitness += fitness

    return total_fitness / num_games if num_games > 0 else 0

def reproduce_population(fitness_results, population_size, mutation_rate):
    """
    Sélectionne, croise et mute pour recréer une population de taille `population_size`.
    """
    # Sélection : on prend la meilleure moitié
    half = len(fitness_results) // 2
    best_half = fitness_results[:half]
    selected_params = [item[0] for item in best_half]

    new_population = []
    while len(new_population) < population_size:
        parent1 = random.choice(selected_params)
        parent2 = random.choice(selected_params)
        child = crossover(parent1, parent2)
        mutate(child, mutation_rate)
        new_population.append(child)

    return new_population

def crossover(params1, params2):
    """
    Crossover simple: on fait la moyenne de chaque paramètre.
    """
    child = {}
    for k in params1:
        child[k] = (params1[k] + params2[k]) / 2.0
    return child

def mutate(params, mutation_rate):
    """
    Mutation: on modifie légèrement les valeurs avec une prob mutation_rate.
    """
    for k in params:
        if random.random() < mutation_rate:
            # Variation +/- 0.2 => ajustez selon vos besoins
            variation = random.uniform(-0.2, 0.2)
            params[k] += variation
            # Exemple de bornes (adaptez si nécessaire)
            if k == 'distance_weight':
                params[k] = max(0.1, min(5.0, params[k]))
            elif k == 'shoot_accuracy':
                params[k] = max(1, min(40, params[k]))
            elif k == 'retreat_threshold':
                params[k] = max(0.0, min(1.0, params[k]))
            elif k == 'aggressiveness':
                params[k] = max(0.0, min(1.0, params[k]))

def random_params():
    """
    Crée un dictionnaire de paramètres aléatoires 
    (même structure que dans GeneticHunterBrain.random_params()).
    """
    return {
        'distance_weight': random.uniform(0.5, 2.0),
        'shoot_accuracy': random.uniform(5, 20),
        'retreat_threshold': random.uniform(0.1, 0.5),
        'aggressiveness': random.uniform(0.0, 1.0)
    }

if __name__ == "__main__":
    # Lance l'entraînement génétique
    genetic_training(
        population_size=100,
        generations=100,
        mutation_rate=0.1
    )