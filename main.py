# This is a sample Python script.
from keras.datasets import mnist
from keras.layers import Input,merge
from keras.layers.core import Reshape,Dense,Dropout,Activation,Flatten
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import Conv2D, UpSampling2D
from keras.layers.normalization import *
from keras.optimizers import *
from keras.models import Model
import matplotlib.pyplot as plt
import random
from tqdm import tqdm


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

# Freeze weights in the discriminator for stacked training
def make_trainable(net, val):
    net.trainable = val
    for l in net.layers:
        l.trainable = val

def plot_loss(losses):
#        display.clear_output(wait=True)
#        display.display(plt.gcf())
    plt.figure(figsize=(10,8))
    plt.plot(losses["d"], label='discriminitive loss')
    plt.plot(losses["g"], label='generative loss')
    plt.legend()
    plt.show()

def plot_gen(n_ex=16,dim=(4,4), figsize=(10,10) ):
    noise = np.random.uniform(0,1,size=[n_ex,100])
    generated_images = generator.predict(noise)
    plt.figure(figsize=figsize)
    for i in range(generated_images.shape[0]):
        plt.subplot(dim[0],dim[1],i+1)
        img = generated_images[i,0,:,:]
        plt.imshow(img)
        plt.axis('off')
    plt.tight_layout()
    plt.show()


def train_for_n(nb_epoch=5000, plt_frq=25, BATCH_SIZE=32):
    for e in tqdm(range(nb_epoch)):
        # Make generative images
        image_batch = X_train[np.random.randint(0, X_train.shape[0], size=BATCH_SIZE), :, :, :]
        noise_gen = np.random.uniform(0, 1, size=[BATCH_SIZE, 100])
        generated_images = generator.predict(noise_gen)
        # Train discriminator on generated images
        X = np.concatenate((image_batch, generated_images))
        y = np.zeros([2 * BATCH_SIZE, 2])
        y[0:BATCH_SIZE, 1] = 1
        y[BATCH_SIZE:, 0] = 1
        # make_trainable(discriminator,True)
        d_loss = discriminator.train_on_batch(X, y)
        losses["d"].append(d_loss)
        # train Generator-Discriminator stack on input noise to non-generated output class
        noise_tr = np.random.uniform(0, 1, size=[BATCH_SIZE, 100])
        y2 = np.zeros([BATCH_SIZE, 2])
        y2[:, 1] = 1
        # make_trainable(discriminator,False)
        g_loss = GAN.train_on_batch(noise_tr, y2)
        losses["g"].append(g_loss)
        # Updates plots
        if e % plt_frq == plt_frq - 1:
            plot_loss(losses)
            plot_gen()


