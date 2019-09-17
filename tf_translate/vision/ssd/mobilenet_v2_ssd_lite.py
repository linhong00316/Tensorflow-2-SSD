from functools import partial

from tensorflow.python.keras.layers import SeparableConv2D, Conv2D

from vision.nn.mobilenet_v2 import MobileNetV2, inverted_res_block
from .config import mobilenetv1_ssd_config as config
from .predictor import Predictor
from .ssd import SSD, GraphPath


def create_mobilenetv2_ssd_lite(num_classes, width_mult=1.0, is_test=False):
    base_net = MobileNetV2(input_shape=(config.image_size, config.image_size, 3),
                           include_top=False, alpha=width_mult)

    source_layer_indexes = [
        GraphPath((108, 116), 'conv', 3),
        19,
    ]
    extras = [
        # Make frozen inverted residual block functions that only need input
        partial(inverted_res_block, expansion=0.2, stride=2, alpha=width_mult,
                filters=512, block_id=None),
        partial(inverted_res_block, expansion=0.25, stride=2, alpha=width_mult,
                filters=256, block_id=None),
        partial(inverted_res_block, expansion=0.5, stride=2, alpha=width_mult,
                filters=256, block_id=None),
        partial(inverted_res_block, expansion=0.25, stride=2, alpha=width_mult,
                filters=64, block_id=None)
    ]

    regression_headers = [
        # TODO change to relu6
        SeparableConv2D(filters=6 * 4, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * 4, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * 4, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * 4, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * 4, kernel_size=3, padding='same', activation='relu'),
        Conv2D(filters=6 * 4, kernel_size=1),
    ]

    classification_headers = [
        SeparableConv2D(filters=6 * num_classes, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * num_classes, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * num_classes, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * num_classes, kernel_size=3, padding='same', activation='relu'),
        SeparableConv2D(filters=6 * num_classes, kernel_size=3, padding='same', activation='relu'),
        Conv2D(filters=6 * num_classes, kernel_size=1),
    ]

    return SSD(num_classes, base_net, source_layer_indexes,
               extras, classification_headers, regression_headers, is_test=is_test, config=config)


def create_mobilenetv2_ssd_lite_predictor(net, candidate_size=200, nms_method=None, sigma=0.5):
    predictor = Predictor(net, config.image_size, config.image_mean,
                          config.image_std,
                          nms_method=nms_method,
                          iou_threshold=config.iou_threshold,
                          candidate_size=candidate_size,
                          sigma=sigma)
    return predictor
