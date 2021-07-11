import os
import shutil

os.environ["CUDA_VISIBLE_DEVICES"]="-1"

import mutant_predictor
import predictor


import random
from datetime import datetime
from os.path import splitext

from eye_input import Eye
from eye_mutator import EyeMutator
from utils import print_archive

import numpy as np
import glob
from deap import base, creator, tools
from deap.tools.emo import selNSGA2


import archive_manager
from individual import Individual
from properties import NGEN, POPSIZE, \
    INITIALPOP, DATASET, RESEEDUPPERBOUND, \
    UNITY_STANDARD_IMGS_PATH, MUT_MODELS, MODELS
from sikulix import start_sikulix_server, set_sikulix_scripts_home


sample_list = glob.glob(DATASET + '/*.jpg')
random.shuffle(sample_list)
starting_seeds = sample_list[:POPSIZE]
assert(len(starting_seeds) == POPSIZE)

# DEAP framework setup.
toolbox = base.Toolbox()
# Define a bi-objective fitness function.
creator.create("FitnessMulti", base.Fitness, weights=(-1.0, 1.0))
# Define the individual.
creator.create("Individual", Individual, fitness=creator.FitnessMulti)


def fetch_seed(image_path):
    path = splitext(image_path)
    json_path = path[0]+".json"
    return json_path, image_path


def generate_sample(seed):
    json_path, image_path = fetch_seed(seed)
    return Eye(json_path, image_path)


def generate_individual():
    Individual.COUNT += 1

    if INITIALPOP == 'random':
        # Choose randomly a file in the original dataset.
        chosen_seed = random.choice(starting_seeds)
        Individual.SEEDS.add(chosen_seed)
    elif INITIALPOP == 'seeded':
        # Choose sequentially the inputs from the seed list.
        # NOTE: number of seeds should be no less than the initial population
        assert (len(starting_seeds) == POPSIZE)
        chosen_seed = starting_seeds[Individual.COUNT - 1]
        Individual.SEEDS.add(chosen_seed)
    else:
        print("Select a valid population generation strategy")
        exit()

    # now a seed is a jpg file path
    new_sample = generate_sample(chosen_seed)

    #print("generated individual sample" + str(Individual.COUNT))

    EyeMutator(new_sample).mutate()

    #print("mutated individual sample" + str(Individual.COUNT))

    individual = creator.Individual(new_sample, chosen_seed)

    return individual


def reseed_individual(seeds):
    Individual.COUNT += 1
    # Chooses randomly the seed among the ones that are not covered by the archive
    #if len(starting_seeds) > len(seeds):
    #    chosen_seed = random.sample(set(starting_seeds) - seeds, 1)[0]
    #else:
    chosen_seed = random.choice(starting_seeds)

    new_sample = generate_sample(chosen_seed)

    EyeMutator(new_sample).mutate()

    individual = creator.Individual(new_sample, chosen_seed)
    return individual


# Evaluate an individual.
def evaluate_individual(individual, current_solution):
    individual.evaluate(current_solution)
    return individual.ff, individual.sparseness


def mutate_individual(individual):
    Individual.COUNT += 1
    EyeMutator(individual.member).mutate()
    individual.reset()


toolbox.register("individual", generate_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate_individual)
toolbox.register("select", selNSGA2)
toolbox.register("mutate", mutate_individual)

def pre_evaluate_batch(invalid_ind):
    batch_img = [i.member.img_np for i in invalid_ind]
    #TODO: refactor reshaping
    batch_img = np.reshape(batch_img, (-1, 36, 60, 1))

    batch_head_pose = [i.member.h_angles_rad_np for i in invalid_ind]
    batch_head_pose = np.reshape(batch_head_pose, (-1, 2))

    batch_label = np.array([i.member.eye_angles_rad for i in invalid_ind])

    for i in range(len(glob.glob(MUT_MODELS + '/*.h5'))):
        predictions, confidences = (mutant_predictor.Predictor.predict(i, batch_img,
                                                                       batch_head_pose, batch_label))

        for ind, confidence, prediction in zip(invalid_ind, confidences, predictions):
            ind.member.diff.append(confidence)
            ind.member.predicted_label.append(prediction)

    for i in range(len(glob.glob(MODELS + '/*.h5'))):
        predictions, confidences = (predictor.Predictor.predict(i, batch_img,
                                                                batch_head_pose, batch_label))

        for ind, confidence, prediction in zip(invalid_ind, confidences, predictions):
            ind.member.diff_original.append(confidence)
            ind.member.predicted_label_original.append(prediction)



