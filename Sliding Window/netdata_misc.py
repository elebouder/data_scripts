# set up Python environment: numpy for numerical routines, and matplotlib for plotting
import numpy as np
import matplotlib.pyplot as plt
import caffe
caffe_root = 'C:/Projects/caffe/'

# set display defaults
plt.rcParams['figure.figsize'] = (10, 10)        # large images
plt.rcParams['image.interpolation'] = 'nearest'  # don't interpolate: show square pixels
plt.rcParams['image.cmap'] = 'gray'  # use grayscale output rather than a (potentially misleading) color heatmap

caffe.set_mode_gpu()
model_def = caffe_root + 'models/bvlc_alexnet/build 1.8/GAPnet/deploy.prototxt'
model_weights = caffe_root + 'models/bvlc_alexnet/build 1.8/GAPnet/caffe_alexnet_train_iter_20000.caffemodel'

net = caffe.Net(model_def, model_weights, caffe.TEST)

mu = np.load(caffe_root + 'data/L8_all/mean.npy')
mu = mu.mean(1).mean(1)
print 'mean-subtracted values: ', zip('BGR', mu)

transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})

transformer.set_transpose('data', (2, 0, 1))
transformer.set_mean('data', mu)
transformer.set_raw_scale('data', 255)
transformer.set_channel_swap('data', (2, 1, 0))

image = caffe.io.load_image(caffe_root + 'examples/landsat/LC80490202014240LGN00_531_1.tif')
transformed_image = transformer.preprocess('data', image)
net.forward()
plt.title('Input Image')
plt.imshow(image)
plt.show()

for layer_name, blob in net.blobs.iteritems():
    print layer_name + '\t' + str(blob.data.shape)


def vis_square(data):
    # normalize data for display
    data = (data - data.min()) / (data.max() - data.min())

    # force the number of filters to be square
    n = int(np.ceil(np.sqrt(data.shape[0])))
    padding = (((0, n ** 2 - data.shape[0]),
                (0, 1), (0, 1))                     # add some space between filters
               + ((0, 0),) * (data.ndim - 3))       # don't pad the last dimension (if there is one)
    data = np.pad(data, padding, mode='constant', constant_values=1)    # pad with ones (white)

    # tile the filters into an image
    data = data.reshape((n, n) + data.shape[1:]).transpose((0, 2, 1, 3) + tuple(range(4, data.ndim + 1)))
    data = data.reshape((n * data.shape[1], n * data.shape[3]) + data.shape[4:])

    plt.imshow(data); plt.axis('off'); plt.title('Conv1 Filters')
    plt.show()

filters = net.params['conv1'][0].data
vis_square(filters.transpose(0, 2, 3, 1))


feat = net.blobs['fc9'].data[0]
plt.subplot(2, 1, 1)
plt.plot(feat.flat)
plt.subplot(2, 1, 2)
_ = plt.hist(feat.flat[feat.flat > 0], bins=100)
plt.title('Output values and histogram for fc9')
plt.draw()

feat = net.blobs['prob'].data[0]
print feat
plt.figure(figsize=(15, 3))
plt.plot(feat.flat)
plt.title('Final prediction probability')
plt.draw()
plt.show()
