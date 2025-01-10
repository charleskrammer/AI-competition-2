import random
from brains.perso import GeneticHunterBrain


class GeneticAlgorithm:
    def __init__(self, population_size=10, generations=50, mutation_rate=0.1):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.population = [GeneticHunterBrain() for _ in range(population_size)]

    def evaluate_population(self, game_engine):
        fitness_scores = {}
        for brain in self.population:
            score = game_engine.run_single_game(brain)
            fitness_scores[brain] = score
        return fitness_scores

    def select_parents(self, fitness_scores):
        sorted_brains = sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True)
        return [brain for brain, _ in sorted_brains[:self.population_size // 2]]

    def crossover(self, parent1, parent2):
        child_params = {}
        for key in parent1.params.keys():
            child_params[key] = random.choice([parent1.params[key], parent2.params[key]])
        return GeneticHunterBrain(child_params)

    def mutate(self, brain):
        if random.random() < self.mutation_rate:
            key = random.choice(list(brain.params.keys()))
            brain.params[key] += random.uniform(-0.1, 0.1)
        return brain

    def evolve(self, fitness_scores):
        parents = self.select_parents(fitness_scores)
        next_generation = []
        while len(next_generation) < self.population_size:
            parent1, parent2 = random.sample(parents, 2)
            child = self.crossover(parent1, parent2)
            child = self.mutate(child)
            next_generation.append(child)
        self.population = next_generation

    def run(self, game_engine):
        for generation in range(self.generations):
            fitness_scores = self.evaluate_population(game_engine)
            best_score = max(fitness_scores.values())
            print(f"Generation {generation}: Best Score = {best_score}")
            self.evolve(fitness_scores)