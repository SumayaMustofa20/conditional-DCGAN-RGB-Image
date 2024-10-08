# -*- coding: utf-8 -*-
"""cDCGAN.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Rq2ILMjO6W-pswnmHBYDcbK9cHSLhTBS
"""

# Install required packages
!pip install tensorflow==2.12.0 tensorflow-addons==0.20.0 keras==2.12.0
!pip install typeguard==2.13.3 inflect==6.0.2
!pip install visualkeras
!pip install numpy==1.23.5

# Tensorflow / Keras
from tensorflow import keras # for building Neural Networks
print('Tensorflow/Keras: %s' % keras.__version__) # print version
from keras.models import Model, load_model # for assembling a Neural Network model
from keras.layers import Input, Dense, Embedding, Reshape, Concatenate, Flatten, Dropout # for adding layers
from keras.layers import Conv2D, Conv2DTranspose, MaxPool2D, ReLU, LeakyReLU # for adding layers
from tensorflow.keras.utils import plot_model # for plotting model diagram
from tensorflow.keras.optimizers import Adam # for model optimization

# Data manipulation
import numpy as np # for data manipulation
print('numpy: %s' % np.__version__) # print version

# Visualization
import matplotlib
import matplotlib.pyplot as plt # for data visualizationa
print('matplotlib: %s' % matplotlib.__version__) # print version
import graphviz # for showing model diagram
print('graphviz: %s' % graphviz.__version__) # print version

# Other utilities
import sys
import os

# Assign main directory to a variable
main_dir='/content/drive/Shareddrives/For_Research (S)/GAN'
print(main_dir)

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Define labels and image size
labels = ['Anthracnose', 'Bacterial_Canker','Cutting_Weevil']
img_size = 128

# Data loading function
def get_data(data_dir):
    data = []
    for label in labels:
        path = os.path.join(data_dir, label)
        class_num = labels.index(label)
        for img in os.listdir(path):
            try:
                img_arr = cv2.imread(os.path.join(path, img))[...,::-1]  # Convert BGR to RGB
                resized_arr = cv2.resize(img_arr, (img_size, img_size))  # Resize the image
                data.append([resized_arr, class_num])
            except Exception as e:
                print(e)
    data = [d for d in data if d[0] is not None and d[0].size > 0]
    return np.array(data)

#['Clear_Cell', 'Endometri', 'Mucinous', 'Non_Cancerous', 'Serous']

# Load and preprocess data
data_dir = get_data("/content/drive/Shareddrives/For_Research (S)/GAN/Small_mango")

# Divide the dataset into X and Y
X = np.array([i[0] for i in data_dir])  # Image data
Y = np.array([i[1] for i in data_dir])  # Labels

# Print shapes
print("Shape of X: ", X.shape)
print("Shape of Y: ", Y.shape)

# Display images of the first 10 samples in the dataset and their true labels
fig, axs = plt.subplots(2, 4, sharey=False, tight_layout=True, figsize=(12, 6), facecolor='white')
n = 0
for i in range(0, 1):
    for j in range(0, 3):
        axs[i, j].imshow(X[n], cmap='gray')
        axs[i, j].set(title=labels[Y[n]])
        axs[i, j].axis('off')
        n = n + 1
plt.show()

# Scale and reshape as required by the model
data = X.copy()
data = data.reshape(X.shape[0], img_size, img_size, 3)
data = (data - 127.5) / 127.5  # Normalize the images to [-1, 1]
print("Shape of the scaled array: ", data.shape)

"""#Generator Model"""

