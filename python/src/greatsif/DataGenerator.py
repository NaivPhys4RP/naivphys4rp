import rosbag
import cv2
import numpy as np
import tensorflow as tf
from cv_bridge import CvBridge

def generate_pirnn_dataset(bag_path, start_time, end_time,
                           rgb_topic, depth_topic,
                           sampling_rate,
                           flow_time, spread_surface_cm2,
                           img_size=(128, 128)):
    """
    Extracts and synchronizes RGB-D data from a ROS Bag for PIRNN training.

    Returns:
        - X_rgbd: [1, Time, 128, 128, 4] tensor (Normalized)
        - Y_supervision: [1, 3] tensor [flow_time, 0, spread_surface_cm2]
          (Note: Spillage index left at 0 for now)
    """
    bridge = CvBridge()
    bag = rosbag.Bag(bag_path)

    # 1. Initialize storage
    raw_rgb = []
    raw_depth = []

    # Define time window
    t_start = rosbag.rosbag_main.Duration(start_time)
    t_end = rosbag.rosbag_main.Duration(end_time)

    # 2. Extract Data
    # We iterate and sample based on the sampling_rate (e.g., sample every 0.1s)
    last_sampled_t = 0
    interval = 1.0 / sampling_rate

    # We use a simple message-by-message sync approach here
    # For high precision, you would use message_filters.Cache
    for topic, msg, t in bag.read_messages(topics=[rgb_topic, depth_topic]):
        current_t = t.to_sec()

        if current_t < start_time: continue
        if current_t > end_time: break

        # Sampling logic
        if (current_t - last_sampled_t) >= interval:
            if topic == rgb_topic:
                cv_img = bridge.imgmsg_to_cv2(msg, "rgb8")
                res_img = cv2.resize(cv_img, img_size)
                raw_rgb.append(res_img / 255.0) # Normalize RGB
                last_sampled_t = current_t

            elif topic == depth_topic:
                # '16UC1' is standard for Depth; convert to meters/cm and normalize
                cv_depth = bridge.imgmsg_to_cv2(msg, "16UC1")
                res_depth = cv2.resize(cv_depth, img_size)
                # Normalize depth (clipping at 3m for consistency)
                norm_depth = np.clip(res_depth.astype(np.float32) / 3000.0, 0, 1)
                raw_depth.append(norm_depth)

    bag.close()

    # 3. Synchronize Sequence Length
    # Ensure both lists are equal length
    min_len = min(len(raw_rgb), len(raw_depth))
    raw_rgb = np.array(raw_rgb[:min_len])
    raw_depth = np.array(raw_depth[:min_len])[..., np.newaxis] # Add channel dim

    # 4. Concatenate into [Time, 128, 128, 4]
    rgbd_sequence = np.concatenate([raw_rgb, raw_depth], axis=-1)

    # Add Batch Dimension
    X_rgbd = np.expand_dims(rgbd_sequence, axis=0)

    # 5. Prepare Supervision Labels
    # [FlowTime, Spillage(binary/float), SpreadArea]
    Y_supervision = np.array([[flow_time, 0.0, spread_surface_cm2]], dtype=np.float32)

    return tf.convert_to_tensor(X_rgbd, dtype=tf.float32), \
           tf.convert_to_tensor(Y_supervision, dtype=tf.float32)

# --- Usage Example ---
# x, y = generate_pirnn_dataset("maize_pour_01.bag", 10.5, 15.0,
#                               "/cam/rgb", "/cam/depth", 10,
#                               4.2, 1550.0)
