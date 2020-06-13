#toller blogpost der erklärt wie der rl agent im generator funktioniert:http://karpathy.github.io/2016/05/31/rl/
#https://medium.com/@jonathan_hui/gan-why-it-is-so-hard-to-train-generative-advisory-networks-819a86b3750b
#hAIku poem generator
import torch
import torch.nn as nn
import torch.optim as optim 
import numpy as np
import random

import Generator
import Discriminator
import Tools

import matplotlib.pyplot as plt
import matplotlib.collections as collections
import time

def example():
	generator.reset_hidden(batch_size = 1)
	
	haiku_length = 5#np.random.randint(8, 12)	#length boundaries are arbitrary
	output = torch.empty(haiku_length, batch_size, len(Tools.alphabet))
	raw_output = torch.empty(haiku_length, batch_size, len(Tools.alphabet))
	previous_output = torch.rand(1, batch_size, len(Tools.alphabet))
	loss = 0

	optimal = torch.zeros(haiku_length, 1, len(Tools.alphabet))
	
	#generate sequence
	for index in range(haiku_length):
		probs = generator(previous_output)
		raw_output[index] = probs
		result = Tools.roundOutput(probs)
		output[index] = result
		previous_output = result.unsqueeze(0)
		target = torch.argmax(Tools.Q(output[:index], haiku_length, discriminator)).unsqueeze(0)#Q function is slow as heck
		#loss += generator.criterion(probs, target)
		optimal[index, 0, target] = 1

	loss = generator.MSE(raw_output, optimal)
	#optimize generator
	generator.optimizer.zero_grad()
	loss.backward()
	generator.optimizer.step()

	print(f"{Tools.decode(output)} Reward: {discriminator.forward(output).item()}")
	print(f"{Tools.decode(optimal)} Reward: {discriminator.forward(optimal).item()}")
	return optimal

dataset_path = "dataset.txt"
modelsave_path = "models/"
load_models = False
batch_size = 1

torch.manual_seed(1)
np.random.seed(1)

dataloader = Tools.fetch_sample(dataset_path)

#Init models
generator = Generator.generator(in_size = len(Tools.alphabet), out_size = len(Tools.alphabet))
discriminator = Discriminator.discriminator(in_size = len(Tools.alphabet))

if load_models:
	generator.load_state_dict(torch.load(f"{modelsave_path}Generator.pt"))
	discriminator.load_state_dict(torch.load(f"{modelsave_path}Discriminator.pt"))

start_state = torch.zeros(len(Tools.alphabet))

#TRAINING
discriminator.train()
generator.train()

training_time = 1000
start_time = time.time()
episode = 0
try:
	while time.time() < start_time + training_time:
		#print progress
		Tools.progressBar(start_time, time.time(), training_time, episode)
		episode += 1
		
		real_sample = next(dataloader)
		fake_sample = example()#Tools.encode(["".join(random.choice(Tools.alphabet) for i in range(5))])

		#take outputs from discriminator and log them
		score_real = discriminator(real_sample)
		score_fake = discriminator(fake_sample)

		#Save scores for evaluation
		discriminator.scores_real.append(score_real.item())
		discriminator.scores_fake.append(score_fake.item())
		print(f"real:{score_real}")
		print(f"fake:{score_fake}")

		#calculate losses(Discriminator minimizes, generator maximizes
		loss_d = torch.mean(-torch.log(1.01-score_fake) - torch.log(score_real))
		loss_g = torch.mean(torch.log(score_fake))

		#save losses
		generator.losses.append(loss_g.item())
		discriminator.losses.append(loss_d.item())

		#optimize discriminator
		discriminator.optimizer.zero_grad()
		loss_d.backward()
		discriminator.optimizer.step()
	
	#TESTING
	discriminator.eval()
	generator.eval()

	with torch.no_grad():
		pass

finally:
	#Models are always saved, even after a KeyboardInterrupt
	torch.save(discriminator.state_dict(), f"{modelsave_path}Discriminator.pt")
	torch.save(generator.state_dict(), f"{modelsave_path}Generator.pt")

	#plot the graph of the different losses over time
	fig, ax = plt.subplots()
	ax.plot(discriminator.scores_real, label = "Real")
	ax.plot(discriminator.scores_fake, label = "Fake")
	plt.ylabel("Scores")
	plt.xlabel("training duration")
	ax.legend()

	plt.show()