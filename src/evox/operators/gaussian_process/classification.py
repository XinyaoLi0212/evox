# https://docs.jaxgaussianprocesses.com/examples/classification/

import jax
import jax.random as jr
import jax.numpy as jnp
import optax as ox

try:
    import gpjax as gpx
    from gpjax.mean_functions import Zero
    from gpjax.kernels import RBF
    from gpjax.objectives import LogPosteriorDensity
except ImportError as e:
    original_error_msg = str(e)

    def gpx(*args, **kwargs):
        raise ImportError(
            f'gpjax requires gpjax, but got "{original_error_msg}" when importing'
        )

    def RBF(*args, **kwargs):
        raise ImportError(
            f'RBF requires gpjax, but got "{original_error_msg}" when importing'
        )

    def Zero(*args, **kwargs):
        raise ImportError(
            f'Zero requires gpjax, but got "{original_error_msg}" when importing'
        )

    def LogPosteriorDensity(*args, **kwargs):
        raise ImportError(
            f'LogPosteriorDensity requires gpjax, but got "{original_error_msg}" when importing'
        )


# jax.config.update('jax_enable_x64', True)


class GPClassification:
    """
    Gaussian Process Classification model using JAX, Optax and GPJAX.

    This model applies Gaussian Process (GP) for classification tasks. It uses an RBF kernel and
    a Zero mean function by default. The class allows for fitting the model to data and making predictions.
    The GP's prior and posterior are defined, and the model is fitted using the specified optimization method.

    Attributes:
        kernel: The kernel function for the GP (default is RBF).
                The difference between the kernels are shown in the link: https://docs.jaxgaussianprocesses.com/examples/intro_to_kernels/.
        mean_fun: The mean function for the GP (default is Zero).
        key: JAX random key for stochastic operations.
        prior: The prior distribution of the GP, which is chosen by the user according to the specific problems.
        likelihood: The likelihood function for the GP.
        object: The objective function (default is negative Log Posterior Density).
        posterior: The posterior distribution of the GP after applying the likelihood.
    """

    def __init__(
        self,
        kernel=RBF(),
        meanfun=Zero(),
        likelihood=None,
        object=LogPosteriorDensity(negative=True),
        key=jr.PRNGKey(123),
    ):
        """Initializes the Gaussian Process Classification model with default parameters."""
        self.kernel = kernel
        self.mean_fun = meanfun
        self.key = key
        self.prior = gpx.gps.Prior(mean_function=meanfun, kernel=kernel)
        self.likelihood = likelihood
        self.object = object
        self.posterior = self.prior * self.likelihood

    def fit(self, x: jax.Array, y: jax.Array, optimizer=ox.adam):
        """
        Fits the model to the provided data.

        The method takes in features (x) and labels (y), creates a dataset, and then uses
        the specified optimization method to fit the model. The process includes setting
        the objective function and optimizing the posterior distribution.

        Args:
            x: The feature matrix.
            y: The label vector.
            optimizer: The optimization algorithm implemented by Optax to use (default is Adam).
        """
        self.dataset = gpx.Dataset(X=x.astype(jnp.float32), y=y.astype(jnp.float32))
        self.object(self.posterior, train_data=self.dataset)
        self.opt_posterior, self.history = gpx.fit(
            model=self.posterior,
            objective=self.object,
            train_data=self.dataset,
            optim=optimizer,
            num_iters=500,
            key=self.key,
            verbose=False,
        )

    def predict(self, x):
        """
        Makes predictions on new data.

        The method computes the predictive distribution of the optimized model for new input features.
        It returns the predictive distribution along with the mean and standard deviation of the predictions.

        Args:
            x: The feature matrix for which predictions are to be made.

        Returns:
            A tuple containing the predictive distribution, predictive mean, and predictive standard deviation.
        """
        latent_dist = self.opt_posterior.predict(x, train_data=self.dataset)
        predictive_dist = self.opt_posterior.likelihood(latent_dist)

        predictive_mean = predictive_dist.mean()
        predictive_std = predictive_dist.stddev()
        return predictive_dist, predictive_mean, predictive_std