def generator(latent_dim, in_shape=(32,32,1), n_cats=10):

    # Label Inputs
    in_label = Input(shape=(1,), name='Generator-Label-Input-Layer') # Input Layer
    lbls = Embedding(n_cats, 50, name='Generator-Label-Embedding-Layer')(in_label) # Embed label to vector

    # Scale up to image dimensions
    n_nodes = in_shape[0] * in_shape[1]
    lbls = Dense(n_nodes, name='Generator-Label-Dense-Layer')(lbls)
    lbls = Reshape((in_shape[0], in_shape[1], 1), name='Generator-Label-Reshape-Layer')(lbls) # New shape

    # Generator Inputs (latent vector)
    in_latent = Input(shape=latent_dim, name='Generator-Latent-Input-Layer')

    # Image Foundation
    n_nodes = 32 * 32 * 128 # number of nodes in the initial layer***
    g = Dense(n_nodes, name='Generator-Foundation-Layer')(in_latent)
    g = ReLU(name='Generator-Foundation-Layer-Activation-1')(g)
    g = Reshape((in_shape[0], in_shape[1], 128), name='Generator-Foundation-Layer-Reshape-1')(g)

    # Combine both inputs so it has two channels
    concat = Concatenate(name='Generator-Combine-Layer')([g, lbls])

    # Hidden Layer 1
    g = Conv2DTranspose(filters=128, kernel_size=(4,4), strides=(2,2), padding='same', name='Generator-Hidden-Layer-1')(concat)
    g = ReLU(name='Generator-Hidden-Layer-Activation-1')(g)

    # Hidden Layer 2
    g = Conv2DTranspose(filters=128, kernel_size=(4,4), strides=(2,2), padding='same', name='Generator-Hidden-Layer-2')(g)
    g = ReLU(name='Generator-Hidden-Layer-Activation-2')(g)

    # Output Layer (Note, we use only one filter because we have a greysclae image. Color image would have three ****
    output_layer = Conv2D(filters=3, kernel_size=(7,7), activation='tanh', padding='same', name='Generator-Output-Layer')(g)

    # Define model
    model = Model([in_latent, in_label], output_layer, name='Generator')
    return model

# Instantiate
latent_dim=100 # Our latent space has 100 dimensions. We can change it to any number
gen_model = generator(latent_dim)

# Show model summary and plot model diagram
gen_model.summary()
#plot_model(gen_model, show_shapes=True, show_layer_names=True, dpi=400, to_file=main_dir+'/pics/generator_structure.png')

"""#Discriminator model"""

def discriminator(in_shape=(128,128,3), n_cats=10):
    # Label Inputs
    in_label = Input(shape=(1,), name='Discriminator-Label-Input-Layer')
    lbls = Embedding(n_cats, 50, name='Discriminator-Label-Embedding-Layer')(in_label)

    # Scale up to image dimensions
    n_nodes = in_shape[0] * in_shape[1]
    lbls = Dense(n_nodes, name='Discriminator-Label-Dense-Layer')(lbls)
    lbls = Reshape((in_shape[0], in_shape[1], 1), name='Discriminator-Label-Reshape-Layer')(lbls)

    # Print shapes for debugging
    print("Image input shape:", in_shape)
    print("Label input shape after reshape:", lbls.shape)

    # Image Inputs
    in_image = Input(shape=in_shape, name='Discriminator-Image-Input-Layer')

    # Combine both inputs
    concat = Concatenate(name='Discriminator-Combine-Layer')([in_image, lbls])

    # Hidden Layer 1
    h = Conv2D(filters=64, kernel_size=(3,3), strides=(2,2), padding='same', name='Discriminator-Hidden-Layer-1')(concat)
    h = LeakyReLU(alpha=0.2, name='Discriminator-Hidden-Layer-Activation-1')(h)

    # Hidden Layer 2
    h = Conv2D(filters=128, kernel_size=(3,3), strides=(2,2), padding='same', name='Discriminator-Hidden-Layer-2')(h)
    h = LeakyReLU(alpha=0.2, name='Discriminator-Hidden-Layer-Activation-2')(h)
    h = MaxPool2D(pool_size=(3,3), strides=(2,2), padding='valid', name='Discriminator-MaxPool-Layer-2')(h)

    # Flatten and Output Layers
    h = Flatten(name='Discriminator-Flatten-Layer')(h)
    h = Dropout(0.2, name='Discriminator-Flatten-Layer-Dropout')(h)

    output_layer = Dense(1, activation='sigmoid', name='Discriminator-Output-Layer')(h)

    # Define model
    model = Model([in_image, in_label], output_layer, name='Discriminator')

    # Compile the model
    model.compile(loss='binary_crossentropy', optimizer=Adam(learning_rate=0.0002, beta_1=0.5), metrics=['accuracy'])
    return model

# Instantiate
dis_model = discriminator()

# Show model summary
dis_model.summary()

def def_gan(generator, discriminator):

    # We don't want to train the weights of discriminator at this stage. Hence, make it not trainable
    discriminator.trainable = False

    # Get Generator inputs / outputs
    gen_latent, gen_label = generator.input # Latent and label inputs from the generator
    gen_output = generator.output # Generator output image

    # Connect image and label from the generator to use as input into the discriminator
    gan_output = discriminator([gen_output, gen_label])

    # Define GAN model
    model = Model([gen_latent, gen_label], gan_output, name="cDCGAN")

    # Compile the model
    model.compile(loss='binary_crossentropy', optimizer=Adam(learning_rate=0.0002, beta_1=0.5))
    return model