def plot_real(n_ex=16, dim=(4, 4), figsize=(10, 10)):
    idx = np.random.randint(0, X_train.shape[0], n_ex)
    generated_images = X_train[idx, :, :, :]
    plt.figure(figsize=figsize)
    for i in range(generated_images.shape[0]):
        plt.subplot(dim[0], dim[1], i + 1)
        img = generated_images[i, 0, :, :]
        plt.imshow(img)
        plt.axis('off')
    plt.tight_layout()
    plt.show()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    img_rows, img_cols = 28, 28
    (X_train, y_train), (X_test, y_test) = mnist.load_data()
    X_train = X_train.reshape(X_train.shape[0], 1, img_rows, img_cols)
    X_test = X_test.reshape(X_test.shape[0], 1, img_rows, img_cols)
    X_train = X_train.astype('float32')
    X_test = X_test.astype('float32')
    X_train /= 255
    X_test /= 255
    # print np.min(X_train), np.max(X_train)

    print('X_train shape:', X_train.shape)
    print(X_train.shape[0], 'train samples')
    print(X_test.shape[0], 'test samples')

    shp = X_train.shape[1:]
    dropout_rate = 0.25
    opt = Adam(lr=1e-4)
    dopt = Adam(lr=1e-3)

    # Build Generative model ...
    nch = 200 # Channel
    g_input = Input(shape=[100])
    H = Dense(nch * 14 * 14, init='glorot_normal')(g_input)
    H = BatchNormalization()(H) #mode = 2?
    H = Activation('relu')(H)
    H = Reshape([nch, 14, 14])(H)
    H = UpSampling2D(size=(2, 2), data_format="channels_first")(H)
    H = Conv2D(nch//2, (3, 3), padding='same', kernel_initializer='glorot_uniform', data_format="channels_first")(H)
    H = BatchNormalization()(H)
    H = Activation('relu')(H)
    H = Conv2D(nch//4, (3, 3), padding='same', kernel_initializer='glorot_uniform', data_format="channels_first")(H)
    H = BatchNormalization()(H)
    H = Activation('relu')(H)
    H = Conv2D(1, (1, 1), padding='same', kernel_initializer='glorot_uniform', data_format="channels_first")(H)
    g_V = Activation('sigmoid')(H)
    generator = Model(g_input, g_V)
    generator.compile(loss='binary_crossentropy', optimizer=opt)
    generator.summary()

    # Build Discriminative model ...
    d_input = Input(shape=shp)
    H = Conv2D(256, (5, 5), strides=(2, 2), padding='same', activation='relu', data_format="channels_first")(d_input)
    H = LeakyReLU(0.2)(H)
    H = Dropout(dropout_rate)(H)
    H = Conv2D(512, (5, 5), strides=(2, 2), padding='same', activation='relu', data_format="channels_first")(H)
    H = LeakyReLU(0.2)(H)
    H = Dropout(dropout_rate)(H)
    H = Flatten()(H)
    H = Dense(256)(H)
    H = LeakyReLU(0.2)(H)
    H = Dropout(dropout_rate)(H)
    d_V = Dense(2, activation='softmax')(H)
    discriminator = Model(d_input, d_V)
    discriminator.compile(loss='categorical_crossentropy', optimizer=dopt)
    discriminator.summary()

    make_trainable(discriminator, False)

    # Build stacked GAN model
    gan_input = Input(shape=[100])
    H = generator(gan_input)
    gan_V = discriminator(H)
    GAN = Model(gan_input, gan_V)
    GAN.compile(loss='categorical_crossentropy', optimizer=opt)
    GAN.summary()

    #
    ntrain = 10000
    trainidx = random.sample(range(0, X_train.shape[0]), ntrain)
    XT = X_train[trainidx, :, :, :]

    # Pre-train the discriminator network ...
    noise_gen = np.random.uniform(0, 1, size=[XT.shape[0], 100])
    generated_images = generator.predict(noise_gen)
    X = np.concatenate((XT, generated_images))
    n = XT.shape[0]
    y = np.zeros([2 * n, 2])
    y[:n, 1] = 1
    y[n:, 0] = 1

    make_trainable(discriminator, True)
    discriminator.fit(X, y, nb_epoch=1, batch_size=128)
    y_hat = discriminator.predict(X)

    # Measure accuracy of pre-trained discriminator network
    y_hat_idx = np.argmax(y_hat, axis=1)
    y_idx = np.argmax(y, axis=1)
    diff = y_idx - y_hat_idx
    n_tot = y.shape[0]
    n_rig = (diff == 0).sum()
    acc = n_rig * 100.0 / n_tot
    print
    "Accuracy: %0.02f pct (%d of %d) right" % (acc, n_rig, n_tot)

    # set up loss storage vector
    losses = {"d": [], "g": []}

    # Train for 6000 epochs at original learning rates
    train_for_n(nb_epoch=6000, plt_frq=500, BATCH_SIZE=32)

    # Train for 2000 epochs at reduced learning rates
    opt.lr.set_value(1e-5)
    dopt.lr.set_value(1e-4)
    train_for_n(nb_epoch=2000, plt_frq=500, BATCH_SIZE=32)

    # Train for 2000 epochs at reduced learning rates
    opt.lr.set_value(1e-6)
    dopt.lr.set_value(1e-5)
    train_for_n(nb_epoch=2000, plt_frq=500, BATCH_SIZE=32)

    # Plot the final loss curves
    plot_loss(losses)

    # Plot some generated images from our GAN
    plot_gen(25, (5, 5), (12, 12))

    # Plot real MNIST images for comparison
    plot_real()


    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
