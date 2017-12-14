import cv2
import pickle
import os.path
import numpy as np
from imutils import paths
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer
from keras.models import Sequential
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.layers.core import Dense, Flatten
from helpers import resize_to_fit

LETTER_IMAGES_FOLDER = "extracted_letter_images"
MODEL_FILENAME = "captcha_model.hdf5"
MODEL_LABELS_FILENAME = "model_labels.dat"

# Initialise the data and labels
data = []
labels = []

# Loop over the input images
for image_file in paths.list_images(LETTER_IMAGES_FOLDER):
    # lOad image and cobert it to grayscale
    image = cv2.imread(image_file)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Resize to fit 20 x 20 pixel box
    image = resize_to_fit(image, 20, 20)

    # Add a third channel for keras
    image = np.expand_dims(image, axis=2)

    # Grab the name of the letter based on the folder it is in
    label = image_file.split(os.path.sep)[-2]

    # Add the letter image and label to the lists
    data.append(image)
    labels.append(label)

# scale the raw pixel intensities to the range [0, 1] (this improves training)
data = np.array(data, dtype="float32") / 255.0
labels = np.array(labels)

# Split into training and test sets
(X_train, X_test, Y_train, Y_test) = train_test_split(data, labels, test_size=0.25, random_state=0)

# Convert the labels (letters) into one-hot encodings ofr keras
lb = LabelBinarizer().fit(list(Y_train)+list(Y_test))
Y_train = lb.transform(Y_train)
Y_test = lb.transform(Y_test)

# save the mappings from labels to one_hot_encodings
# We will use this later when we use the model to decode the prediction
with open(MODEL_LABELS_FILENAME, "wb") as f:
    pickle.dump(lb, f)

### Build the Neural network ###
model = Sequential()

# First Convulational layer with max pooling
model.add(Conv2D(20, (5, 5), padding="same", input_shape=(20, 20, 1), activation="relu"))
model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))

# Second convolutional layer with max pooling
model.add(Conv2D(50, (5, 5), padding="same", activation="relu"))
model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))

# Hidden layer with 500 nodes
model.add(Flatten())
model.add(Dense(500, activation="relu"))

# Output layer with 32 nodes (one for each possible letter/number we predict)
model.add(Dense(32, activation="softmax"))

# Ask Keras to build the TensorFlow model behind the scenes
model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

# Train the neural network
model.fit(X_train, Y_train, validation_data=(X_test, Y_test), batch_size=32, epochs=10, verbose=1)

# Summary of the model
print(model.summary())
# Save the trained model to disk
model.save(MODEL_FILENAME)
