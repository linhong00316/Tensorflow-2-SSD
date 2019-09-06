from ..utils import box_utils
import tensorflow as tf


class MultiboxLoss(tf.keras.Model):
    def __init__(self, priors, iou_threshold, neg_pos_ratio,
                 center_variance, size_variance):
        """Implement SSD Multibox Loss.

        Basically, Multibox loss combines classification loss
         and Smooth L1 regression loss.
        """
        super(MultiboxLoss, self).__init__()
        self.iou_threshold = iou_threshold
        self.neg_pos_ratio = neg_pos_ratio
        self.center_variance = center_variance
        self.size_variance = size_variance
        self.priors = priors

    def forward(self, y_true, y_pred):
        """Compute classification loss and smooth l1 loss.
        Args:
            :param y_true: Tuple containing:
                labels (batch_size, num_priors): real labels of all the priors.
                boxes (batch_size, num_priors, 4): real boxes corresponding all the priors.
            :param y_pred: Tuple containing:
                confidence (batch_size, num_priors, num_classes): class predictions.
                locations (batch_size, num_priors, 4): predicted locations.
        """
        confidence = y_pred[:, :, :21]
        predicted_locations = y_pred[:, :, 21:]
        gt_locations = y_true[:, :, :4]
        labels = y_true[:, :, 4]
        num_classes = confidence.shape[2]
        # derived from cross_entropy=sum(log(p))
        loss = -tf.nn.log_softmax(confidence, axis=2)[:, :, 0]
        mask = box_utils.hard_negative_mining(loss, labels, self.neg_pos_ratio)

        confidence = tf.boolean_mask(confidence, mask)
        logits = tf.reshape(confidence, [-1, num_classes])
        ce_labels = tf.cast(tf.boolean_mask(labels, mask), tf.int64)
        classification_loss = tf.reduce_sum(tf.nn.sparse_softmax_cross_entropy_with_logits(ce_labels, logits))
        pos_mask = tf.math.greater(labels, 0)
        predicted_locations = tf.reshape(tf.boolean_mask(predicted_locations, pos_mask), [-1, 4])
        gt_locations = tf.reshape(tf.boolean_mask(gt_locations, pos_mask), [-1, 4])
        smooth_l1_loss = tf.losses.Huber()
        smooth_l1_loss = smooth_l1_loss(predicted_locations, gt_locations)
        num_pos = tf.cast(tf.shape(gt_locations)[0], dtype=tf.float32)
        return (smooth_l1_loss / num_pos) + (classification_loss / num_pos)
