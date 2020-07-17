import json

from ruamel.yaml import YAML
from midiutil.MidiFile import MIDIFile, SHARPS, FLATS, MAJOR, MINOR
import pygame

class KeySignature:
    def __init__(self, options):
        self.number = options.get('Number')
        self.type = options.get('Type')
        if self.type.lower() in ['flats', 'flat']:
            self.type = FLATS
        elif self.type.lower() in ['sharps', 'sharp']:
            self.type = SHARPS
        else:
            raise ValueError(f"KeySignature types must be either 'flats' or 'sharps', not {self.type}.")
        self.mode = options.get('Mode').upper()
        if not self.mode in ['MAJOR', 'MINOR']:
            raise ValueError(f"KeySignature mode must be either 'major' or 'minor', not {self.mode}.")
        elif self.mode == 'MAJOR':
            self.mode = MAJOR
        elif self.mode == 'MINOR':
            self.mode == MINOR

    def fixNote(self, note):
        if self.type == FLATS:
            if self.number == 4:
                if note == 'E':
                    return 'D#'
                elif note == 'D':
                    return 'C#'
                elif note == 'B':
                    return 'A#'
                elif note == 'A':
                    return 'G#'
                else:
                    return note
        else:
            raise Exception('Could not fix note.')

class NoteReader:
    def __init__(self, music_yml):
        print(music_yml)
        yaml = YAML()

        with open(music_yml, 'r') as file:
            settings = yaml.load(file)

        self.name = settings.get('Name', None)
        self.tracks = settings['Music']['Tracks']
        self.bpm = settings['Settings']['BPM']
        self.channels = settings['Settings']['Channels']
        self.keySignature = KeySignature(settings['Settings']['Key Signature'])

        print(json.dumps(dict(settings), indent = 2))
        print(f"Reading \"{self.name}\" from `{music_yml}`.")
        self.initializeMidi()
        for i, track in enumerate(self.tracks):
            self.writeTrack(track, i)
        print("Saving midi...")
        self.saveMidi()

    def initializeMidi(self):
        self.midi = MIDIFile(len(self.tracks))

        for i, track in enumerate(self.tracks):
            self.midi.addTrackName(i, 0, track['Name'])
            self.midi.addTempo(i, 0, self.bpm)
            self.midi.addProgramChange(i, 0, 0, track['Program'])

    def writeTrack(self, track, i):
        print(track)
        for note in track['Notes']:
            note['Start']
            if 'Volume' in note.keys():
                volume = note['Volume']
            else:
                volume = track['Volume']
            self.midi.addNote(i, 0, self.transposeNoteOctave(note['Note'], note['Octave']), note['Start'], note['Duration'], volume)

    def saveMidi(self):
        with open(f"./{self.name}.mid", 'wb+') as file:
            self.midi.writeFile(file)

    def checkOctave(self, octave):
        try:
            octave = int(octave)
        except:
            raise ValueError(f"Octave must be an integer between -1 and 16, inclusive, received `{octave}`.")
        finally:
            if octave < -1:
                octave = -1
            elif octave > 9:
                octave = 9
            return octave

    def evalMidi(self, note):
        midi_vals = {
            'C': 0,
            'C#': 1,
            'D': 2,
            'D#': 3,
            'E': 4,
            'F': 5,
            'F#': 6,
            'G': 7,
            'G#': 8,
            'A': 9,
            'A#': 10,
            'B': 11
        }
        if not note.upper() in midi_vals.keys():
            raise ValueError(f"Note {note} is not in list of valid notes.")
        else:
            note = self.keySignature.fixNote(note)
            return midi_vals[note.upper()]

    def transposeNoteOctave(self, note, octave):
        octave = self.checkOctave(octave)
        val = self.evalMidi(note) + (12 * (octave + 1))
        return val

    def play(self):
        def play_midi(file):
            clock = pygame.time.Clock()
            try:
                pygame.mixer.music.load(file)
                print(f"Loaded {file}!")
            except pygame.error:
                print(f"File {file} not found! {pygame.geterror()}")
                return
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                clock.tick(30)

        file = f"./{self.name}.mid"

        freq = 44100 # Audio CD quality
        bitsize = -16 # unsigned 16 bit
        channels = 1 # 1 for mono, 2 for stereo
        buffer = 1024 # sample size
        pygame.mixer.init(freq, bitsize, channels, buffer)

        pygame.mixer.music.set_volume(0.8) # optional, 0-1.0

        try:
            play_midi(file)
        except KeyboardInterrupt:
            pygame.mixer.music.fadeout(1000)
            pygame.mixer.music.stop()
            raise SystemExit

if __name__ == "__main__":
    notes = NoteReader(input("Please input a *.yml file to be converted to MIDI:\n"))
    notes.play()
