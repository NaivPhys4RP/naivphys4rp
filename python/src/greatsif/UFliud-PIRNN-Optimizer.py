import tensorflow as tf
from tensorflow.keras import layers, Model, models

class PIRNN_GR2EaTSF(Model):
    def __init__(self, latent_dim_formal=128, latent_dim_intuitive=64, dt=0.1):
        super(PIRNN_GR2EaTSF, self).__init__()
        self.dt = dt
        self.latent_dim_formal = latent_dim_formal
        self.latent_dim_intuitive = latent_dim_intuitive

        # --- 1. Formal Parameter Auto-Encoder ---
        self.formal_encoder = self.build_recurrent_encoder(latent_dim_formal)
        self.formal_decoder = self.build_formal_decoder(latent_dim_formal)

        # --- 2. Intuitive Parameter Auto-Encoder ---
        # Maps Formal (a,b,t,g) -> Intuitive (mu_scene, mu_fluid)
        self.intuitive_encoder = self.build_intuitive_encoder(latent_dim_intuitive)
        self.intuitive_decoder = self.build_intuitive_decoder(latent_dim_formal)

        # --- 3. Observation MLP (Supervision) ---
        self.obs_predictor = models.Sequential([
            layers.Dense(64, activation='relu'),
            layers.Dense(3, name="obs_output") # [flow_rate, spillage, spread_area]
        ])

    def build_recurrent_encoder(self, dim):
        inputs = layers.Input(shape=(None, 128, 128, 4)) # [Time, W, H, C]
        x = layers.TimeDistributed(layers.Conv2D(32, 3, activation='relu', padding='same'))(inputs)
        x = layers.TimeDistributed(layers.MaxPooling2D(2))(x)
        x = layers.TimeDistributed(layers.Conv2D(64, 3, activation='relu', padding='same'))(x)
        x = layers.TimeDistributed(layers.Flatten())(x)
        # Latent LSTM to capture temporal dependencies
        lstm_out = layers.LSTM(dim, return_sequences=True)(x)
        return Model(inputs, lstm_out, name="Formal_Encoder")

    def build_formal_decoder(self, dim):
        latent_input = layers.Input(shape=(None, dim))
        x = layers.TimeDistributed(layers.Dense(8 * 8 * 64, activation='relu'))(latent_input)
        x = layers.TimeDistributed(layers.Reshape((8, 8, 64)))(x)
        x = layers.TimeDistributed(layers.Conv2DTranspose(32, 3, strides=2, padding='same', activation='relu'))(x)
        x = layers.TimeDistributed(layers.Conv2DTranspose(16, 3, strides(4), padding='same', activation='relu'))(x)
        x = layers.TimeDistributed(layers.Conv2DTranspose(4, 3, strides=2, padding='same', activation='sigmoid'))(x)
        return Model(latent_input, x, name="Formal_Decoder")

    def build_intuitive_encoder(self, intuitive_dim):
        formal_input = layers.Input(shape=(None, self.latent_dim_formal))
        # Recursive bottleneck to map formal physics to simulation parameters
        x = layers.LSTM(64, return_sequences=True)(formal_input)
        mu_vectors = layers.TimeDistributed(layers.Dense(intuitive_dim, activation='linear'))(x)
        return Model(formal_input, mu_vectors, name="Intuitive_Encoder")

    def build_intuitive_decoder(self, formal_dim):
        intuitive_input = layers.Input(shape=(None, self.latent_dim_intuitive))
        # Recursive reconstruction of the formal space
        x = layers.LSTM(64, return_sequences=True)(intuitive_input)
        reconst_formal = layers.TimeDistributed(layers.Dense(formal_dim, activation='linear'))(x)
        return Model(intuitive_input, reconst_formal, name="Intuitive_Decoder")

    def call(self, rgbd_sequence):
        # Pass 1: Formal Auto-Encoding
        latent_formal = self.formal_encoder(rgbd_sequence)
        reconst_rgbd = self.formal_decoder(latent_formal)

        # Pass 2: Intuitive Mapping (Coordinate Discovery)
        latent_intuitive = self.intuitive_encoder(latent_formal)
        reconst_formal = self.intuitive_decoder(latent_intuitive)

        # Pass 3: Observation Prediction
        obs_signals = self.obs_predictor(latent_formal)

        # Vector Slicing for Loss Functions
        # Assuming 128 total: alpha[0:32], beta[32:64], theta[64:96], gamma[96:128]
        alpha = latent_formal[:, :, 0:32]
        beta  = latent_formal[:, :, 32:64] # Fluid Dynamics field
        theta = latent_formal[:, :, 64:96]
        gamma = latent_formal[:, :, 96:128]

        return {
            "reconst_rgbd": reconst_rgbd,
            "latent_formal": latent_formal,
            "beta": beta,
            "latent_intuitive": latent_intuitive, # Output to C++ Simulator
            "reconst_formal": reconst_formal,
            "obs_signals": obs_signals
        }

