import numpy as np


def distance(x, y, p_norm=1):
    return np.sum(np.abs(x - y) ** p_norm) ** (1 / p_norm)


def sample_inside_sphere(dimensionality, radius, p_norm=1):
    direction_unit_vector = (2 * np.random.rand(dimensionality) - 1)
    direction_unit_vector = direction_unit_vector / distance(direction_unit_vector, np.zeros(dimensionality), p_norm)

    return direction_unit_vector * np.random.rand() * radius


class CCR:
    def __init__(self, energy, p_norm=1, n=None):
        self.energy = energy
        self.p_norm = p_norm
        self.n = n

    def fit_sample(self, X, y):
        classes = np.unique(y)
        sizes = [sum(y == c) for c in classes]
        minority_class = classes[np.argmin(sizes)]

        minority_points = X[y == minority_class].copy()
        majority_points = X[y != minority_class].copy()
        minority_labels = y[y == minority_class].copy()
        majority_labels = y[y != minority_class].copy()

        if self.n is None:
            n = len(majority_points) - len(minority_points)
        else:
            n = self.n

        distances = np.zeros((len(minority_points), len(majority_points)))

        for i in range(len(minority_points)):
            for j in range(len(majority_points)):
                distances[i][j] = distance(minority_points[i], majority_points[j], self.p_norm)

        radii = np.zeros(len(minority_points))

        translations = np.zeros(majority_points.shape)
        kept_indices = np.full(len(majority_points), True)

        for i in range(len(minority_points)):
            minority_point = minority_points[i]
            remaining_energy = self.energy
            radius = 0.0
            sorted_distances = np.argsort(distances[i])
            n_majority_points_within_radius = 0

            while True:
                if n_majority_points_within_radius == len(majority_points):
                    if n_majority_points_within_radius == 0:
                        radius_change = remaining_energy / (n_majority_points_within_radius + 1)
                    else:
                        radius_change = remaining_energy / n_majority_points_within_radius

                    radius += radius_change

                    break

                radius_change = remaining_energy / (n_majority_points_within_radius + 1)

                if distances[i, sorted_distances[n_majority_points_within_radius]] >= radius + radius_change:
                    radius += radius_change

                    break
                else:
                    if n_majority_points_within_radius == 0:
                        last_distance = 0.0
                    else:
                        last_distance = distances[i, sorted_distances[n_majority_points_within_radius - 1]]

                    radius_change = distances[i, sorted_distances[n_majority_points_within_radius]] - last_distance
                    radius += radius_change
                    remaining_energy -= radius_change * (n_majority_points_within_radius + 1)
                    n_majority_points_within_radius += 1

            radii[i] = radius

            for j in range(n_majority_points_within_radius):
                majority_point = majority_points[sorted_distances[j]]
                d = distances[i, sorted_distances[j]]

                while d < 1e-20:
                    majority_point += (1e-6 * np.random.rand(len(majority_point)) + 1e-6) * \
                                      np.random.choice([-1.0, 1.0], len(majority_point))
                    d = distance(minority_point, majority_point)

                translation = (radius - d) / d * (majority_point - minority_point)
                translations[sorted_distances[j]] += translation

                kept_indices[sorted_distances[j]] = False

        majority_points += translations

        appended = []

        for i in range(len(minority_points)):
            minority_point = minority_points[i]
            n_synthetic_samples = int(np.round(1.0 / (radii[i] * np.sum(1.0 / radii)) * n))
            r = radii[i]

            for _ in range(n_synthetic_samples):
                appended.append(minority_point + sample_inside_sphere(len(minority_point), r, self.p_norm))

        if len(appended) > 0:
            points = np.concatenate([majority_points, minority_points, appended])
            labels = np.concatenate([majority_labels, minority_labels, np.tile([minority_class], len(appended))])
        else:
            points = np.concatenate([majority_points, minority_points])
            labels = np.concatenate([majority_labels, minority_labels])

        return points, labels
