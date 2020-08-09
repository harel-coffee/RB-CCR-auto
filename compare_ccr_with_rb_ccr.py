import datasets
import numpy as np
import pandas as pd

from collections import OrderedDict
from merge import RESULTS_PATH
from scipy.stats import wilcoxon


ALGORITHMS = ['CCR', 'RB-CCR-CV']
CLASSIFIERS = ['CART', 'KNN', 'L-SVM', 'R-SVM', 'P-SVM', 'LR', 'NB', 'R-MLP', 'L-MLP']
METRICS = ['AUC', 'F-measure', 'G-mean']
P_VALUE = 0.10


def load_final_dict(classifier, metric):
    csv_path = RESULTS_PATH / 'results_final.csv'

    df = pd.read_csv(csv_path)
    df = df[(df['Classifier'] == classifier) & (df['Metric'] == metric)]

    measurements = OrderedDict()

    for algorithm in ALGORITHMS:
        measurements[algorithm] = []

        for dataset in datasets.names():
            scores = df[(df['Resampler'] == algorithm) & (df['Dataset'] == dataset)]['Score']

            assert len(scores) == 10

            measurements[algorithm].append(np.mean(scores))

    return measurements


if __name__ == '__main__':
    for classifier in CLASSIFIERS:
        row = [classifier]

        for metric in METRICS:
            d = load_final_dict(classifier, metric)

            x = d['CCR']
            y = d['RB-CCR-CV']

            p = np.round(wilcoxon(x, y, alternative='less')[1], 4)

            ccr_wins = 0
            rb_ccr_wins = 0
            ties = 0

            for ccr_i, rb_ccr_i in zip(x, y):
                if ccr_i > rb_ccr_i:
                    ccr_wins += 1
                elif rb_ccr_i > ccr_i:
                    rb_ccr_wins += 1
                else:
                    ties += 1

            if p <= P_VALUE:
                p = '\\textbf{' + f'{p:.4f}' + '}'
            else:
                p = f'{p:.4f}'

            row += [ccr_wins, rb_ccr_wins, p]

        print(' & '.join([str(r) for r in row]) + ' \\\\')