# --- Physics-Informed Navier-Stokes Residuals ---
def navier_stokes_residual(beta, dt=0.1):
    """
    beta: [Batch, Time, 32]
    Indices: [0:3]=u,v,w | [3]=p | [4]=rho | [5:8]=grad_p
    """
    # Slice the temporal trajectory
    # State at time (t) and (t+1)
    beta_t = beta[:, :-1, :]
    beta_t_plus_1 = beta[:, 1:, :]

    # 1. Discrete Velocity Derivative: du/dt ≈ (u_t+1 - u_t) / dt
    u_t = beta_t[:, :, 0:3]
    u_tp1 = beta_t_plus_1[:, :, 0:3]
    du_dt = (u_tp1 - u_t) / dt

    # 2. Extract local pressure gradient and density
    # grad_p is learned in the formal latent space
    grad_p = beta_t[:, :, 5:8]
    rho = tf.nn.softplus(beta_t[:, :, 4:5]) + 1e-3

    # 3. Momentum Residual: rho * (du/dt) + grad_p + [External Forces] = 0
    # For your funnel experiment, gravity (g) is a constant in the Z direction
    gravity = tf.constant([0.0, 0.0, -9.81])
    momentum_res = (rho * du_dt) + grad_p - (rho * gravity)

    # 4. Continuity Residual: div(u) ≈ sum of velocity flux in latent space
    # We assume [8:11] are the flux components
    div_u = tf.reduce_sum(beta_t[:, :, 8:11], axis=-1, keepdims=True)

    # Combine residuals into a single scalar loss
    l_physics = tf.reduce_mean(tf.square(momentum_res)) + tf.reduce_mean(tf.square(div_u))
    return l_physics

# --- Final Integrated Loss & Training Step ---
def train_step(model, x_rgbd, target_obs, sim_results, weights, optimizer):
    with tf.GradientTape() as tape:
        preds = model(x_rgbd)

        # Loss 1: Formal Reconstruction (Visual)
        l_reconst_f = tf.reduce_mean(tf.square(x_rgbd - preds["reconst_rgbd"]))

        # Loss 2: Navier-Stokes (Physical Constraints on Beta)
        l_physics = navier_stokes_residual(preds["beta"], dt=model.dt)

        # Loss 3: Intuitive Reconstruction (Mapping Consistency)
        l_reconst_i = tf.reduce_mean(tf.square(preds["latent_formal"] - preds["reconst_formal"]))

        # Loss 4: Observation (Video Supervision: Area, Time)
        l_obs = tf.reduce_mean(tf.square(target_obs - preds["obs_signals"]))

        # Loss 5: Emulation (Simulator Feedback Loop)
        l_emul = tf.reduce_mean(tf.square(target_obs - sim_results))

        total_loss = (weights[0] * l_reconst_f + weights[1] * l_physics +
                      weights[2] * l_reconst_i + weights[3] * l_obs + weights[4] * l_emul)

    gradients = tape.gradient(total_loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return total_loss