def main(rand_seed=None):
    random.seed(rand_seed)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "min", "max", "avg", "std"

    # Generate initial population.
    print("### Initializing population ....")
    population = toolbox.population(n=POPSIZE)

    # Evaluate the individuals with an invalid fitness.
    # Note: the fitnesses are all invalid before the first iteration since they have not been evaluated
    invalid_ind = [ind for ind in population]

    to_evaluate_ind = [ind for ind in population if ind.ff is None]
    pre_evaluate_batch(to_evaluate_ind)

    # Note: the sparseness is calculated wrt the archive.
    # Therefore, we pass to the evaluation method the current archive.
    fitnesses = [toolbox.evaluate(i, archive.get_archive()) for i in invalid_ind]
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    # Update archive with the individuals on the decision boundary.
    for ind in population:
        if ind.filterin:
            archive.update_archive(ind)

    print("### Number of Individuals generated in the initial population: " + str(Individual.COUNT))

    # This is just to assign the crowding distance to the individuals (no actual selection is done).
    population = toolbox.select(population, len(population))

    record = stats.compile(population)
    logbook.record(gen=0, evals=len(invalid_ind), **record)
    print(logbook.stream)

    # Begin the generational process
    for gen in range(1, NGEN):
        # Vary the population.
        offspring = tools.selTournamentDCD(population, len(population))
        offspring = [toolbox.clone(ind) for ind in offspring]

        # Reseeding
        if len(archive.get_archive()) > 0:
            seed_range = random.randrange(1, RESEEDUPPERBOUND)
            candidate_seeds = archive.archived_seeds
            for i in range(seed_range):
                population[len(population) - i - 1] = reseed_individual(candidate_seeds)

            for i in range(len(population)):
                if population[i].filterout == True:
                    population[i] = reseed_individual(candidate_seeds)

        # Mutation.
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values

        # Evaluate the individuals
        # NOTE: all individuals in both population and offspring are evaluated to assign crowding distance.
        invalid_ind = [ind for ind in population + offspring]
        pre_evaluate_batch(invalid_ind)

        fitnesses = [toolbox.evaluate(i, archive.get_archive()) for i in invalid_ind]

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        for ind in population + offspring:
            if ind.filterin:
                archive.update_archive(ind)

        # Select the next generation population
        population = toolbox.select(population + offspring, POPSIZE)

        if gen % 300 == 0:
            archive.create_report(gen)

        # Update the statistics with the new population
        if gen % 1 == 0:
            record = stats.compile(population)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)
            print(logbook.stream)

    print(logbook.stream)

    return population


if __name__ == "__main__":
    # Start sikulix server
    # start_sikulix_server()
    # set_sikulix_scripts_home()
    #
    # archive = archive_manager.Archive()
    # pop = main()
    #
    # print_archive(archive.get_archive())
    # archive.create_report('final')
    # print("GAME OVER")

    print("Starting")
    # start_sikulix_server()
    print("Sikulix server started")
    set_sikulix_scripts_home()
    print("Sikulix scripts home set")

    try:
        print("Getting to Archive")
        archive = archive_manager.Archive()
        print("getting to main")
        pop = main()
    except:
        shutil.rmtree(UNITY_STANDARD_IMGS_PATH)
        if not os.path.exists(UNITY_STANDARD_IMGS_PATH):
            os.mkdir(UNITY_STANDARD_IMGS_PATH)
        raise

    print_archive(archive.get_archive())
    archive.create_report('final')
    print("GAME OVER")

    # datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)