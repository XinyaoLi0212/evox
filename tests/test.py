from evox import workflows, algorithms, problems
from evox.monitors import StdMOMonitor
from evox.metrics import IGD
import jax
import jax.numpy as jnp
from evox.operators.gaussian_process.regression import GPRegression
import gpjax as gpx
from gpjax.kernels import Linear
from gpjax.likelihoods import Gaussian
from gpjax.mean_functions import Zero
import optax as ox


N = 12
M = 3
POP_SIZE = 100
LB = 0
UB = 1
ITER = 100

def nsga2():
    algorithm = algorithms.NSGA2(
        lb=jnp.full(shape=(N,), fill_value=LB),
        ub=jnp.full(shape=(N,), fill_value=UB),
        n_objs=M,
        pop_size=POP_SIZE,
    )
    run_moea(algorithm)

def rm_meda():
    algorithm = algorithms.RMMEDA(
        lb=jnp.full(shape=(N,), fill_value=LB),
        ub=jnp.full(shape=(N,), fill_value=UB),
        n_objs=M,
        pop_size=POP_SIZE,
    )
    run_moea(algorithm)

def im_moea():
    algorithm = algorithms.IMMOEA(
        lb=jnp.full(shape=(N,), fill_value=LB),
        ub=jnp.full(shape=(N,), fill_value=UB),
        n_objs=M,
        pop_size=POP_SIZE,
    )
    run_moea(algorithm)

def run_moea(algorithm, problem=problems.numerical.DTLZ2(m=M)):
    key = jax.random.PRNGKey(42)
    monitor = StdMOMonitor(record_pf=False)
    workflow = workflows.StdWorkflow(
        algorithm=algorithm,
        problem=problem,
        monitors=[monitor],
    )
    state = workflow.init(key)
    true_pf, state = problem.pf(state)
    ind = IGD(true_pf)
    for i in range(ITER):
        state = workflow.step(state)
        obj = state.get_child_state("algorithm").fitness
        print(ind(obj))

    # objs = monitor.get_last()
    # print(objs)

def run_gp():
    # 假设 matrix 是一个 N x M 的矩阵
    x = jnp.array([1, 2, 3, 12])[:, jnp.newaxis]
    pre_x = jnp.array([4,5,6])[:, jnp.newaxis]
    y = jnp.array([4, 5, 6, 13])[:, jnp.newaxis]
    # 假设 mask 是一个长度为 N 的布尔数组
    likelihood = Gaussian(num_datapoints=len(x))
    model = GPRegression(likelihood=likelihood)
    model.fit(x, y, optimzer=ox.sgd(0.001))
    _, mu, std = model.predict(pre_x)
    print(std)

def f(x):
    # 这里只是一个示例，您可以根据实际需求定义 f
    return jnp.array([[x, x+1, x+2], [x+3, x+4, x+5], [x+6, x+7, x+8], [x+9, x+10, x+11]])

def rr():
    # 使用 vmap 对 f 进行三次操作
    vmap_f = jax.vmap(f, in_axes=0, out_axes=0)
    result = vmap_f(jnp.array([0, 1, 2]))
    re_res = jnp.zeros(shape=(4,9))
    # 展平结果并按列排序
    for i in range(result.shape[1]):
        re_res = re_res.at[i].set(result[:,i,:].flatten())

    print(result.shape)
    print(re_res)
    # print(b)
if __name__ == "__main__":
    # rm_meda()
    # nsga2()
    # print("done")
    rr()