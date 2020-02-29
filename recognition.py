import numpy as np
import wave
import json

from deepspeech import Model

def words_from_metadata(metadata):
    word = ""
    word_list = []
    # Loop through each character
    for i in range(0, metadata.num_items):
        item = metadata.items[i]
        # Append character to word if it's not a space
        if item.character != " ":
            word = word + item.character
        # Word boundary is either a space or the last character in the array
        if item.character == " " or i == metadata.num_items - 1:

            each_word = word

            word_list.append(each_word)
            # Reset
            word = ""

    return word_list

def recognition(audio, words=True, use_lm=True):
    model = 'deepspeech-0.6.1-models/output_graph.pbmm'
    lm = 'deepspeech-0.6.1-models/lm.binary'
    trie = 'deepspeech-0.6.1-models/trie'
    beam_width=500
    lm_alpha=0.75
    lm_beta=1.85
    
    ds = Model(model, beam_width)

    desired_sample_rate = ds.sampleRate()

    if use_lm:
        ds.enableDecoderWithLM(lm, trie, lm_alpha, lm_beta)

    with wave.open(audio, 'rb') as fin:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)

    if words:
        return words_from_metadata(ds.sttWithMetadata(audio))
    else:
        return ds.stt(audio)

if __name__ == '__main__':
    print(recognition('Audio/out.wav', words=True))