import torch
import torch.nn as nn
import torch.optim as optim


class discriminator(nn.Module):
	def __init__(self, in_size, hidden_size=400, out_size=1, n_layers=1, lr=0.01, embedding_dim=50, batch_first=True):
		super(discriminator, self).__init__()

		self.in_size = in_size
		self.out_size = out_size
		self.embedding_dim = embedding_dim
		self.lr = lr
		self.hidden_size = hidden_size
		self.n_layers = n_layers

		# Architecture
		self.embedding = nn.Embedding(self.in_size, self.embedding_dim)
		self.lstm = nn.LSTM(self.embedding_dim, self.hidden_size, self.n_layers, batch_first=batch_first)
		self.network = nn.Sequential(
			nn.Linear(self.hidden_size, 400),
			nn.ReLU(),
			nn.Linear(400, 300),
			nn.ReLU(),
			nn.Linear(300, 100),
			nn.ReLU(),
			nn.Linear(100, self.out_size),
			nn.Sigmoid()

		)
		self.criterion = nn.BCELoss()
		self.optimizer = optim.Adagrad(self.parameters(), self.lr)

		self.losses = []
		self.scores_real = []
		self.scores_fake = []

	def reset_hidden(self, batch_size):
		# discriminator hidden is not random
		self.hidden = (torch.zeros(self.n_layers, batch_size, self.hidden_size), torch.zeros(self.n_layers, batch_size, self.hidden_size))

	def forward(self, input):
		batch_size = input.shape[0]
		self.reset_hidden(batch_size)

		input = self.embedding(input.long()).view(batch_size, -1, self.embedding_dim)
		lstm_out, self.hidden = self.lstm(input, self.hidden)
		# WARUM HAT DAS HIER OHNE DAS RESHAPE FUNKTIONIERT
		lstm_out = lstm_out.reshape([-1, self.hidden_size])
		output = self.network(lstm_out)
		return torch.mean(output).view(1, 1, 1)  # return the last score, incomplete sequence may be judged incorrectly
