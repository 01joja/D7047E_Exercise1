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
import loadDataset
import os
from datetime import datetime, timedelta
import moveDataset

batchSize = 200
epochs = 10
learningRate = 0.001

#gets the paths to the different datasets
val1Path = moveDataset.getVal1Path()
val2Path = moveDataset.getVal2Path()
trainPath = moveDataset.getTrainPath()

transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize([400,400]),
    transforms.RandomCrop([360,360]),
    transforms.ToTensor(),
    transforms.Normalize((0.4823), (0.2230)),
])

transformVal = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize([360,360]),
    transforms.ToTensor(),
    transforms.Normalize((0.4823), (0.2230)),
])

continueTraning = False
testDrive = False
while True:
    val = input("Continue training?(Yes/No):")
    if val == "Yes":
        continueTraning = True
        break
    elif val == "No":
        continueTraning = False
        break
    print("Answer Yes or No")
print("Load dataset")
try:
    val1 = loadDataset.PneumoniaDataSet(val1Path, transform = transformVal)
    val2 = loadDataset.PneumoniaDataSet(val2Path, transform = transformVal)
    train = loadDataset.PneumoniaDataSet(trainPath, transform = transform)
except:
    print("Creates new dataset")
    moveDataset.moveDataset(val1N = 154,val1P = 462, val2N = 308, val2P = 462)
    val1 = loadDataset.PneumoniaDataSet(val1Path, transform = transformVal)
    val2 = loadDataset.PneumoniaDataSet(val2Path, transform = transformVal)
    train = loadDataset.PneumoniaDataSet(trainPath, transform = transform)
trainLoader = DataLoader(train, batch_size=batchSize, shuffle=True)
validationLoader = DataLoader(val1, batch_size=batchSize, shuffle=True)
#Set batch_size to 1 to make it easy to create the confusion matrix.
testLoader = DataLoader(val2, batch_size= 1, shuffle=True)

def createNetwork():
    return nn.Sequential(
    nn.Conv2d(in_channels=1, out_channels=2, kernel_size=5,padding=2),
    nn.ReLU(),
    nn.Conv2d(in_channels=2, out_channels=2, kernel_size=5,padding=2),
    nn.ReLU(),
    nn.MaxPool2d(kernel_size=2),

    nn.Conv2d(in_channels=2, out_channels=4, kernel_size=3,padding=1),
    nn.ReLU(),
    nn.Conv2d(in_channels=4, out_channels=4, kernel_size=3,padding=1),
    nn.ReLU(),
    nn.MaxPool2d(kernel_size=2),

    nn.Flatten(),
    
    nn.Linear(32400, 4096),
    nn.Linear(4096,2)
    )
try:
    if continueTraning:
        print("Loading network")
        with open("best_network", 'rb') as f:
            object = pickle.load(f)
            temp = {}
            if type(object) == type(temp):
                network = object["network"]
                trainingLoss = object["trainLoss"]
                valLoss = ["valLoss"]
            else:
                network = object
                trainingLoss = []
                valLoss = []
except:
    continueTraning = False
    print("You don't have an existing network")

if continueTraning == False:
    trainingLoss = []
    valLoss = []
    print("Creates new network")
    network = createNetwork()
optimizer = optim.Adam(network.parameters(), lr = learningRate)
bestModel = copy.deepcopy(network)
lossFunction = nn.CrossEntropyLoss()
validationLoss = 9000


totalElements = epochs*val1.__len__()+epochs*train.__len__()
elementsDone = 0
starT = datetime.now()

print("Training started:",starT,"\n")
for epoch in range(epochs):
    newTrainingloss = 0
    # Toggle training AKA turing on dropout
    i = 0
    for train_nr, (images, labels,_) in enumerate(trainLoader):
        i+=1
        elementsDone +=images.size()[0]
        optimizer.zero_grad()
        prediction = network(images)
        loss = lossFunction(prediction, labels)
        loss.backward()
        optimizer.step()
        nowT = datetime.now()
        deltaT =  nowT - starT
        tLeft = deltaT*(1/(elementsDone/totalElements)-1)
        print(
            '\rEpoch {:3}/{:3} [{:5}/{:5}] - Loss: {:3.4} train'.format(
                epoch+1,epochs, train_nr+1, len(trainLoader), loss
            ),
            end='                         Done: {:2.3%} Time left: {} '.format(elementsDone/totalElements, tLeft)
        )
        newTrainingloss += loss.item()
    trainingLoss.append(newTrainingloss/i)
    #swriter.add_scalar('MINST/traininglosses', newTrainingloss/i, epoch)

    #Toggle evaluation AKA turing off dropout
    i = 0
    totalValLoss = 0
    for val_nr, (images, labels,_) in enumerate(validationLoader):
        i+=1
        elementsDone +=images.size()[0]
        prediction = network(images)
        loss = lossFunction(prediction, labels).item()
        totalValLoss += loss
        nowT = datetime.now()
        deltaT =  nowT - starT
        tLeft = deltaT*(1/(elementsDone/totalElements)-1)
        print(
            '\rEpoch {:3}/{:3} [{:5}/{:5}] - Loss: {:3.4} val'.format(
                epoch+1,epochs, val_nr+1, len(validationLoader), loss
            ),
            end='                         Done: {:2.3%} Time left: {} '.format(elementsDone/totalElements,tLeft)
        )
    
    #Calculate the newValidationloss
    newValidationloss = totalValLoss/i
    valLoss.append(newValidationloss)

    if newValidationloss < validationLoss:
        validationLoss = newValidationloss
        bestModel = copy.deepcopy(network)
        info = "Date trained: {}, epochs trained: {}, batch size: ".format(datetime.now(),len(trainingLoss),batchSize)
        saveObject = {
            "network": bestModel,
            "valLoss": valLoss,
            "trainLoss": trainingLoss,
            "info": info
        }
        # Saves network if the loss where better on the validation
        # compered to last validaton.
        print("\r New best! loss:{:3.4}".format(validationLoss), end="                  ")
        with open("best_network", 'wb') as f:
            pickle.dump(saveObject, f, protocol=pickle.HIGHEST_PROTOCOL)

    #writer.add_scalar('MINST/validationloss', newValidationloss/i, epoch)

# Run on test data
corr = 0
guesses = 0
correctSick = 0
incorrectSick = 0
correctNormal = 0
incorrectNormal = 0
noImages = val2.__len__()
starT = datetime.now()

for index, (image, label,_) in enumerate(testLoader):
    
    guess = torch.argmax(bestModel(image), dim=-1)
    result = (guess == label).sum()
    corr += result.item()
    guesses +=image.size()[0]
    nowT = datetime.now()
    deltaT =  nowT - starT
    tLeft = deltaT*(1/(guesses/noImages)-1)

    if guess.item()==1:
        if label.item() == 1:
            correctSick+=1
        else:
            incorrectSick+=1
    else:
        if label.item() == 0:
            correctNormal+=1
        else: 
            incorrectNormal+=1
    print("\r", "Right guess: {:3.2%}".format(corr/guesses), "Tested pictures: {:3.2%}".format(guesses/noImages) ,
        end="                 Time left: {} ".format(tLeft)
    )
correctness = corr/noImages
print("\n","Result on test:{:2.3%}".format(correctness))
print("Guessed correct sick:", correctSick, "Guessed incorrect sick:", incorrectSick)
print("Guessed correct normal:", correctNormal, "Guessed incorrect normal:", incorrectNormal)
#writer.add_hparams({'lr': learning_rate, 'bsize': batch_size, 'run': 'MNIST Traingin'},
#                    {'hparam/accuracy': correctness})

