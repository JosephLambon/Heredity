import csv
import itertools
import sys
import numpy as np

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]

def get_number_genes(person, one_gene, two_genes):
    if person in one_gene:
        return 1
    elif person in two_genes:
        return 2
    else:
        return 0

def prob_of_passing(numGenes):
    if numGenes == 0:
        return PROBS["mutation"]
    elif numGenes == 1:
        return 0.5
    else:
        return (1 - PROBS["mutation"])


NO_MUTATION = 1 - PROBS["mutation"]
MUTATES  = PROBS["mutation"]

def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.
    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    probJoint = 1
    for key, person in people.items():
        # Find how many genes this person has
        ownGenes = get_number_genes(person["name"], one_gene, two_genes)
        if person["mother"] == None and person["father"] == None:
            # 1. Neither parent has gene
            probGenes = PROBS['gene'][ownGenes]
        else:
            # Get number of genes each parent has
            fatherGenes = get_number_genes(person["father"], one_gene, two_genes)
            motherGenes = get_number_genes(person["mother"], one_gene, two_genes)
            # Calculate prob of parent passing gene
            fatherProb = prob_of_passing(fatherGenes) # Probability the father passes gene to child
            motherProb = prob_of_passing(motherGenes) # Probability the mother passes gene to child

            # Calculate the probability of the person having specified no. genes
            if ownGenes == 0:
                probGenes = (1 - fatherProb) * (1 - motherProb)
            if ownGenes == 1:
                probGenes = (motherProb * (1 - fatherProb)) + (fatherProb * (1 - motherProb))
            if ownGenes == 2:
                probGenes = (motherProb * fatherProb)
        # Calculate the probability of the person showing the trait
        if person["name"] in have_trait:
            probTrait = PROBS["trait"][ownGenes][True]
        else:
            probTrait = PROBS["trait"][ownGenes][False]

        # Calculate probJoint
        probJoint *= probGenes * probTrait

    return probJoint


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    for person in probabilities.keys():
        ownGenes = get_number_genes(person, one_gene, two_genes) # Get no. genes for person
        trait = person in have_trait # True or false if/not in have_trait
        # Add 'p' to each relevant distribution
        if trait:
            probabilities[person]["trait"][True] += p
        else:
            probabilities[person]["trait"][False] += p
        probabilities[person]["gene"][ownGenes] += p


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    def norm_dict(p):
        total = np.sum(list(p.values()))
        return {a: b / total for a,b in p.items()}

    for person in probabilities:
         probabilities[person]["gene"] = norm_dict(probabilities[person]["gene"])
         probabilities[person]["trait"] = norm_dict(probabilities[person]["trait"])

if __name__ == "__main__":
    main()
