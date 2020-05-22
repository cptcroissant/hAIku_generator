#toller blogpost der erklärt wie der rl agent im generator funktioniert:http://karpathy.github.io/2016/05/31/rl/
#https://medium.com/@jonathan_hui/gan-why-it-is-so-hard-to-train-generative-advisory-networks-819a86b3750b
import torch
import torch.nn as nn
import torch.optim as optim 
import numpy as np

import random
import os

import Generator_LSTM
import Generator_MCTS
import Discriminator
import Converter

import matplotlib.pyplot as plt
import matplotlib.collections as collections

dataset_path = "C:/Users/Wuelle/Documents/KI-Bundeswettbewerb-2020/Datensatz/notewise/"
modelsave_path = "C:/Users/Wuelle/Documents/KI-Bundeswettbewerb-2020/BW-KI-2020/models/"
load_models = False
generatorModel = "MCTS"

torch.manual_seed(1)
random.seed(1)
np.random.seed(1)

sample_size = 32
dataloader = Converter.fetch_sample(sample_size, dataset_path)

discriminator_trained = []

#Init models
if generatorModel == "MCTS":
	generator = Generator_MCTS.generator(sequence_length = sample_size, branching_factor = Converter.vocab_size)
elif generatorModel == "LSTM":
	generator = Generator_LSTM.generator(in_size = Converter.vocab_size, hidden_size = 192, out_size = Converter.vocab_size)

discriminator = Discriminator.discriminator(in_size = Converter.vocab_size)


if load_models:
	generator.loadModel(f"{modelsave_path}Generator_{generatorModel}.pt")
	discriminator.loadModel(f"{modelsave_path}Discriminator.pt")

#TRAINING
discriminator.train()
generator.train()

num_episodes = 2

for episode in range(num_episodes):
	print("Episode Nr.{}".format(episode))
	
	#load a random file to test the discriminator with
	filename = dataset_path + random.choice(os.listdir(dataset_path))

	real_sample = next(dataloader)
	fake_sample = generator(sample_size)

	#take outputs from discriminator
	score_real = discriminator(real_sample)
	score_fake = discriminator(fake_sample)

	#calculate losses
	loss_d = torch.mean(-torch.log(1-score_fake) - torch.log(score_real))
	if generatorModel == "LSTM":
		loss_g = torch.mean(-torch.log(score_fake))
	elif generatorModel == "MCTS":
		loss_g = torch.mean(torch.log(score_fake))

	#save losses
	generator.losses.append(loss_g.item())
	discriminator.losses.append(loss_d.item())


	#optimize discriminator if his loss is above 0.25, otherwise let the generator exploit him
	if loss_d > 0.25:
		discriminator.optimizer.zero_grad()
		loss_d.backward(retain_graph = True)
		discriminator.optimizer.step()

	discriminator_trained.append(loss_d > 0.25)

	
	#optimize generator
	if generatorModel == "LSTM":
		generator.optimizer.zero_grad()
		loss_g.backward()
		generator.optimizer.step()
	elif generatorModel == "MCTS":
		generator.optimize(loss_g.item())
	
#TESTING
discriminator.eval()
generator.eval()

discriminator.saveModel(f"{modelsave_path}Discriminator.pt")
generator.saveModel(f"{modelsave_path}Generator_{generatorModel}.pt")

generator.save_example()

#plot the graph of the different losses over time
fig, ax = plt.subplots()
ax.plot(generator.losses, label = f"Generator {generatorModel}")
ax.plot(discriminator.losses, label = "Discriminator")

collection = collections.BrokenBarHCollection.span_where(
    np.arange(num_episodes), ymin=-100, ymax=100, where=discriminator_trained, facecolor='green', alpha=0.5)
ax.add_collection(collection)

collection = collections.BrokenBarHCollection.span_where(
    np.arange(num_episodes), ymin=-100, ymax=100, where=[not i for i in discriminator_trained], facecolor='red', alpha=0.5)
ax.add_collection(collection)

ax.legend()

plt.show()