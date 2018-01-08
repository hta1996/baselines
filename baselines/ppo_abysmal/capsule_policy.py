import baselines.common.tf_util as U
import tensorflow as tf
import gym
from baselines.common.distributions import make_pdtype
import time

class Capsule_policy(object):
    recurrent = False
    def __init__(self, name, ob_space, ac_space, kind='large'):
        with tf.variable_scope(name):
            self._init(ob_space, ac_space, kind)
            self.scope = tf.get_variable_scope().name

    def _init(self, ob_space, ac_space, kind):
        assert isinstance(ob_space, gym.spaces.Box)

        self.pdtype = pdtype = make_pdtype(ac_space)
        sequence_length = None

        ob = U.get_placeholder(name="ob", dtype=tf.float32, shape=[sequence_length] + list(ob_space.shape))
    
        x = ob
        if kind == 'small': # from A3C paper
            x = tf.nn.relu(U.conv2d(x, 16, "l1", [3, 3], [1, 1], pad="SAME"))
            x = tf.nn.relu(U.conv2d(x, 32, "l2", [3, 3], [1, 1], pad="SAME"))
            x = U.flattenallbut0(x)
            x = tf.nn.relu(U.dense(x, 256, 'lin', U.normc_initializer(1.0)))
        elif kind == 'large': # Nature DQN
            x = tf.nn.relu(U.conv2d(x, 64, "l1", [3, 3], [1, 1], pad="SAME"))
            x = tf.nn.relu(U.conv2d(x, 64, "l2", [3, 3], [1, 1], pad="SAME"))
            x = tf.nn.relu(U.conv2d(x, 128, "l3", [3, 3], [1, 1], pad="SAME"))
            x = U.flattenallbut0(x)
            x = tf.nn.relu(U.dense(x, 512, 'lin', U.normc_initializer(1.0)))
        else:
            raise NotImplementedError

        y = ob
        if kind == 'small':  # from A3C paper
            y = tf.nn.relu(U.conv2d(y, 16, "yl1", [3, 3], [1, 1], pad="SAME"))
            y = tf.nn.relu(U.conv2d(y, 32, "yl2", [3, 3], [1, 1], pad="SAME"))
            y = U.flattenallbut0(y)
            y = tf.nn.relu(U.dense(y, 256, 'ylin', U.normc_initializer(1.0)))
        elif kind == 'large':  # Nature DQN
            y = tf.nn.relu(U.conv2d(y, 64, "yl1", [3, 3], [1, 1], pad="SAME"))
            y = tf.nn.relu(U.conv2d(y, 64, "yl2", [3, 3], [1, 1], pad="SAME"))
            y = tf.nn.relu(U.conv2d(y, 128, "yl3", [3, 3], [1, 1], pad="SAME"))
            y = U.flattenallbut0(y)
            y = tf.nn.relu(U.dense(y, 512, 'ylin', U.normc_initializer(1.0)))
        else:
            raise NotImplementedError

        logits = U.dense(x, pdtype.param_shape()[0], "logits", U.normc_initializer(0.01))
        self.pd = pdtype.pdfromflat(logits)
        self.vpred = U.dense(y, 1, "value", U.normc_initializer(1.0))[:,0]

        self.state_in = []
        self.state_out = []

        stochastic = tf.placeholder(dtype=tf.bool, shape=())
        ac = self.pd.sample() # XXX
        self._act = U.function([stochastic, ob], [ac, self.vpred])

    def act(self, stochastic, ob):
        ac1, vpred1 =  self._act(stochastic, ob[None])
        return ac1[0], vpred1[0]
    def get_variables(self):
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.scope)
    def get_trainable_variables(self):
        return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, self.scope)
    def get_initial_state(self):
        return []

