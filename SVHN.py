from torch.utils.tensorboard import SummaryWriter

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import torchvision
import copy
import matplotlib.pyplot as plt
import numpy as np
import pickle
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter()

with open('MNIST_network', 'rb') as handle:
    best_model = pickle.load(handle)

batch_size = 200


SVHN_train = datasets.SVHN("./", split='train', download=True)

'''
means = SVHN_train.mean(axis = (3,1,0)) / 255
stds = SVHN_train.data.std(axis = (3,1,0)) / 255
'''


preprocessTest = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.4376821, 0.4437697, 0.47280442), (0.19803012, 0.20101562, 0.19703614))
])

SVHN_test = datasets.SVHN("./", split='test', download=True, transform=preprocessTest)

test_loader = DataLoader(SVHN_test, shuffle=False)

# Run on test data
corr = 0
i = 0

for index, (image, label) in enumerate(test_loader):
    i +=1
    guess = torch.argmax(best_model(image), dim=-1)
    result = (guess == label).sum()
    corr += result.item()
    if 1 == (i%30):
        print("\r", "Right guess:", 100*corr/26032, "Tested pictures:", 100*i/26032,end="                                                         ")
correctness = 100*corr/26032
print("\n","Result on test:", correctness)
                    