# Instantiate
gan_model = def_gan(gen_model, dis_model)

# Show model summary and plot model diagram
gan_model.summary()
#plot_model(gan_model, show_shapes=True, show_layer_names=True, dpi=400, to_file=main_dir+'/pics/dcgan_structure.png')

"""#Preparing inputs for the Generator and the Discriminator"""

# samples real images and labels from the training data
def real_samples(data_dir, categories, n):

    # Create a random list of indices
    indx = np.random.randint(0, data_dir.shape[0], n)

    # Select real data samples (images and category labels) using the list of random indeces from above
    X, cat_labels = data_dir[indx], categories[indx]

    # Class labels
    y = np.ones((n, 1))
    return [X, cat_labels], y


# function draws random vectors from the latent space, as well as random labels to be used as inputs into the Generator
def latent_vector(latent_dim, n, n_cats=10):

    # Generate points in the latent space
    latent_input = np.random.randn(latent_dim * n)

    # Reshape into a batch of inputs for the network
    latent_input = latent_input.reshape(n, latent_dim)

    # Generate category labels
    cat_labels = np.random.randint(0, n_cats, n)
    return [latent_input, cat_labels]


#the third function passes latent variables and labels into the Generator model to generate fake examples.
def fake_samples(generator, latent_dim, n):

    # Draw latent variables
    latent_output, cat_labels = latent_vector(latent_dim, n)

    # Predict outputs (i.e., generate fake samples)
    X = generator.predict([latent_output, cat_labels])

    # Create class labels
    y = np.zeros((n, 1))
    return [X, cat_labels], y

"""#Function to see interim results"""

def show_fakes(generator, latent_dim, n=10):

    # Get fake (generated) samples
    x_fake, y_fake = fake_samples(generator, latent_dim, n)

    # Rescale from [-1, 1] to [0, 1]
    X_tst = (x_fake[0] + 1) / 2.0

    # Display fake (generated) images
    fig, axs = plt.subplots(2, 5, sharey=False, tight_layout=True, figsize=(12,6), facecolor='white')
    k=0
    for i in range(0,1):
        for j in range(0,3):
            axs[i,j].matshow(X_tst[k], cmap='gray')
            axs[i,j].set(title=x_fake[1][k])
            axs[i,j].axis('off')
            k=k+1
    plt.show()

"""#Training Function"""

def train(g_model, d_model, gan_model, data_dir, categories, latent_dim, n_epochs=15, n_batch=128, n_eval=200):
    # Number of batches to use per each epoch
    batch_per_epoch = int(data_dir.shape[0] / n_batch)
    print(' batch_per_epoch: ',  batch_per_epoch)
    # Our batch to train the discriminator will consist of half real images and half fake (generated) images
    half_batch = int(n_batch / 2)

    # We will manually enumare epochs
    for i in range(n_epochs):

        # Enumerate batches over the training set
        for j in range(batch_per_epoch):

        # Discriminator training
            # Prep real samples
            [x_real, cat_labels_real], y_real = real_samples(data_dir, categories, half_batch)
            # Train discriminator with real samples
            discriminator_loss1, _ = d_model.train_on_batch([x_real, cat_labels_real], y_real)

            # Prep fake (generated) samples
            [x_fake, cat_labels_fake], y_fake = fake_samples(g_model, latent_dim, half_batch)
            # Train discriminator with fake samples
            discriminator_loss2, _ = d_model.train_on_batch([x_fake, cat_labels_fake], y_fake)


        # Generator training
            # Get values from the latent space to be used as inputs for the generator
            [latent_input, cat_labels] = latent_vector(latent_dim, n_batch)
            # While we are generating fake samples,
            # we want GAN generator model to create examples that resemble the real ones,
            # hence we want to pass labels corresponding to real samples, i.e. y=1, not 0.
            y_gan = np.ones((n_batch, 1))

            # Train the generator via a composite GAN model
            generator_loss = gan_model.train_on_batch([latent_input, cat_labels], y_gan)

        # Summarize training progress and loss
            if (j) % n_eval == 0:
                print('Epoch: %d, Batch: %d/%d, D_Loss_Real=%.3f, D_Loss_Fake=%.3f Gen_Loss=%.3f' %
                      (i+1, j+1, batch_per_epoch, discriminator_loss1, discriminator_loss2, generator_loss))
                show_fakes(g_model, latent_dim)

train(gen_model, dis_model, gan_model, data, Y, latent_dim)