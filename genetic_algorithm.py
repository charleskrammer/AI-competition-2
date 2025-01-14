# genetic_algorithm.py
import random
import math
from space_game import SpaceGame, GameEnvironment
from helpers import GameEngine
from brains.perso import GeneticHunterBrain

class GeneticAlgorithm:
    def __init__(
        self,
        population_size=20,
        mutation_rate=0.1,
        generations=100,
        elite_size=2
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.elite_size = elite_size

        # Initialisation de la population
        self.population = [GeneticHunterBrain() for _ in range(population_size)]

    def evolve(self, environment, num_games_per_individual=3):
        """
        Lance l'évolution génétique.
        :param environment: l'environnement de jeu (GameEnvironment).
        :param num_games_per_individual: nombre de parties à jouer pour évaluer un individu.
        :return: le meilleur cerveau trouvé.
        """
        best_brain = None
        best_score = -float('inf')

        for generation in range(self.generations):
            print(f"\n=== Generation {generation + 1}/{self.generations} ===")
            fitness_scores = []

            # 1) Évaluer chaque cerveau
            for brain in self.population:
                fitness = self.evaluate_brain(brain, environment, num_games_per_individual)
                fitness_scores.append((brain, fitness))

            # 2) Trier par fitness décroissant
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            current_best_brain, current_best_score = fitness_scores[0]

            # Mémoriser le meilleur global
            if current_best_score > best_score:
                best_brain = current_best_brain
                best_score = current_best_score

            print(f" => Best brain of Gen {generation+1} = {current_best_brain.id} | Fitness = {current_best_score:.2f}")

            # 3) Sélection (on garde l'élite + quelques autres)
            selected_brains = [b for (b, _) in fitness_scores[: self.elite_size]]
            # On complète avec la première moitié
            half = len(fitness_scores) // 2
            selected_brains += [b for (b, _) in fitness_scores[self.elite_size:half]]

            # 4) Reproduction
            new_population = []
            while len(new_population) < self.population_size:
                parent1 = random.choice(selected_brains)
                parent2 = random.choice(selected_brains)
                child_params = self.crossover(parent1.params, parent2.params)
                self.mutate(child_params)
                child_brain = GeneticHunterBrain(params=child_params)
                new_population.append(child_brain)

            self.population = new_population

        return best_brain

    def evaluate_brain(self, brain, environment, num_games):
        """
        Joue num_games parties avec un individu (un cerveau),
        calcule une fitness basée sur plusieurs critères.
        """
        total_fitness = 0
        for _ in range(num_games):
            engine = GameEngine(environment)
            # run_single_game doit renvoyer un dict ou un objet contenant :
            #   score, kills, survived (bool), etc.
            result = engine.run_single_game(brain)
            
            # Par exemple, on définit la fitness comme un mélange de :
            #   - score final
            #   - nb d'ennemis détruits
            #   - survie (1 si survécu, 0 sinon)
            fitness = result['score'] + (result['kills'] * 50)
            if result['survived']:
                fitness += 100  # bonus si on est encore en vie
            total_fitness += fitness

        return total_fitness / num_games

    @staticmethod
    def crossover(params1, params2):
        """
        Crossover plus avancé : on fait la moyenne des deux valeurs pour chaque paramètre.
        """
        child = {}
        for key in params1:
            child[key] = (params1[key] + params2[key]) / 2.0
        return child

    def mutate(self, params):
        """
        Mutation : on applique de petites variations aléatoires dans l'intervalle [-0.1, 0.1].
        Puis on clip à [0, 1] si besoin (dépend de votre usage).
        """
        for key in params:
            if random.random() < self.mutation_rate:
                mutation_value = random.uniform(-0.1, 0.1)
                params[key] += mutation_value
                # Exemples de clipping, selon la logique
                if key in ['retreat_threshold', 'aggressiveness', 'brake_usage']:
                    params[key] = max(0.0, min(1.0, params[key]))
                elif key == 'distance_weight':
                    params[key] = max(0.1, min(5.0, params[key]))
                elif key == 'shoot_accuracy':
                    params[key] = max(1.0, min(30.0, params[key]))
                # etc. (à adapter selon vos besoins)