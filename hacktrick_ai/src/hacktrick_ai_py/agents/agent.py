import itertools, math
import numpy as np
from collections import defaultdict
from hacktrick_ai.src.hacktrick_ai_py.mdp.actions import Action


class Agent(object):

    def __init__(self):
        self.reset()

    def action(self, state):
        """
        Should return an action, and an action info dictionary.
        If collecting trajectories of the agent with HacktrickEnv, the action
        info data will be included in the trajectory data under `ep_infos`.

        This allows agents to optionally store useful information about them
        in the trajectory for further analysis.
        """
        return NotImplementedError()

    def actions(self, states, agent_indices):
        """
        A multi-state version of the action method. This enables for parallized
        implementations that can potentially give speedups in action prediction. 

        Args:
            states (list): list of HacktrickStates for which we want actions for
            agent_indices (list): list to inform which agent we are requesting the action for in each state

        Returns:
            [(action, action_info), (action, action_info), ...]: the actions and action infos for each state-agent_index pair
        """
        return NotImplementedError()

    @staticmethod
    def a_probs_from_action(action):
        action_idx = Action.ACTION_TO_INDEX[action]
        return np.eye(Action.NUM_ACTIONS)[action_idx]

    @staticmethod
    def check_action_probs(action_probs, tolerance=1e-4):
        """Check that action probabilities sum to ≈ 1.0"""
        probs_sum = sum(action_probs)
        assert math.isclose(probs_sum, 1.0, rel_tol=tolerance), "Action probabilities {} should sum up to approximately 1 but sum up to {}".format(list(action_probs), probs_sum)

    def set_agent_index(self, agent_index):
        self.agent_index = agent_index

    def set_mdp(self, mdp):
        self.mdp = mdp

    def reset(self):
        """
        One should always reset agents in between trajectory rollouts, as resetting
        usually clears history or other trajectory-specific attributes.
        """
        self.agent_index = None
        self.mdp = None


class AgentGroup(object):
    """
    AgentGroup is a group of N agents used to sample 
    joint actions in the context of an HacktrickEnv instance.
    """

    def __init__(self, *agents, allow_duplicate_agents=False):
        self.agents = agents
        self.n = len(self.agents)
        self.reset()

        if not all(a0 is not a1 for a0, a1 in itertools.combinations(agents, 2)):
            assert allow_duplicate_agents, "All agents should be separate instances, unless allow_duplicate_agents is set to true"

    def joint_action(self, state):
        actions_and_probs_n = tuple(a.action(state) for a in self.agents)
        return actions_and_probs_n

    def set_mdp(self, mdp):
        for a in self.agents:
            a.set_mdp(mdp)

    def reset(self):
        """
        When resetting an agent group, we know that the agent indices will remain the same,
        but we have no guarantee about the mdp, that must be set again separately.
        """
        for i, agent in enumerate(self.agents):
            agent.reset()
            agent.set_agent_index(i)


class AgentPair(AgentGroup):
    """
    AgentPair is the N=2 case of AgentGroup. Unlike AgentGroup,
    it supports having both agents being the same instance of Agent.

    NOTE: Allowing duplicate agents (using the same instance of an agent
    for both fields can lead to problems if the agents have state / history)
    """

    def __init__(self, *agents, allow_duplicate_agents=False): 
        super().__init__(*agents, allow_duplicate_agents=allow_duplicate_agents)
        assert self.n == 2
        self.a0, self.a1 = self.agents

    def joint_action(self, state):
        if self.a0 is self.a1:
            # When using the same instance of an agent for self-play,
            # reset agent index at each turn to prevent overwriting it
            self.a0.set_agent_index(0)
            action_and_infos_0 = self.a0.action(state)
            self.a1.set_agent_index(1)
            action_and_infos_1 = self.a1.action(state)
            joint_action_and_infos = (action_and_infos_0, action_and_infos_1)
            return joint_action_and_infos
        else:
            return super().joint_action(state)


class RandomAgent(Agent):
    """
    An agent that randomly picks motion actions.
    NOTE: Does not perform interact actions, unless specified
    """

    def __init__(self, sim_threads=None, all_actions=False, custom_wait_prob=None):
        self.sim_threads = sim_threads
        self.all_actions = all_actions
        self.custom_wait_prob = custom_wait_prob
    
    def action(self, state):
        action_probs = np.zeros(Action.NUM_ACTIONS)
        legal_actions = list(Action.MOTION_ACTIONS)
        if self.all_actions:
            legal_actions = Action.ALL_ACTIONS
        legal_actions_indices = np.array([Action.ACTION_TO_INDEX[motion_a] for motion_a in legal_actions])
        action_probs[legal_actions_indices] = 1 / len(legal_actions_indices)

        if self.custom_wait_prob is not None:
            stay = Action.STAY
            if np.random.random() < self.custom_wait_prob:
                return stay, {"action_probs": Agent.a_probs_from_action(stay)}
            else:
                action_probs = Action.remove_indices_and_renormalize(action_probs, [Action.ACTION_TO_INDEX[stay]])

        return Action.sample(action_probs), {"action_probs": action_probs}

    def actions(self, states, agent_indices):
        return [self.action(state) for state in states]

    def direct_action(self, obs):
        return [np.random.randint(4) for _ in range(self.sim_threads)]


class StayAgent(Agent):

    def __init__(self, sim_threads=None):
        self.sim_threads = sim_threads
    
    def action(self, state):
        a = Action.STAY
        return a, {}

    def direct_action(self, obs):
        return [Action.ACTION_TO_INDEX[Action.STAY]] * self.sim_threads