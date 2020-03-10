#Documentation for MIDIUtils:https://midiutil.readthedocs.io/en/latest/
from midiutil.MidiFile import MIDIFile
import numpy as np

array = np.load("output_array.npy")

def getNoteLength(start_idx, note):
	end_idx = start_idx
	while array[end_idx][note] and end_idx != array.shape[0]:
		if end_idx < array.shape[0]-1:
			end_idx += 1
		else:
			break
	return (end_idx-start_idx)/tps



# create your MIDI object
mf = MIDIFile(1)
track = 0
tps = 4	#4 ticks per second

time = 0    # start at the beginning
mf.addTrackName(track, time, "Music read from .npy file")
mf.addTempo(track, time, 120)

channel = 0
volume = 100

playing = np.zeros(128)

for tick_idx in range(array.shape[0]):
	for note_idx in range(array.shape[1]):
		if array[tick_idx, note_idx] == 1 and not playing[note_idx]:
				duration = getNoteLength(tick_idx, note_idx)*2
				mf.addNote(track, channel, note_idx, tick_idx*0.5, duration, volume)
				playing[note_idx] = 1
		elif array[tick_idx, note_idx] == 0 and playing[note_idx]:
			playing[note_idx] = 0



# write it to disk
with open("from_array.mid", 'wb') as outf:
    mf.writeFile(outf)