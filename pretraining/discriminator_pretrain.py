# enable imports from parent directory
import sys
import os
sys.path.append(os.path.realpath(".."))

import torch
import torch.utils.data  # cant inherit from torch.utils.data.Dataset otherwise
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
import numpy as np

import Discriminator
from Dataset import Dataset

import matplotlib.pyplot as plt
from tqdm import tqdm
import random

def generate_random(batch_size):
	"""
	Generates a collection of random haikus(batch_size), padds them to equal length
	and returns them as a PackedSequenceObject
	"""
	lengths = []
	unpadded_data = []

	for _ in range(batch_size):
		# generate a single fake sample
		fake_length = random.randint(8, 13)
		fake_sample = " ".join([random.choice(tuple(dataset.embedding.vocab)) for word in range(fake_length)])
		fake_sample = dataset.encode(fake_sample)
		unpadded_data.append(fake_sample)
		lengths.append(fake_length)

	# padd and pack the fake samples
	padded_data = pad_sequence(unpadded_data, batch_first=True)
	packed_data = pack_padded_sequence(padded_data, lengths, batch_first=True, enforce_sorted=False)
	return packed_data

batch_size = 3
torch.manual_seed(1)
np.random.seed(1)

dataset = Dataset(path_data="../data/dataset_clean.txt", path_model="../models/word2vec.model", train_test=0.04)
training_iterator = dataset.DataLoader(end=dataset.train_cap, batch_size=batch_size)
testing_iterator = dataset.DataLoader(start=dataset.train_cap, end=dataset.test_cap, batch_size=batch_size)


# Init/Load model
discriminator = Discriminator.discriminator(in_size=dataset.embedding.embedding_dim)
# discriminator.loadModel(path="../models/Discriminator_pretrained.pt")

# TRAINING
epochs = 1
training_progress = tqdm(total = dataset.train_cap * epochs, desc = "Training")
discriminator.train()
try:
	for epoch in range(epochs):
		for real_sample in training_iterator:
			fake_sample = generate_random(batch_size)

			# update training prorgess bar
			training_progress.update(batch_size)

			# Pass the samples through the discriminator
			score_real = discriminator(real_sample)
			score_fake = discriminator(fake_sample)

			# optimize
			loss = torch.mean(- torch.log(0.001 + score_real) - torch.log(1.001 - score_fake))
			discriminator.learn(loss)

			# save results
			discriminator.scores_real.append(score_real.mean().item())
			discriminator.scores_fake.append(score_fake.mean().item())
			discriminator.losses.append(loss.item())

finally:
	# Models are always saved, even after a KeyboardInterrupt
	discriminator.saveModel(path="../models/Discriminator.pt")

	# TESTING
	testing_progress = tqdm(total=dataset.test_cap - dataset.train_cap, desc="Testing")
	discriminator.eval()

	with torch.no_grad():
		real_scores = torch.zeros(dataset.test_cap - dataset.train_cap, batch_size)
		for index, real_sample in enumerate(testing_iterator):
			# update progress bar
			testing_progress.update(batch_size)

			#forward pass
			real_scores[index] = discriminator(real_sample).view(batch_size)

		mean_real_score = torch.mean(real_scores)

		print(f"The mean score for real samples from the training set is: {mean_real_score}")

	# smooth out the loss functions (avg of last window episodes)
	window = 25
	discriminator.scores_real = [np.mean(discriminator.scores_real[max(0, t-window):(t+1)]) for t in range(len(discriminator.scores_real))]
	discriminator.scores_fake = [np.mean(discriminator.scores_fake[max(0, t-window):(t+1)]) for t in range(len(discriminator.scores_fake))]
	discriminator.losses = [np.mean(discriminator.losses[max(0, t-window):(t+1)]) for t in range(len(discriminator.losses))]

	# plot the results
	fig, (loss_plot, score_plot) = plt.subplots(2)
	loss_plot.plot(discriminator.losses)
	loss_plot.title.set_text("Loss")

	score_plot.plot(discriminator.scores_real, label="Real")
	score_plot.plot(discriminator.scores_fake, label="Fake")
	score_plot.legend()
	score_plot.title.set_text("Scores")

	fig.tight_layout()
	plt.savefig("../training_graphs/disc_pretrain_scores")
	plt.show()