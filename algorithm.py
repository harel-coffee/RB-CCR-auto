import numpy as np

from sklearn.model_selection import StratifiedKFold


def distance(x, y):
    return np.sum(np.abs(x - y))


def taxicab_sample(n, r):
    sample = []

    for _ in range(n):
        spread = r - np.sum([np.abs(x) for x in sample])
        sample.append(spread * (2 * np.random.rand() - 1))

    return np.random.permutation(sample)


class CCR:
    def __init__(self, energy=0.25, scaling=0.0, n=None):
        self.energy = energy
        self.scaling = scaling
        self.n = n

    def fit_sample(self, X, y):
        classes = np.unique(y)
        sizes = [sum(y == c) for c in classes]

        assert len(classes) == len(set(sizes)) == 2

        minority_class = classes[np.argmin(sizes)]
        majority_class = classes[np.argmax(sizes)]
        minority = X[y == minority_class]
        majority = X[y == majority_class]

        if self.n is None:
            n = len(majority) - len(minority)
        else:
            n = self.n

        energy = self.energy * (X.shape[1] ** self.scaling)

        distances = np.zeros((len(minority), len(majority)))

        for i in range(len(minority)):
            for j in range(len(majority)):
                distances[i][j] = distance(minority[i], majority[j])

        radii = np.zeros(len(minority))
        translations = np.zeros(majority.shape)

        for i in range(len(minority)):
            minority_point = minority[i]
            remaining_energy = energy
            r = 0.0
            sorted_distances = np.argsort(distances[i])
            current_majority = 0

            while True:
                if current_majority == len(majority):
                    if current_majority == 0:
                        radius_change = remaining_energy / (current_majority + 1.0)
                    else:
                        radius_change = remaining_energy / current_majority

                    r += radius_change

                    break

                radius_change = remaining_energy / (current_majority + 1.0)

                if distances[i, sorted_distances[current_majority]] >= r + radius_change:
                    r += radius_change

                    break
                else:
                    if current_majority == 0:
                        last_distance = 0.0
                    else:
                        last_distance = distances[i, sorted_distances[current_majority - 1]]

                    radius_change = distances[i, sorted_distances[current_majority]] - last_distance
                    r += radius_change
                    remaining_energy -= radius_change * (current_majority + 1.0)
                    current_majority += 1

            radii[i] = r

            for j in range(current_majority):
                majority_point = majority[sorted_distances[j]]
                d = distances[i, sorted_distances[j]]

                if d < 1e-20:
                    majority_point += (1e-6 * np.random.rand(len(majority_point)) + 1e-6) * \
                                      np.random.choice([-1.0, 1.0], len(majority_point))
                    d = distance(minority_point, majority_point)

                translation = (r - d) / d * (majority_point - minority_point)
                translations[sorted_distances[j]] += translation

        majority += translations

        appended = []

        for i in range(len(minority)):
            minority_point = minority[i]
            synthetic_samples = int(np.round(1.0 / (radii[i] * np.sum(1.0 / radii)) * n))
            r = radii[i]

            for _ in range(synthetic_samples):
                appended.append(minority_point + taxicab_sample(len(minority_point), r))

        return np.concatenate([majority, minority, appended]), \
               np.concatenate([np.tile([majority_class], len(majority)),
                               np.tile([minority_class], len(minority) + len(appended))])


class CCRSelection:
    def __init__(self, classifier, measure, n_splits=5, energies=(0.25,), scaling_factors=(0.0,), n=None):
        self.classifier = classifier
        self.measure = measure
        self.n_splits = n_splits
        self.energies = energies
        self.scaling_factors = scaling_factors
        self.n = n
        self.selected_energy = None
        self.selected_scaling = None
        self.skf = StratifiedKFold(n_splits=n_splits)

    def fit_sample(self, X, y):
        self.skf.get_n_splits(X, y)

        best_score = -np.inf

        for energy in self.energies:
            for scaling in self.scaling_factors:
                scores = []

                for train_idx, test_idx in self.skf.split(X, y):
                    X_train, y_train = CCR(energy=energy, scaling=scaling, n=self.n).\
                        fit_sample(X[train_idx], y[train_idx])

                    classifier = self.classifier.fit(X_train, y_train)
                    predictions = classifier.predict(X[test_idx])
                    scores.append(self.measure(y[test_idx], predictions))

                score = np.mean(scores)

                if score > best_score:
                    self.selected_energy = energy
                    self.selected_scaling = scaling

                    best_score = score

        return CCR(energy=self.selected_energy, scaling=self.selected_scaling, n=self.n).fit_sample(X, y)
