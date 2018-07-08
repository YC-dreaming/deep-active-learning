import numpy as np
from torchvision import datasets, transforms
import torch
from datetime import datetime
from query_strategies import RandomSampling, LeastConfidence, MarginSampling, EntropySampling, \
                                LeastConfidenceDropout, MarginSamplingDropout, EntropySamplingDropout, \
                                KMeansSampling, KCenterGreedy, BALDDropout, CoreSet, \
                                AdversarialBIM, AdversarialDeepFool, ActiveLearningByLearning

import ipdb

# parameters
SEED = 5

NUM_INIT_LB = 10000
NUM_QUERY = 1000
NUM_ROUND = 10

args = {'n_epoch': 10, 'transform': transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]),
        'loader_tr_args':{'batch_size': 64, 'num_workers': 1},
        'loader_te_args':{'batch_size': 1000, 'num_workers': 1},
        'optimizer_args':{'lr': 0.01, 'momentum': 0.5}}

# set seed
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.backends.cudnn.enabled = False

# load dataset
raw_tr = datasets.MNIST('./MNIST', train=True, download=True)
raw_te = datasets.MNIST('./MNIST', train=False, download=True)
# raw_tr = datasets.FashionMNIST('./FashionMNIST', train=True, download=True)
# raw_te = datasets.FashionMNIST('./FashionMNIST', train=False, download=True)
X_tr = raw_tr.train_data[:40000]
Y_tr = raw_tr.train_labels[:40000]
X_te = raw_te.test_data
Y_te = raw_te.test_labels

# start experiment
n_pool = len(Y_tr)
n_test = len(Y_te)
print('number of labeled pool: {}'.format(NUM_INIT_LB))
print('number of unlabeled pool: {}'.format(n_pool - NUM_INIT_LB))
print('number of testing pool: {}'.format(n_test))

# generate initial label
idxs_lb = np.zeros(n_pool, dtype=bool)
idxs_tmp = np.arange(n_pool)
np.random.shuffle(idxs_tmp)
idxs_lb[idxs_tmp[:NUM_INIT_LB]] = True

# strategy = RandomSampling(X_tr, Y_tr, idxs_lb, args)
# strategy = LeastConfidence(X_tr, Y_tr, idxs_lb, args)
# strategy = MarginSampling(X_tr, Y_tr, idxs_lb, args)
# strategy = EntropySampling(X_tr, Y_tr, idxs_lb, args)
# strategy = LeastConfidenceDropout(X_tr, Y_tr, idxs_lb, args, n_drop=10)
# strategy = MarginSamplingDropout(X_tr, Y_tr, idxs_lb, args, n_drop=10)
# strategy = EntropySamplingDropout(X_tr, Y_tr, idxs_lb, args, n_drop=10)
# strategy = KMeansSampling(X_tr, Y_tr, idxs_lb, args)
# strategy = KCenterGreedy(X_tr, Y_tr, idxs_lb, args)
# strategy = BALDDropout(X_tr, Y_tr, idxs_lb, args, n_drop=10)
# strategy = CoreSet(X_tr, Y_tr, idxs_lb, args)
# strategy = AdversarialBIM(X_tr, Y_tr, idxs_lb, args, eps=0.05)
# strategy = AdversarialDeepFool(X_tr, Y_tr, idxs_lb, args, max_iter=50)
albl_list = [MarginSampling(X_tr, Y_tr, idxs_lb, args),
             KMeansSampling(X_tr, Y_tr, idxs_lb, args)]
strategy = ActiveLearningByLearning(X_tr, Y_tr, idxs_lb, args, strategy_list=albl_list, delta=0.1)


print('SEED {}'.format(SEED))
print(type(strategy).__name__)
strategy.train()
P = strategy.predict(X_te, Y_te)
acc = np.zeros(NUM_ROUND+1)
acc[0] = 1.0 * (Y_te==P).sum().item() / len(Y_te)
print('Round 0\ntesting accuracy {}'.format(acc[0]))
T = np.zeros(NUM_ROUND)

for rd in range(1, NUM_ROUND+1):
    print('Round {}'.format(rd))

    t_start = datetime.now()
    q_idxs = strategy.query(NUM_QUERY)
    t_end = datetime.now()
    T[rd-1] = (t_end - t_start).total_seconds()

    idxs_lb[q_idxs] = True
    strategy.update(idxs_lb)
    strategy.train()
    P = strategy.predict(X_te, Y_te)
    acc[rd] = 1.0 * (Y_te==P).sum().item() / len(Y_te)
    print('testing accuracy {}'.format(acc[rd]))

print('SEED {}'.format(SEED))
print(type(strategy).__name__)
print(T)
print(T.mean())
print(acc)
