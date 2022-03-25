# from sympy import false
# from os import stat
from hacktrick_ai.build.lib.hacktrick_ai_py.mdp import hacktrick_mdp
from hacktrick_ai.src.hacktrick_ai_py.agents.agent import Agent, AgentPair
from hacktrick_ai.src.hacktrick_ai_py.mdp.hacktrick_mdp import HacktrickState, Recipe
from hacktrick_ai.src.hacktrick_ai_py.mdp.actions import Action
from hacktrick_rl.hacktrick_rl.rllib.rllib import RlLibAgent, load_agent_pair
from AgentHelper import AgentHelper



class MainAgent(Agent):
    def __init__(self):
        super().__init__()
        self.agentHelper = AgentHelper(0)
        self.first = True
        self.cooking_counter = 0
        self.actions = []
        self.tasks = []
        
    def action(self, state): 
        self.init_orders(state)
        self.agentHelper.set_player_positions(state) 

        # Get new actions to do 
        self.actions = self.agentHelper.decide(state, self.tasks, self.cooking_counter, self.actions)

        # Count cooking time
        if self.agentHelper.order_under_cooking(state):
            self.cooking_counter += 1
        elif not self.agentHelper.order_is_ready(state) and not self.agentHelper.order_under_cooking(state):
            self.cooking_counter = 0
            
        # Wait until the order be ready
        if self.actions[0] == Action.INTERACT and self.agentHelper.waiting_to_ready(state):
            action = Action.STAY
        else:
            action =  self.agentHelper.avoid_collision(self.actions[0])
            if action == self.actions[0]:
                self.actions.pop(0)
                
        action_probs = {}
        return action, action_probs
    
    def init_orders(self, state):
        if self.first:
            self.agentHelper.init_orders(state) 
            self.first = False


    

class OptionalAgent(Agent):
    def __init__(self):
        super().__init__()
        self.agentHelper = AgentHelper(1)
        self.first = True
        self.cooking_counter = 0
        # self.actions = [(1, 0), (1, 0), (0, 1)]
        self.actions = [(-1, 0), (-1, 0), (0, 1), (0, 1), (0, 1), (0, 1), (1, 0)]
        self.tasks = []
        
    def action(self, state): 
        # self.init_orders(state)
        # self.agentHelper.set_player_positions(state) 

        # # Get new actions to do 
        # self.actions = self.agentHelper.decide(state, self.tasks, self.cooking_counter, self.actions)

        # # Count cooking time
        # if self.agentHelper.order_under_cooking(state):
        #     self.cooking_counter += 1
        # elif not self.agentHelper.order_is_ready(state) and not self.agentHelper.order_under_cooking(state):
        #     self.cooking_counter = 0
            
        # # Wait until the order be ready
        # if self.actions[0] == Action.INTERACT and self.agentHelper.waiting_to_ready(state):
        #     action = Action.STAY
        # else:
        #     action =  self.agentHelper.avoid_collision(self.actions[0])
        #     if action == self.actions[0]:
        #         self.actions.pop(0)
        
        if len(self.actions):
            action = self.actions[0]
            self.actions.pop(0)
        else:
            action = Action.STAY

        action_probs = {}
        return action, action_probs
                
        action_probs = {}
        return action, action_probs
    
    def init_orders(self, state):
        if self.first:
            self.agentHelper.init_orders(state) 
            self.first = False
            
            

class HacktrickAgent(object):
    # Enable this flag if you are using reinforcement learning from the included ppo ray support library
    RL = False
    # Rplace with the directory for the trained agent
    # Note that `agent_dir` is the full path to the checkpoint FILE, not the checkpoint directory
    agent_dir = ''
    # If you do not plan to use the same agent logic for both agents and use the OptionalAgent set it to False
    # Does not matter if you are using RL as this is controlled by the RL agent
    share_agent_logic = False

    def __init__(self):
        Recipe.configure({})
        if self.RL:
            agent_pair = load_agent_pair(self.agent_dir)
            self.agent0 = agent_pair.a0
            self.agent1 = agent_pair.a1
        else:
            self.agent0 = MainAgent()
            self.agent1 = OptionalAgent()
    
    def set_mode(self, mode):
        self.mode = mode

        if "collaborative" in self.mode:
            if self.share_agent_logic and not self.RL:
                self.agent1 = MainAgent()
            self.agent_pair = AgentPair(self.agent0, self.agent1)
        else:
            self.agent1 =None
            self.agent_pair =None
    
    def map_action(self, action):
        action_map = {(0, 0): 'STAY', (0, -1): 'UP', (0, 1): 'DOWN', (1, 0): 'RIGHT', (-1, 0): 'LEFT', 'interact': 'SPACE'}
        action_str = action_map[action[0]]
        return action_str

    def action(self, state_dict):
        state = HacktrickState.from_dict(state_dict['state']['state'])

        if "collaborative" in self.mode:
            (action0, action1) = self.agent_pair.joint_action(state)
            action0 = self.map_action(action0)
            action1 = self.map_action(action1)
            action = [action0, action1]
        else:
            action0 = self.agent0.action(state)
            action0 = self.map_action(action0)
            action = action0

        return action