# Rock, Paper, Scissors Gesture Classifier

## Problem statement

This project trains a convolutional neural network (CNN) in TensorFlow / Keras to look at a picture of a hand and say whether it shows **rock**, **paper** or **scissors**.

**Why it matters.** Hand gestures let people control software without a keyboard, mouse or controller. Examples include webcam games, touch-free kiosks, and accessibility tools for people who find a controller hard to use. Rock, paper, scissors is a small, well-defined version of that problem: three gestures, each with one clear meaning.

**Who would use it.** A game developer building a webcam game where you play rock, paper, scissors against the computer. The model reads the player's hand from the camera, and the game compares it with the computer's move to decide who wins.

**What I want to find out.**

- How accurately a CNN trained from scratch can tell the three gestures apart.
- Which gestures it confuses, and what the misclassified images have in common.
- How far the model can be trusted outside its dataset, since every training image is a computer-generated hand on a plain white background rather than a real webcam photo.
